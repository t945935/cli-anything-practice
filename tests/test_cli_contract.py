"""驗收器本身的拒絕規則；實際命令流程另以參考介面驗證。"""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('textmeter_contract', ROOT / 'ch15/check_cli.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class ContractTests(unittest.TestCase):
    def response(self, **changes):
        data = dict(schema_version=1, command='analyze', ok=True,
                    data=dict(checker.EXPECTED), error=None)
        data.update(changes)
        return {'returncode': 0, 'stdout': json.dumps(data), 'stderr': ''}

    def test_stdout_noise_duplicate_keys_and_nonfinite_json_are_rejected(self):
        for text in ['hello\n{}', '{}\n{}', '{"ok":true,"ok":false}', '{"x":NaN}']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                checker.strict_json(text)

    def test_boolean_and_float_are_not_integer_statistics(self):
        for value in [True, 4.0, '4']:
            data = dict(checker.EXPECTED, lines=value)
            with self.subTest(value=value), self.assertRaises(ValueError):
                checker.check_stats(data, checker.EXPECTED)

    def test_schema_and_success_exit_must_agree(self):
        for version in [True, '1', 2]:
            with self.subTest(version=version), self.assertRaises(ValueError):
                checker.check_response(self.response(schema_version=version), 'analyze', True)
        log = self.response()
        log['returncode'] = 1
        with self.assertRaises(ValueError):
            checker.check_response(log, 'analyze', True)

    def test_nonzero_exit_without_error_evidence_is_not_expected_failure(self):
        log = self.response(ok=False, data=None, error={'code': '', 'message': ''})
        log['returncode'] = 1
        with self.assertRaises(ValueError):
            checker.check_response(log, 'analyze', False)
        log['stdout'] = json.dumps(dict(schema_version=1, ok=False, data=None,
                                      error={'code': 'missing', 'message': 'no file'}))
        self.assertIsNone(checker.check_response(log, 'analyze', False))

    def test_omitted_error_and_wrong_command_fail(self):
        for payload in [dict(schema_version=1, command='analyze', ok=True, data={}),
                        dict(schema_version=1, command='export', ok=True, data={}, error=None)]:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                checker.check_response({'returncode': 0, 'stdout': json.dumps(payload)}, 'analyze', True)

    def test_timeout_keeps_output_and_is_blocked(self):
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / 'command.json'
            with patch.object(checker.subprocess, 'run', side_effect=subprocess.TimeoutExpired('demo', 1, output=b'partial')):
                with self.assertRaises(checker.Blocked):
                    checker.invoke('demo', [], Path(folder), log, 1)
            saved = json.loads(log.read_text())
            self.assertEqual(saved['stdout'], 'partial')
            self.assertIsNone(saved['returncode'])

    def test_success_without_export_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            case = Path(folder) / 'export'
            payload = dict(schema_version=1, command='export', ok=True,
                           data={'stats': checker.EXPECTED, 'output': str(case / 'report.json')}, error=None)
            log = {'returncode': 0, 'stdout': json.dumps(payload), 'stderr': ''}
            with patch.object(checker, 'invoke', return_value=log):
                result = checker.run_case('demo', case, Path(folder), 'export', checker.SAMPLE, checker.EXPECTED, 'export', 1)
            self.assertEqual(result['status'], 'failed')
            self.assertIn('匯出檔案不存在', result['detail'])

    def test_input_mutation_cannot_be_hidden_by_correct_json(self):
        with tempfile.TemporaryDirectory() as folder:
            case = Path(folder) / 'sample'
            def mutate(*args):
                (case / '中文 範例.txt').write_bytes(b'changed')
                return self.response()
            with patch.object(checker, 'invoke', side_effect=mutate):
                result = checker.run_case('demo', case, Path(folder), 'sample', checker.SAMPLE, checker.EXPECTED, 'analyze', 1)
            self.assertEqual(result['status'], 'failed')
            self.assertFalse(result['protected_files_unchanged'])


if __name__ == '__main__':
    unittest.main()
