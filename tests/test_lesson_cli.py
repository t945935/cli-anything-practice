"""第八章介面契約；不呼叫原生 LibreOffice。"""
from contextlib import redirect_stdout, redirect_stderr
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('lesson_cli', ROOT / 'ch08/src/lesson_kit/cli.py')
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


class LessonCliTests(unittest.TestCase):
    def call(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = cli.main(['--workspace', str(ROOT), '--json', *map(str, args)])
        self.assertEqual(stderr.getvalue(), '')
        return code, json.loads(stdout.getvalue())

    def test_check_success(self):
        code, result = self.call('check', ROOT / 'ch07/lesson.json')
        self.assertEqual(code, 0)
        self.assertTrue(result['ok'])
        self.assertEqual(result['data']['slides'], 4)
        self.assertIsNone(result['error'])

    def test_plan_handles_spaces_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / '課程 資料.json'
            source.write_bytes((ROOT / 'ch07/lesson.json').read_bytes())
            target = Path(directory) / '尚未建立' / '教材 輸出'
            code, result = self.call('plan', source, '--output', target)
            self.assertEqual(code, 0)
            self.assertEqual(result['data']['output'], str(target))
            self.assertFalse(target.parent.exists())

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            sentinel = Path(directory) / 'keep.txt'
            sentinel.write_text('keep', encoding='utf-8')
            code, result = self.call('build', ROOT / 'ch07/lesson.json', '--output', directory)
            self.assertEqual(code, 2)
            self.assertEqual(result['error']['code'], 'output_exists')
            self.assertEqual(sentinel.read_text(), 'keep')

    def test_argument_error_is_json(self):
        code, result = self.call('build')
        self.assertEqual(code, 2)
        self.assertFalse(result['ok'])
        self.assertEqual(result['error']['code'], 'invalid_arguments')

    def test_missing_input_is_json(self):
        with tempfile.TemporaryDirectory() as directory:
            code, result = self.call('check', Path(directory) / 'missing.json')
        self.assertEqual(code, 2)
        self.assertEqual(result['error']['code'], 'invalid_input')

    def test_doctor_reports_missing_tools(self):
        with patch.object(cli.shutil, 'which', return_value=None):
            code, result = self.call('doctor')
        self.assertEqual(code, 3)
        self.assertEqual(result['error']['code'], 'missing_dependency')
        self.assertIsNone(result['data']['tools']['libreoffice'])

    def test_zero_exit_without_artifacts_is_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'output'
            fake = subprocess.CompletedProcess([], 0, stdout='success', stderr='')
            with patch.object(cli, 'require_environment'), patch.object(cli.subprocess, 'run', return_value=fake):
                code, result = self.call('build', ROOT / 'ch07/lesson.json', '--output', target)
            self.assertEqual(code, 1)
            self.assertEqual(result['error']['code'], 'invalid_result')

    def test_backend_error_is_not_mixed_into_stdout(self):
        with tempfile.TemporaryDirectory() as directory:
            fake = subprocess.CompletedProcess([], 1, stdout='backend log', stderr='export failed')
            with patch.object(cli, 'require_environment'), patch.object(cli.subprocess, 'run', return_value=fake):
                code, result = self.call('build', ROOT / 'ch07/lesson.json', '--output', Path(directory) / 'output')
            self.assertEqual(code, 1)
            self.assertEqual(result['data']['stderr'], 'export failed')


if __name__ == '__main__':
    unittest.main()
