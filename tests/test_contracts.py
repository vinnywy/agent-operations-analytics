import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

from agentops.common import OpsError, atomic_write, no_secrets
from agentops import __version__
from agentops.releases import build_manifest, verify_manifest, verify_signature
from agentops.evaluations import evaluate

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('triage_rfc', ROOT / 'scripts/triage_rfc.py')
triage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(triage)


class ContractTests(unittest.TestCase):
    def test_package_and_runtime_versions_match(self):
        with (ROOT / 'pyproject.toml').open('rb') as source:
            self.assertEqual(tomllib.load(source)['project']['version'], __version__)

    def test_protocol_small(self):
        self.assertLessEqual((ROOT / 'AGENTS.md').stat().st_size, 6144)

    def test_documentation_links(self):
        docs = [ROOT / 'README.md', *ROOT.glob('docs/*.md')]
        for path in docs:
            for dest in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
                if '://' not in dest and not dest.startswith('#'):
                    self.assertTrue((path.parent / dest.split('#')[0]).exists(), f'{path.name}: {dest}')

    def test_docs_are_project_independent(self):
        for path in [ROOT / 'README.md', *ROOT.glob('docs/*.md'), *ROOT.glob('policy/*.md')]:
            self.assertIsNone(re.search(r'\b(Motiva|PSD|GitLab)\b', path.read_text(encoding='utf-8'), re.I), path.name)

    def test_no_known_secrets_in_distribution(self):
        for directory in ('docs', 'policy', 'src', '.agents', 'templates'):
            for path in (ROOT / directory).rglob('*'):
                if path.suffix in ('.md', '.py', '.json', '.toml'):
                    no_secrets(path.read_text(encoding='utf-8'))

    def test_all_skills_have_frontmatter(self):
        skills = list((ROOT / '.agents/skills').glob('*/SKILL.md'))
        self.assertEqual(9, len(skills))
        for path in skills:
            content = path.read_text(encoding='utf-8')
            self.assertTrue(content.startswith('---\nname: '))
            self.assertIn('\ndescription:', content)

    def test_eval_preview_never_calls_client(self):
        with patch('agentops.evaluations.run') as run:
            result = evaluate(ROOT, ROOT, execute=False)
            self.assertEqual('NOT_RUN', result['state'])
            self.assertEqual(6, result['cases'])
            run.assert_not_called()

    def test_triage_allows_only_enums(self):
        good = '<!-- agentops-meta:{"area":"harness","impact":"low","origin":"agent"} -->'
        self.assertEqual(['type:rfc', 'area:harness', 'impact:low', 'origin:agent'], triage.classify(good))
        self.assertEqual([], triage.classify(good.replace('harness', '$(command)')))
        self.assertEqual([], triage.classify(good.replace('"area":', '"status":"accepted","area":')))
        self.assertEqual([], triage.classify(good + good))
        self.assertEqual([], triage.classify('<!-- agentops-meta:[] -->'))

    def test_triage_form(self):
        body = '### area\n\nsecurity\n\n### impact\n\ncritical\n\n### origin\n\nuser\n'
        self.assertIn('area:security', triage.classify(body))

    def test_manifest_tamper_and_extra_files(self):
        with tempfile.TemporaryDirectory(prefix='agentops-manifest-') as temp:
            root = Path(temp)
            atomic_write(root / 'AGENTS.md', 'Protocol\n')
            build_manifest(root, 'test')
            self.assertEqual('PASS', verify_manifest(root)['integrity'])
            atomic_write(root / 'policy/extra.md', 'new')
            with self.assertRaises(OpsError):
                verify_manifest(root)
            build_manifest(root, 'test')
            atomic_write(root / 'AGENTS.md', 'Changed')
            with self.assertRaises(OpsError):
                verify_manifest(root)

    @unittest.skipUnless(shutil.which('ssh-keygen'), 'OpenSSH not installed')
    def test_real_signature_and_wrong_identity(self):
        with tempfile.TemporaryDirectory(prefix='agentops-signature-') as temp:
            root = Path(temp)
            source = root / 'release'
            atomic_write(source / 'AGENTS.md', 'Protocol\n')
            build_manifest(source, 'test')
            key = root / 'test-key'
            subprocess.run(['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-f', str(key)], check=True, capture_output=True)
            subprocess.run(['ssh-keygen', '-Y', 'sign', '-f', str(key), '-n', 'agentops-release', str(source / 'release-manifest.json')], check=True, capture_output=True)
            signers = root / 'allowed_signers'
            atomic_write(signers, 'test ' + key.with_suffix('.pub').read_text(encoding='utf-8'))
            self.assertEqual('PASS', verify_signature(source, signers, 'test')['authentication'])
            with self.assertRaises(OpsError):
                verify_signature(source, signers, 'wrong')


if __name__ == '__main__':
    unittest.main()
