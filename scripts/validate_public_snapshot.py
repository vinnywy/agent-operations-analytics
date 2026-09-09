"""Fast guard against accidental inclusion of known private identifiers or local state."""
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
FORBIDDEN_PARTS = {".git", ".venv", "__pycache__", "state.sqlite", "reports", "backups"}
FORBIDDEN_TEXT = ("M07-Inteli", "Motiva", "GitLab", "vinnywy/agent-operations")

def main() -> int:
    failures = []
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if "__pycache__" in path.parts or relative == Path("scripts/validate_public_snapshot.py"):
            continue
        if any(part in FORBIDDEN_PARTS for part in path.parts):
            failures.append(f"forbidden path: {path.relative_to(ROOT)}")
        if path.is_file() and "tests" not in path.parts and path.suffix in {".md", ".py", ".toml", ".yaml", ".json", ".sql"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            for term in FORBIDDEN_TEXT:
                if term in text:
                    failures.append(f"private term {term!r}: {path.relative_to(ROOT)}")
    if failures:
        print("\n".join(failures)); return 1
    print("public snapshot check: PASS"); return 0

if __name__ == "__main__":
    raise SystemExit(main())
