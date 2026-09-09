"""Narrow, parameterized API. X-Principal exists only for the local fixture."""
from __future__ import annotations
import hashlib, json, os
from uuid import UUID
import psycopg
from fastapi import FastAPI, Header, HTTPException, Response
from pydantic import BaseModel, Field

app = FastAPI(title="Agent Operations shared-memory laboratory", version="0.1.0")
DB = os.environ.get("DATABASE_URL", "postgresql://lab_app:lab_only_change_me@localhost:54329/memory_lab")
KINDS = {"task-summary","finding","decision","experiment-summary","dataset-note","rfc-reference"}

class RecordInput(BaseModel):
    kind: str
    title: str = Field(max_length=240)
    summary: str = Field(max_length=600)
    payload: dict = Field(default_factory=dict)
    evidence_status: str = "observed"

class SearchInput(BaseModel):
    query: str = Field(min_length=1, max_length=200)
    kinds: list[str] | None = None
    limit: int = Field(default=5, ge=1, le=20)

class RevisionInput(BaseModel):
    title: str = Field(max_length=240)
    summary: str = Field(max_length=600)
    payload: dict = Field(default_factory=dict)
    evidence_status: str = "observed"

def canonical(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",",":"))

def principal(conn, label: str) -> UUID:
    row = conn.execute("SELECT id FROM principals WHERE label=%s AND enabled", (label,)).fetchone()
    if not row: raise HTTPException(401, "unknown local fixture principal")
    return row[0]

def project_scope(conn, project_id: UUID, actor: UUID) -> UUID:
    row = conn.execute("SELECT p.team_id FROM projects p JOIN memberships m ON m.team_id=p.team_id WHERE p.id=%s AND m.principal_id=%s", (project_id, actor)).fetchone()
    if not row: raise HTTPException(404, "project not found")
    return row[0]

def bind_principal(conn, actor: UUID) -> None:
    conn.execute("SELECT set_config('app.principal_id', %s, true)", (str(actor),))

@app.post("/v1/projects/{project_id}/records", status_code=201)
def publish(project_id: UUID, item: RecordInput, response: Response, x_principal: str = Header(...), idempotency_key: str = Header(...)):
    if item.kind not in KINDS: raise HTTPException(422, "invalid kind")
    body = item.model_dump(); request_hash = hashlib.sha256(canonical(body).encode()).hexdigest()
    with psycopg.connect(DB) as conn:
        actor = principal(conn, x_principal)
        team = project_scope(conn, project_id, actor)
        bind_principal(conn, actor)
        prior = conn.execute("SELECT request_hash,record_id FROM idempotency_keys WHERE principal_id=%s AND project_id=%s AND key=%s", (actor,project_id,idempotency_key)).fetchone()
        if prior:
            if prior[0] != request_hash: raise HTTPException(409, "idempotency key reused with different payload")
            response.status_code = 200; return {"id": str(prior[1]), "idempotent": True}
        content_hash = hashlib.sha256(canonical(body).encode()).hexdigest()
        record = conn.execute("INSERT INTO records(team_id,project_id,kind,created_by) VALUES(%s,%s,%s,%s) RETURNING id", (team,project_id,item.kind,actor)).fetchone()[0]
        conn.execute("INSERT INTO record_revisions(record_id,revision,title,summary,payload,evidence_status,content_hash,created_by) VALUES(%s,1,%s,%s,%s,%s,%s,%s)", (record,item.title,item.summary,json.dumps(item.payload),item.evidence_status,content_hash,actor))
        conn.execute("INSERT INTO idempotency_keys(principal_id,project_id,key,request_hash,record_id) VALUES(%s,%s,%s,%s,%s)", (actor,project_id,idempotency_key,request_hash,record))
        conn.execute("INSERT INTO audit_events(actor_id,action,target_id,outcome) VALUES(%s,'publish',%s,'success')", (actor,record))
        return {"id": str(record), "revision": 1, "content_hash": content_hash}

@app.post("/v1/projects/{project_id}/search")
def search(project_id: UUID, query: SearchInput, x_principal: str = Header(...)):
    allowed = query.kinds or list(KINDS)
    if not set(allowed).issubset(KINDS): raise HTTPException(422, "invalid kinds")
    with psycopg.connect(DB) as conn:
        actor = principal(conn, x_principal); project_scope(conn,project_id,actor); bind_principal(conn, actor)
        rows = conn.execute("SELECT r.id,r.kind,r.current_revision,v.title,v.summary,v.content_hash FROM records r JOIN record_revisions v ON v.record_id=r.id AND v.revision=r.current_revision WHERE r.project_id=%s AND r.status='active' AND r.kind=ANY(%s) AND to_tsvector('simple',v.title || ' ' || v.summary) @@ websearch_to_tsquery('simple',%s) ORDER BY ts_rank(to_tsvector('simple',v.title || ' ' || v.summary),websearch_to_tsquery('simple',%s)) DESC,r.updated_at DESC LIMIT %s", (project_id,allowed,query.query,query.query,query.limit)).fetchall()
        return {"results":[{"id":str(x[0]),"kind":x[1],"revision":x[2],"title":x[3],"summary":x[4],"content_hash":x[5]} for x in rows],"note":"No result means no authorized record was retrieved."}

@app.get("/v1/projects/{project_id}/records/{record_id}")
def get_record(project_id: UUID, record_id: UUID, x_principal: str = Header(...)):
    with psycopg.connect(DB) as conn:
        actor = principal(conn, x_principal); project_scope(conn, project_id, actor); bind_principal(conn, actor)
        row = conn.execute("SELECT r.id,r.kind,r.current_revision,v.title,v.summary,v.payload,v.evidence_status,v.content_hash FROM records r JOIN record_revisions v ON v.record_id=r.id AND v.revision=r.current_revision WHERE r.id=%s AND r.project_id=%s AND r.status='active'", (record_id, project_id)).fetchone()
        if not row: raise HTTPException(404, "record not found")
        return {"id":str(row[0]),"kind":row[1],"revision":row[2],"title":row[3],"summary":row[4],"payload":row[5],"evidence_status":row[6],"content_hash":row[7]}

@app.post("/v1/projects/{project_id}/records/{record_id}/revisions", status_code=201)
def revise_record(project_id: UUID, record_id: UUID, item: RevisionInput, x_principal: str = Header(...), if_match: int = Header(...)):
    body = item.model_dump()
    with psycopg.connect(DB) as conn:
        actor = principal(conn, x_principal); project_scope(conn, project_id, actor); bind_principal(conn, actor)
        row = conn.execute("SELECT kind,current_revision FROM records WHERE id=%s AND project_id=%s AND status='active' FOR UPDATE", (record_id, project_id)).fetchone()
        if not row: raise HTTPException(404, "record not found")
        if row[1] != if_match: raise HTTPException(409, "revision conflict")
        next_revision = row[1] + 1
        content_hash = hashlib.sha256(canonical({"kind": row[0], **body}).encode()).hexdigest()
        conn.execute("INSERT INTO record_revisions(record_id,revision,title,summary,payload,evidence_status,content_hash,created_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)", (record_id,next_revision,item.title,item.summary,json.dumps(item.payload),item.evidence_status,content_hash,actor))
        conn.execute("UPDATE records SET current_revision=%s,updated_at=now() WHERE id=%s", (next_revision,record_id))
        conn.execute("INSERT INTO audit_events(actor_id,action,target_id,outcome) VALUES(%s,'revise',%s,'success')", (actor,record_id))
        return {"id":str(record_id),"revision":next_revision,"content_hash":content_hash}
