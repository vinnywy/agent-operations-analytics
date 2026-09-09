import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agentops.common import atomic_write

ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def test_real_cli_onboard_task_report_and_preview(self):
        with tempfile.TemporaryDirectory(prefix='agentops-cli-') as temp:
            base = Path(temp)
            workspace = base / 'workspace'
            workspace.mkdir()
            home = base / 'personal'
            env = dict(os.environ, PYTHONUTF8='1')

            def cli(*args):
                proc = subprocess.run([sys.executable, '-m', 'agentops', '--home', str(home), *args],
                                      capture_output=True, encoding='utf-8', env=env, timeout=30)
                self.assertEqual(0, proc.returncode, proc.stderr)
                return json.loads(proc.stdout)

            cli('onboard', '--source', str(ROOT), '--workspace', str(workspace), '--name', 'Teste')
            cli('doctor')
            task = cli('task', 'start', '--briefing', str(ROOT / 'templates/briefing.json'))['task']
            cli('task', 'move', task, 'active')
            atomic_write(workspace / 'note.md', '# Resultado\n\nLimitação: smoke de fluxo, não semântica.\n')
            cli('evidence', task, '--criterion', '1', '--file', 'note.md')
            cli('task', 'move', task, 'validating')
            cli('check', task)
            result = cli('task', 'close', task)
            self.assertEqual('completed', result['state'])
            self.assertTrue(Path(result['report']).is_file())
            self.assertEqual('NOT_RUN', cli('eval')['state'])


if __name__ == '__main__':
    unittest.main()
