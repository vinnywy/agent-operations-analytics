"""Small explicit behavioral runner. No calls occur without --execute."""

import json
import tempfile
from pathlib import Path
from jsonschema import Draft202012Validator

from .common import OpsError, atomic_write, digest, encode, no_secrets, now, read_json, run
from . import __version__


def evaluate(source, home, model=None, execute=False, timeout=60):
    if not 10 <= timeout <= 600:
        raise OpsError("Timeout de eval deve estar entre 10 e 600 segundos por caso.")
    cases = read_json(Path(source) / "evals/cases/smoke.json")
    if not execute:
        return {"state": "NOT_RUN", "cases": len(cases), "model": model,
                "note": "Execução opcional usa o cliente, consome cota e avalia apenas estes casos."}
    if not model:
        raise OpsError("Informe modelo explicitamente para eval com LLM.")
    protocol = (Path(source) / "AGENTS.md").read_text(encoding="utf-8") + "\n" + (Path(source) / "policy/operating-protocol.md").read_text(encoding="utf-8")
    results = []
    for case in cases:
        with tempfile.TemporaryDirectory(prefix="agentops-eval-") as temp:
            folder = Path(temp)
            atomic_write(folder / "AGENTS.md", protocol)
            schema = {"type": "object", "additionalProperties": False, "required": ["action", "reason"],
                      "properties": {"action": {"type": "string", "enum": case["choices"]}, "reason": {"type": "string"}}}
            atomic_write(folder / "schema.json", encode(schema))
            output = folder / "output.json"
            prompt = "Avalie o cenário como decisão de protocolo. Não use ferramentas. Responda pelo schema.\n" + case["input"]
            try:
                proc = run(["codex", "exec", "--ignore-user-config", "--ephemeral", "--skip-git-repo-check",
                            "--sandbox", "read-only", "-c", 'approval_policy="never"', "--model", model,
                            "-C", temp, "--output-schema", str(folder / "schema.json"), "-o", str(output), "-"], timeout=timeout, stdin=prompt)
                actual = read_json(output) if proc.returncode == 0 and output.exists() else {}
                if actual and not Draft202012Validator(schema).is_valid(actual):
                    actual = {}
                no_secrets(encode(actual))
                result = "PASS" if actual.get("action") == case["expected"] else "FAIL" if actual else "ERROR"
            except (OpsError, ValueError):
                actual, result = {}, "ERROR"
            results.append({"case": case["id"], "result": result, "actual": actual})
    report = {"model": model, "at": now(), "results": results, "tokens": None,
              "version": __version__, "protocol_sha256": digest(protocol.encode()), "cases_sha256": digest(cases),
              "coverage": "Decisões sintéticas; não testa segurança do host nem corrige automaticamente o protocolo."}
    path = Path(home) / "reports" / ("eval-" + now().replace(":", "-") + ".json")
    atomic_write(path, encode(report))
    return {"state": "PASS" if all(r["result"] == "PASS" for r in results) else "FAIL", "report": str(path), "results": results}
