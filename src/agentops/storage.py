"""Local state is not an adversary-resistant audit ledger."""

import json
import sqlite3
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from .common import OpsError, encode, now


class MemoryBackend(Protocol):
    def put(self, kind: str, value: dict, identifier: str | None = None) -> str: ...
    def get(self, kind: str, identifier: str) -> dict: ...
    def list(self, kind: str, limit: int = 20) -> list[dict]: ...


class LocalSQLiteBackend:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.directory / "state.sqlite", timeout=10)
        self.db.execute("PRAGMA foreign_keys=ON")
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version > 1:
            self.db.close()
            raise OpsError("Schema mais novo que este harness; atualização necessária.")
        with self.db:
            self.db.execute("CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, kind TEXT NOT NULL, body TEXT NOT NULL, updated TEXT NOT NULL)")
            self.db.execute("CREATE INDEX IF NOT EXISTS record_kind ON records(kind, updated)")
            self.db.execute("CREATE TABLE IF NOT EXISTS audit_events (id INTEGER PRIMARY KEY, record_id TEXT NOT NULL, action TEXT NOT NULL, at TEXT NOT NULL)")
            self.db.execute("PRAGMA user_version=1")

    def close(self):
        self.db.close()

    def put(self, kind, value, identifier=None):
        identifier = identifier or str(uuid4())
        value = dict(value, id=identifier)
        with self.db:
            self.db.execute("INSERT INTO records VALUES (?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET body=excluded.body, updated=excluded.updated", (identifier, kind, encode(value), now()))
            self.db.execute("INSERT INTO audit_events(record_id,action,at) VALUES (?,?,?)", (identifier, f"save:{kind}", now()))
        return identifier

    def get(self, kind, identifier):
        row = self.db.execute("SELECT body FROM records WHERE id=? AND kind=?", (identifier, kind)).fetchone()
        if not row:
            raise OpsError(f"Registro {kind} não encontrado: {identifier}")
        return json.loads(row[0])

    def list(self, kind, limit=20):
        if not 1 <= limit <= 1000:
            raise OpsError("Limite deve estar entre 1 e 1000.")
        return [json.loads(x[0]) for x in self.db.execute("SELECT body FROM records WHERE kind=? ORDER BY updated DESC LIMIT ?", (kind, limit))]

    def backup(self):
        target = self.directory / "backups" / (now().replace(":", "-") + ".sqlite")
        target.parent.mkdir(exist_ok=True)
        dest = sqlite3.connect(target)
        try:
            self.db.backup(dest)
        finally:
            dest.close()
        return str(target)
