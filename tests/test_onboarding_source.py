import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentops.cli import main


class OnboardingSourceTests(unittest.TestCase):
    def test_missing_source_returns_actionable_code_without_creating_config(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home, workspace, wrong = root / "home", root / "workspace", root / "wrong"
            workspace.mkdir(); wrong.mkdir()
            with patch("sys.stderr") as stderr:
                result = main(["--home", str(home), "onboard", "--source", str(wrong), "--workspace", str(workspace), "--name", "A"])
            self.assertEqual(2, result)
            self.assertFalse((home / "installation.json").exists())

if __name__ == "__main__":
    unittest.main()
