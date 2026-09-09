"""Small deterministic contracts. Never use shell=True for user content."""

import hashlib
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from importlib.resources import files
from pathlib import Path

from jsonschema import Draft202012Validator


class OpsError(Exception):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)


def digest(value):
    raw = value if isinstance(value, bytes) else encode(value).encode()
    return hashlib.sha256(raw).hexdigest()


def validate(kind, value):
    schema = json.loads(files("agentops").joinpath(f"resources/{kind}.schema.json").read_text())
    errors = list(Draft202012Validator(schema).iter_errors(value))
    if errors:
        raise OpsError(f"Contrato {kind}: " + "; ".join(e.message for e in errors[:3]))


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def atomic_write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".agentops-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as out:
            out.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def contained(root, path):
    root = Path(root).resolve()
    candidate = Path(path)
    candidate = (root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    if not candidate.is_relative_to(root) or candidate == root:
        raise OpsError("Caminho deve estar dentro da raiz autorizada, sem apontar para a raiz.")
    return candidate


SECRET = re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----|(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{24,})|https?://[^\s/@:]+:[^\s/@]+@")


def no_secrets(text):
    if SECRET.search(text):
        raise OpsError("Possível segredo detectado. Conteúdo não será exibido nem publicado.")


def run(argv, cwd=None, timeout=120, stdin=None):
    try:
        if isinstance(stdin, bytes):
            proc = subprocess.run(argv, cwd=cwd, input=stdin, capture_output=True,
                                  timeout=timeout, shell=False)
            proc.stdout = proc.stdout.decode("utf-8", errors="replace")
            proc.stderr = proc.stderr.decode("utf-8", errors="replace")
            return proc
        return subprocess.run(argv, cwd=cwd, input=stdin, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=timeout,
                              shell=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise OpsError(f"Execução indisponível ou excedeu {timeout}s: {argv[0]}") from exc


def confirm(message):
    if not __import__("sys").stdin.isatty():
        raise OpsError("Aprovação humana requer terminal interativo; use prévia/dry-run pelo agente.")
    if input(message + " Digite APROVAR: ").strip() != "APROVAR":
        raise OpsError("Operação não aprovada.")
