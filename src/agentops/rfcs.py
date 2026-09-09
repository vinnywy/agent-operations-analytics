import json
import re
import tempfile
from pathlib import Path
from uuid import uuid4

from .common import OpsError, atomic_write, digest, encode, no_secrets, now, run, validate


def draft(ops, document):
    validate("rfc", document)
    no_secrets(encode(document))
    identifier = str(uuid4())
    headers = ("observation", "expected", "reproduction", "evidence", "mitigation", "alternatives", "risks", "eval", "acceptance", "version")
    metadata = {k: document[k] for k in ("area", "impact", "origin")}
    body = f"<!-- agentops-rfc:{identifier} -->\n<!-- agentops-meta:{json.dumps(metadata)} -->\n"
    body += "\n".join(f"\n## {k}\n\n{document[k]}\n" for k in headers)
    value = {"document": document, "body": body, "sha256": digest(body.encode()), "state": "draft", "at": now()}
    ops.store.put("rfc", value, identifier)
    path = ops.home / "rfc-drafts" / f"{identifier}.md"
    atomic_write(path, body)
    return {"id": identifier, "preview_file": str(path), "sha256": value["sha256"]}


def publish(ops, identifier, execute=False):
    value = ops.store.get("rfc", identifier)
    repo = ops.config().get("github_repository")
    if not repo or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise OpsError("Configure o destino oficial owner/repositório no onboarding.")
    body = value["body"]
    no_secrets(body)
    if not execute:
        return {"destination": repo, "title": value["document"]["title"], "body": body,
                "sha256": digest(body.encode()), "state": "DRY_RUN"}
    if value.get("url"):
        return {"url": value["url"], "state": "already-published"}
    # Search even on retry after uncertain failure. Never blindly repeat POST.
    found = run(["gh", "issue", "list", "--repo", repo, "--state", "all", "--search", f'"agentops-rfc:{identifier}" in:body', "--json", "url,body", "--limit", "100"])
    if found.returncode:
        raise OpsError("Não foi possível verificar duplicação; publicação interrompida.")
    for issue in json.loads(found.stdout):
        if f"<!-- agentops-rfc:{identifier} -->" in issue.get("body", ""):
            value.update(url=issue["url"], state="published")
            ops.store.put("rfc", value, identifier)
            return {"url": value["url"], "state": "recovered"}
    if value["state"] == "uncertain":
        raise OpsError("Publicação anterior incerta e busca pode estar desatualizada. Confira no GitHub antes de nova tentativa; não será repetida automaticamente.")
    value["state"] = "uncertain"
    ops.store.put("rfc", value, identifier)
    with tempfile.TemporaryDirectory(prefix="agentops-rfc-") as folder:
        path = Path(folder) / "body.md"
        atomic_write(path, body)
        proc = run(["gh", "issue", "create", "--repo", repo, "--title", "[RFC] " + value["document"]["title"], "--body-file", str(path)])
    if proc.returncode:
        raise OpsError("Publicação não confirmada. Estado uncertain preservado para reconciliação.")
    url = proc.stdout.strip()
    if not re.fullmatch(r"https://github\.com/" + re.escape(repo) + r"/issues/\d+", url):
        raise OpsError("Resposta inesperada; conferir Issue antes de repetir.")
    value.update(url=url, state="published", published_at=now())
    ops.store.put("rfc", value, identifier)
    return {"url": url, "state": "published", "labels": "pending-server-triage"}
