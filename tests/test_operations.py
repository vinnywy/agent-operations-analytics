import json
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
from subprocess import CompletedProcess

from agentops.common import OpsError, contained, digest, no_secrets, validate
from agentops.operations import Operations
from agentops import reviews, rfcs

SOURCE = Path(__file__).resolve().parents[1]


class OperationsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="agentops-test-")
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.artifact = self.workspace / "note.md"
        self.artifact.write_text("Resultado e limitação", encoding="utf-8")
        self.ops = Operations(self.root / "personal")
        self.ops.onboard(SOURCE, self.workspace, "Pessoa", "example/agent-operations")

    def tearDown(self):
        self.ops.store.close()
        self.temp.cleanup()

    def start(self, checks=None):
        spec = {"title": "Task", "objective": "Resultado", "scope": "Uma nota", "workflow": "documentation",
                "criteria": ["Nota válida"], "checks": checks or [], "sprint": "backlog"}
        return self.ops.start(spec)["task"]

    def ready(self, checks=None):
        task = self.start(checks)
        self.ops.transition(task, "active")
        self.ops.evidence(task, 1, "note.md")
        self.ops.transition(task, "validating")
        return task

    def test_onboarding_idempotent_preserves_profile(self):
        profile = self.ops.home / "profile.toml"
        original = profile.read_text(encoding="utf-8")
        self.ops.onboard(SOURCE, self.workspace, "Outro")
        self.assertEqual(original, profile.read_text(encoding="utf-8"))

    def test_personal_inside_workspace_rejected(self):
        other = Operations(self.workspace / "personal")
        try:
            with self.assertRaises(OpsError):
                other.onboard(SOURCE, self.workspace, "Pessoa")
        finally:
            other.store.close()

    def test_unknown_profile_authority_rejected(self):
        profile = self.ops.profile()
        profile["skip_tests"] = True
        with self.assertRaises(OpsError):
            validate("profile", profile)

    def test_invalid_transition(self):
        with self.assertRaises(OpsError):
            self.ops.transition(self.start(), "completed")

    def test_missing_evidence_blocks(self):
        task = self.start()
        self.ops.transition(task, "active")
        self.ops.transition(task, "validating")
        with self.assertRaises(OpsError):
            self.ops.check(task)

    def test_close_without_check_blocks(self):
        with self.assertRaises(OpsError):
            self.ops.close_task(self.ready())

    def test_happy_path_and_report(self):
        task = self.ready()
        self.ops.check(task)
        result = self.ops.close_task(task)
        self.assertEqual("completed", result["state"])
        self.assertIn("NOT_RUN", Path(result["report"]).read_text(encoding="utf-8"))

    def test_changed_evidence_invalidates(self):
        task = self.ready()
        self.ops.check(task)
        self.artifact.write_text("Mudou", encoding="utf-8")
        with self.assertRaises(OpsError):
            self.ops.close_task(task)

    def test_essential_check_executes_and_detects_failure(self):
        self.ops.configure_check("fails", [sys.executable, "-c", "raise SystemExit(1)"], ["note.md"])
        task = self.ready(["fails"])
        result = self.ops.check(task)
        self.assertEqual("FAIL", result["results"][1]["result"])
        with self.assertRaises(OpsError):
            self.ops.close_task(task)

    def test_changed_check_input_invalidates(self):
        inp = self.workspace / "config.json"
        inp.write_text("{}", encoding="utf-8")
        self.ops.configure_check("works", [sys.executable, "-c", "print('ok')"], ["config.json"])
        task = self.ready(["works"])
        self.ops.check(task)
        inp.write_text('{"changed":true}', encoding="utf-8")
        with self.assertRaises(OpsError):
            self.ops.close_task(task)

    def test_path_traversal_rejected(self):
        with self.assertRaises(OpsError):
            contained(self.workspace, "../outside")

    def test_review_is_opt_in_and_decline_deduplicates(self):
        task = self.start()
        a = reviews.plan(self.ops, task, "code", "targeted", ["note.md"], "Risco concreto")
        with self.assertRaises(OpsError):
            reviews.execute(self.ops, a["id"], "model", False)
        reviews.decide(self.ops, a["id"], "declined")
        b = reviews.plan(self.ops, task, "code", "targeted", ["note.md"], "Mesma oferta, outro texto")
        self.assertEqual(a["id"], b["id"])
        self.assertEqual("declined", b["state"])

    def test_review_changed_files_and_budget(self):
        task = self.start()
        item = reviews.plan(self.ops, task, "leakage", "targeted", ["note.md"], "Risco")
        reviews.decide(self.ops, item["id"], "accepted", "model")
        self.artifact.write_text("novo", encoding="utf-8")
        with self.assertRaises(OpsError):
            reviews.execute(self.ops, item["id"], "model")

    def test_review_preview_does_not_call_model(self):
        item = reviews.plan(self.ops, self.start(), "code", "targeted", ["note.md"], "Risco")
        reviews.decide(self.ops, item["id"], "accepted", "model")
        with patch("agentops.reviews.run") as runner:
            result = reviews.execute(self.ops, item["id"], "model")
            runner.assert_not_called()
            self.assertEqual("NOT_RUN", result["state"])

    def test_notebook_outputs_not_disclosed(self):
        path = self.workspace / "a.ipynb"
        path.write_text(json.dumps({"cells": [{"cell_type": "code", "source": ["print(1)"], "outputs": ["private output"]}]}))
        self.assertNotIn("private output", reviews.material(path))

    def test_rfc_preview_has_no_side_effect(self):
        data = json.loads((SOURCE / "templates/rfc.json").read_text())
        item = rfcs.draft(self.ops, data)
        with patch("agentops.rfcs.run") as runner:
            value = rfcs.publish(self.ops, item["id"])
            runner.assert_not_called()
            self.assertEqual("DRY_RUN", value["state"])

    def test_secret_rejected_without_echo(self):
        secret = "ghp_" + "a" * 30
        with self.assertRaises(OpsError) as caught:
            no_secrets(secret)
        self.assertNotIn(secret, str(caught.exception))

    def test_rfc_uncertain_does_not_retry_post(self):
        data = json.loads((SOURCE / "templates/rfc.json").read_text())
        item = rfcs.draft(self.ops, data)
        value = self.ops.store.get("rfc", item["id"])
        value["state"] = "uncertain"
        self.ops.store.put("rfc", value, item["id"])
        with patch("agentops.rfcs.run", return_value=CompletedProcess([], 0, "[]", "")) as runner:
            with self.assertRaises(OpsError):
                rfcs.publish(self.ops, item["id"], True)
            self.assertEqual(1, runner.call_count)

    def test_rfc_reconciles_existing_marker(self):
        item = rfcs.draft(self.ops, json.loads((SOURCE / "templates/rfc.json").read_text()))
        body = self.ops.store.get("rfc", item["id"])["body"]
        url = "https://github.com/example/agent-operations/issues/123"
        with patch("agentops.rfcs.run", return_value=CompletedProcess([], 0, json.dumps([{"url": url, "body": body}]), "")) as runner:
            self.assertEqual("recovered", rfcs.publish(self.ops, item["id"], True)["state"])
            self.assertEqual("already-published", rfcs.publish(self.ops, item["id"], True)["state"])
            self.assertEqual(1, runner.call_count)

    def test_review_model_approval_binding(self):
        item = reviews.plan(self.ops, self.start(), "code", "targeted", ["note.md"], "Risco")
        reviews.decide(self.ops, item["id"], "accepted", "approved")
        with patch("agentops.reviews.run") as runner:
            with self.assertRaises(OpsError):
                reviews.execute(self.ops, item["id"], "other", True)
            runner.assert_not_called()

    def test_review_rejects_input_budget_overflow(self):
        self.artifact.write_text("x" * 1100)
        with self.assertRaises(OpsError):
            reviews.plan(self.ops, self.start(), "code", "deep", ["note.md"], "Risco", 1000)

    def test_unknown_sprint_blocks_start(self):
        with self.assertRaises(OpsError):
            self.ops.start({"title": "Task", "objective": "Resultado", "scope": "Nota", "workflow": "documentation",
                            "criteria": ["Nota válida"], "checks": [], "sprint": "invented"})

    def test_integrate_preserves_existing_and_blocks_custom_skill(self):
        agents = self.workspace / "AGENTS.md"
        agents.write_text("# Existing\n", encoding="utf-8")
        result = self.ops.integration(True)
        self.assertTrue(agents.read_text(encoding="utf-8").startswith("# Existing"))
        self.assertGreater(len(result["files"]), 2)
        self.ops.integration(True)
        self.assertEqual(1, agents.read_text(encoding="utf-8").count("<!-- agentops:begin -->"))
        file = self.workspace / ".agents/skills/agentops-task/SKILL.md"
        file.write_text("changed", encoding="utf-8")
        with self.assertRaises(OpsError):
            self.ops.integration(True)

    def test_backup_is_valid_sqlite(self):
        backup = self.ops.store.backup()
        with closing(sqlite3.connect(backup)) as con:
            self.assertEqual("ok", con.execute("PRAGMA integrity_check").fetchone()[0])

    def test_newer_schema_is_rejected(self):
        other = self.root / "newer"
        other.mkdir()
        with closing(sqlite3.connect(other / "state.sqlite")) as con:
            con.execute("PRAGMA user_version=99")
        with self.assertRaises(OpsError):
            Operations(other)


if __name__ == "__main__":
    unittest.main()
