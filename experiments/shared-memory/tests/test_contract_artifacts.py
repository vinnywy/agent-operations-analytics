from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]

class ContractArtifactTests(unittest.TestCase):
    def test_migration_declares_scope_and_revisions(self):
        migration = (ROOT / "migrations/001_initial.sql").read_text(encoding="utf-8")
        for token in ("team_id", "record_revisions", "idempotency_keys", "audit_events", "ENABLE ROW LEVEL SECURITY", "CREATE ROLE lab_app"):
            self.assertIn(token, migration)

    def test_contract_requires_idempotency(self):
        text = (ROOT / "contracts/openapi.yaml").read_text(encoding="utf-8")
        self.assertIn("Idempotency-Key", text)

if __name__ == "__main__":
    unittest.main()
