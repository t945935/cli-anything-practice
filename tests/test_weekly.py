"""每週流程的狀態轉換、來源定位與相依步驟。"""
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
spec = importlib.util.spec_from_file_location('weekly_example', ROOT / 'ch11/run_weekly.py')
weekly = importlib.util.module_from_spec(spec)
spec.loader.exec_module(weekly)


class WeeklyTests(unittest.TestCase):
    def test_partial_documents_are_not_silently_passed(self):
        counts = {'passed_basic_checks': 3, 'failed': 1, 'skipped': 1}
        self.assertEqual(weekly.document_status(1, counts), 'partial_failure')
        with self.assertRaises(ValueError):
            weekly.document_status(0, counts)

    def test_registration_three_requires_verified_artifacts(self):
        summary = {'counts': {'input': 8, 'valid': 4, 'issues': 3, 'duplicates': 1}}
        verified = dict.fromkeys(['all_written_cells_verified', 'totals_are_verified_numeric_values',
                                  'registration_ids_remain_text', 'source_unchanged'], True)
        self.assertEqual(weekly.registration_status(3, summary, verified), 'needs_review')
        with self.assertRaises(ValueError):
            weekly.registration_status(3, summary, {})

    def test_count_conservation_is_required(self):
        summary = {'counts': {'input': 8, 'valid': 4, 'issues': 0, 'duplicates': 1}}
        with self.assertRaises(ValueError):
            weekly.registration_status(0, summary, {})

    def test_overall_preserves_attention_and_failures(self):
        for stages, expected in [(['passed'], ('needs_review', 0)),
                                 (['passed', 'partial_failure'], ('attention_required', 3)),
                                 (['passed', 'needs_review'], ('attention_required', 3)),
                                 (['needs_review', 'failed'], ('failed', 1)),
                                 (['blocked'], ('failed', 1))]:
            with self.subTest(stages=stages):
                self.assertEqual(weekly.overall([{'status': item} for item in stages]), expected)

    def test_config_paths_are_relative_to_config_file(self):
        _, paths, docs, _ = weekly.prepare(ROOT / 'ch11/weekly.json', ROOT / 'output/unused-weekly-test')
        self.assertEqual(paths['lesson'], ROOT / 'ch07/lesson.json')
        self.assertEqual(len(docs), 5)

    def test_dry_run_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'new-output'
            with redirect_stdout(io.StringIO()):
                code = weekly.main(['--config', str(ROOT / 'ch11/weekly.json'), '--output', str(output), '--dry-run'])
            self.assertEqual(code, 0)
            self.assertFalse(output.exists())

    def test_independent_stages_continue_but_failed_lesson_blocks_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'run'
            fake = subprocess.CompletedProcess([], 1, '', 'simulated failure')
            with patch.object(weekly.subprocess, 'run', return_value=fake) as run:
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    code = weekly.main(['--config', str(ROOT / 'ch11/weekly.json'), '--output', str(output)])
            self.assertEqual(code, 1)
            self.assertEqual(run.call_count, 3)
            report = json.loads((output / 'weekly.json').read_text())
            rows = {row['name']: row['status'] for row in report['stages']}
            self.assertEqual(rows['documents'], 'failed')
            self.assertEqual(rows['registrations'], 'failed')
            self.assertEqual(rows['quality'], 'blocked')
            self.assertFalse((output / 'quality').exists())


if __name__ == '__main__':
    unittest.main()
