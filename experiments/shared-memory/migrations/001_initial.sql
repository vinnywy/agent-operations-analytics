CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE ROLE lab_app LOGIN PASSWORD 'lab_only_change_me' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;

CREATE TABLE teams (id uuid PRIMARY KEY, name text NOT NULL UNIQUE);
CREATE TABLE principals (id uuid PRIMARY KEY, label text NOT NULL UNIQUE, enabled boolean NOT NULL DEFAULT true);
CREATE TABLE memberships (team_id uuid REFERENCES teams(id), principal_id uuid REFERENCES principals(id), role text NOT NULL CHECK(role IN ('member','maintainer')), PRIMARY KEY(team_id, principal_id));
CREATE TABLE projects (id uuid PRIMARY KEY, team_id uuid NOT NULL REFERENCES teams(id), name text NOT NULL, UNIQUE(id, team_id));
CREATE TABLE records (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), team_id uuid NOT NULL REFERENCES teams(id), project_id uuid NOT NULL,
  kind text NOT NULL CHECK(kind IN ('task-summary','finding','decision','experiment-summary','dataset-note','rfc-reference')),
  status text NOT NULL DEFAULT 'active' CHECK(status IN ('active','superseded','retracted')), current_revision integer NOT NULL DEFAULT 1,
  created_by uuid NOT NULL REFERENCES principals(id), created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY(project_id,team_id) REFERENCES projects(id,team_id)
);
CREATE TABLE record_revisions (
  record_id uuid REFERENCES records(id), revision integer NOT NULL, title text NOT NULL CHECK(length(title) <= 240), summary text NOT NULL CHECK(length(summary) <= 600),
  payload jsonb NOT NULL DEFAULT '{}'::jsonb, evidence_status text NOT NULL CHECK(evidence_status IN ('observed','unverified','reviewed','retracted')),
  content_hash text NOT NULL CHECK(length(content_hash)=64), created_by uuid NOT NULL REFERENCES principals(id), created_at timestamptz NOT NULL DEFAULT now(), expires_at timestamptz,
  PRIMARY KEY(record_id,revision)
);
CREATE TABLE idempotency_keys (principal_id uuid REFERENCES principals(id), project_id uuid REFERENCES projects(id), key text NOT NULL, request_hash text NOT NULL, record_id uuid REFERENCES records(id), expires_at timestamptz NOT NULL DEFAULT now() + interval '24 hours', PRIMARY KEY(principal_id,project_id,key));
CREATE TABLE audit_events (id bigserial PRIMARY KEY, actor_id uuid REFERENCES principals(id), action text NOT NULL, target_id uuid, request_id uuid NOT NULL DEFAULT gen_random_uuid(), outcome text NOT NULL, at timestamptz NOT NULL DEFAULT now());
CREATE INDEX records_scope_idx ON records(team_id, project_id, status, updated_at DESC);
CREATE INDEX revisions_search_idx ON record_revisions USING GIN(to_tsvector('simple', title || ' ' || summary));

GRANT SELECT ON teams, principals, memberships, projects TO lab_app;
GRANT SELECT, INSERT, UPDATE ON records, record_revisions, idempotency_keys, audit_events TO lab_app;
GRANT USAGE, SELECT ON SEQUENCE audit_events_id_seq TO lab_app;
ALTER TABLE records ENABLE ROW LEVEL SECURITY;
ALTER TABLE record_revisions ENABLE ROW LEVEL SECURITY;
CREATE POLICY records_scope ON records TO lab_app USING (EXISTS (SELECT 1 FROM memberships m WHERE m.team_id=records.team_id AND m.principal_id=current_setting('app.principal_id', true)::uuid)) WITH CHECK (EXISTS (SELECT 1 FROM memberships m WHERE m.team_id=records.team_id AND m.principal_id=current_setting('app.principal_id', true)::uuid));
CREATE POLICY revisions_scope ON record_revisions TO lab_app USING (EXISTS (SELECT 1 FROM records r JOIN memberships m ON m.team_id=r.team_id WHERE r.id=record_revisions.record_id AND m.principal_id=current_setting('app.principal_id', true)::uuid)) WITH CHECK (EXISTS (SELECT 1 FROM records r JOIN memberships m ON m.team_id=r.team_id WHERE r.id=record_revisions.record_id AND m.principal_id=current_setting('app.principal_id', true)::uuid));

-- Fixtures: alpha contains analyst_a and analyst_b; beta contains analyst_c.
INSERT INTO teams VALUES ('00000000-0000-0000-0000-000000000001','alpha'),('00000000-0000-0000-0000-000000000002','beta');
INSERT INTO principals VALUES ('00000000-0000-0000-0000-000000000011','analyst_a',true),('00000000-0000-0000-0000-000000000012','analyst_b',true),('00000000-0000-0000-0000-000000000013','analyst_c',true);
INSERT INTO memberships VALUES ('00000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000011','member'),('00000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000012','member'),('00000000-0000-0000-0000-000000000002','00000000-0000-0000-0000-000000000013','member');
INSERT INTO projects VALUES ('10000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000001','synthetic-sales'),('20000000-0000-0000-0000-000000000002','00000000-0000-0000-0000-000000000002','isolated-project');
