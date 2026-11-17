"""Execute only repository-authored examples locally; student code uses Docker.

Optional dependencies: Flask, pandas, matplotlib, scikit-learn, torch and PHP
with PDO SQLite. Set AI_ANKI_TEST_PHP to a portable PHP executable if needed.
"""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from server.practice_projects import catalog

PHP = os.environ.get('AI_ANKI_TEST_PHP') or shutil.which('php')


class PracticeSolutionsTest(unittest.TestCase):
    def verify(self, project):
        command = [PHP] if project['track'] == 'php' else [sys.executable]
        with TemporaryDirectory() as directory:
            root = Path(directory)
            def write(files):
                for name, text in files.items():
                    path = root / name; path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(text, encoding='utf-8')
            write(project['files'])
            checker = root / ('check.php' if project['track'] == 'php' else 'check.py')
            checker.write_text(project['checks'], encoding='utf-8')
            env = dict(os.environ, MPLBACKEND='Agg', MPLCONFIGDIR=str(root / 'mpl'), PYTHONUTF8='1')
            def run(args):
                return subprocess.run([*command, *args], cwd=root, env=env, capture_output=True, text=True, encoding='utf-8', timeout=60)
            first = run([str(checker), '0'])
            self.assertNotEqual(first.returncode, 0, project['id'] + ': starter should require learner code')
            write(project['solution'])
            for step in range(len(project['steps'])):
                result = run([str(checker), str(step)])
                self.assertEqual(result.returncode, 0, project['id'] + '\n' + result.stdout + result.stderr)
                self.assertIn(f'AI_ANKI_CHECK_OK:{step}', result.stdout)
            result = run([project['entrypoint']])
            self.assertEqual(result.returncode, 0, project['id'] + '\n' + result.stdout + result.stderr)
            if project['preview']:
                self.assertIn('<html', (root / 'artifacts/preview.html').read_text(encoding='utf-8').lower())

    def test_python_tasks(self):
        self.verify(catalog()['python-tasks'])

    @unittest.skipUnless(importlib.util.find_spec('flask'), 'Flask required')
    def test_python_flask(self):
        self.verify(catalog()['python-flask'])

    @unittest.skipUnless(all(importlib.util.find_spec(p) for p in ('pandas','matplotlib')), 'pandas/matplotlib required')
    def test_python_data(self):
        self.verify(catalog()['python-data'])

    @unittest.skipUnless(all(importlib.util.find_spec(p) for p in ('torch','sklearn')), 'PyTorch/scikit-learn required')
    def test_python_neural(self):
        self.verify(catalog()['python-neural'])

    @unittest.skipUnless(PHP, 'PHP required')
    def test_php_projects(self):
        for project in catalog().values():
            if project['track'] == 'php':
                with self.subTest(project=project['id']):
                    self.verify(project)


if __name__ == '__main__':
    unittest.main()
