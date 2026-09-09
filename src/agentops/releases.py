"""Content manifests are local integrity only unless SSH verification succeeds."""

import json
import shutil
from pathlib import Path

from .common import OpsError, atomic_write, contained, digest, encode, now, read_json, run

ROOT_FILES = ("AGENTS.md", "README.md", "CHANGELOG.md", "pyproject.toml", ".gitignore", ".gitattributes")
ROOT_DIRS = ("src", "policy", ".agents", "contracts", "templates", "evals", "tests", "scripts", "docs", ".github")


def inventory(source):
    source = Path(source).resolve()
    paths = [source / name for name in ROOT_FILES if (source / name).is_file()]
    for name in ROOT_DIRS:
        paths.extend(p for p in (source / name).rglob("*") if p.is_file() and "__pycache__" not in p.parts and not p.name.endswith(".pyc") and not any(x.endswith(".egg-info") for x in p.parts))
    return {p.relative_to(source).as_posix(): digest(p.read_bytes()) for p in sorted(paths)}


def build_manifest(source, version):
    source = Path(source).resolve()
    data = {"schema_version": 1, "version": version, "files": inventory(source)}
    if "AGENTS.md" not in data["files"]:
        raise OpsError("Raiz do pacote inválida.")
    atomic_write(source / "release-manifest.json", encode(data))
    return {"manifest": str(source / "release-manifest.json"), "files": len(data["files"]), "authentication": "NOT_RUN"}


def verify_manifest(source):
    source = Path(source).resolve()
    path = source / "release-manifest.json"
    if not path.is_file():
        raise OpsError("Manifesto ausente.")
    data = read_json(path)
    for name in data["files"]:
        contained(source, name)
    if data["files"] != inventory(source):
        raise OpsError("Arquivos ausentes, adicionais ou modificados na instalação.")
    return {"integrity": "PASS", "version": data["version"], "authentication": "NOT_RUN"}


def verify_signature(source, allowed_signers, identity):
    source = Path(source).resolve()
    verify_manifest(source)
    proc = run(["ssh-keygen", "-Y", "verify", "-f", str(Path(allowed_signers).resolve()),
                "-I", identity, "-n", "agentops-release", "-s", str(source / "release-manifest.json.sig")],
               stdin=(source / "release-manifest.json").read_bytes())
    if proc.returncode:
        raise OpsError("Assinatura não autenticada pela identidade/chave confiável.")
    return {"integrity": "PASS", "authentication": "PASS", "identity": identity}


def stage_update(ops, candidate, allowed_signers, identity):
    candidate = Path(candidate).resolve()
    verify_signature(candidate, allowed_signers, identity)
    data = read_json(candidate / "release-manifest.json")
    release_key = digest(data)[:16]
    dest = ops.home / "releases" / release_key
    if dest.exists():
        verify_manifest(dest)
        return {"state": "already-staged", "path": str(dest)}
    dest.mkdir(parents=True)
    for name in data["files"]:
        out = contained(dest, name)
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(contained(candidate, name), out)
    for name in ("release-manifest.json", "release-manifest.json.sig"):
        shutil.copyfile(candidate / name, dest / name)
    verify_signature(dest, allowed_signers, identity)
    backup = ops.store.backup()
    record = {"state": "staged", "source": str(dest), "previous": ops.config()["source"], "backup": backup, "at": now()}
    ops.store.put("update", record)
    return dict(record, next="Instale a release em ambiente separado, execute aceitação e use onboarding em área de teste antes de trocar a instalação. Consulte docs/operations.md.")
