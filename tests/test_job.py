"""工作狀態、回應契約及重試隔離；不啟動 LibreOffice。"""
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
spec = importlib.util.spec_from_file_location('job_example', ROOT / 'ch09/run_job.py')
job = importlib.util.module_from_spec(spec)
spec.loader.exec_module(job)


def response(command, ok=True, data=None):
    return subprocess.CompletedProcess([], 0 if ok else 3, json.dumps({
        'schema_version': 1, 'command': command, 'ok': ok,
        'data': data if data is not None else {},
        'error': None if ok else {'code': 'missing_dependency', 'message': 'missing tools'},
    }), '')


class JobTests(unittest.TestCase):
    def invoke(self, args):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return job.main(args)

    def test_protocol_rejects_unknown_version_wrong_types_and_conflicting_code(self):
        good = response('check')
        data = json.loads(good.stdout)
        cases = [(0, 'progress\n' + good.stdout), (0, '[]'), (1, good.stdout)]
        for update in [{'schema_version': 2}, {'schema_version': True}, {'ok': 'true'}, {'command': 'build'}, {'error': {}}]:
            cases.append((0, json.dumps(dict(data, **update))))
        for code, text in cases:
            with self.subTest(text=text), self.assertRaises(ValueError):
                job.validate_response(subprocess.CompletedProcess([], code, text, ''), 'check')

    def test_lock_rejects_second_writer(self):
        with tempfile.TemporaryDirectory() as directory:
            with job.locked(Path(directory)):
                with self.assertRaises(ValueError):
                    with job.locked(Path(directory)):
                        self.fail('second writer acquired lock')

    def test_atomic_replace_failure_preserves_old_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json'
            job.write_json(path, {'status': 'old'})
            with patch.object(job.os, 'replace', side_effect=OSError('disk error')):
                with self.assertRaises(OSError):
                    job.write_json(path, {'status': 'new'})
            self.assertEqual(json.loads(path.read_text()), {'status': 'old'})
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_failed_retry_gets_new_attempt_and_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / 'job'
            args = ['start', '--input', str(ROOT / 'ch07/lesson.json'), '--job-dir', str(folder), '--workspace', str(ROOT)]
            with patch.object(job.subprocess, 'run', return_value=response('doctor', False)):
                self.assertEqual(self.invoke(args), 1)
                original = (folder / 'attempt-001/doctor.json').read_bytes()
                self.assertEqual(self.invoke(['retry', '--job-dir', str(folder)]), 1)
                self.assertEqual(self.invoke(['retry', '--job-dir', str(folder)]), 1)
                self.assertEqual(self.invoke(['retry', '--job-dir', str(folder)]), 2)
            self.assertEqual((folder / 'attempt-001/doctor.json').read_bytes(), original)
            state = job.read_state(folder)
            self.assertEqual(len(state['attempts']), 3)
            self.assertTrue((folder / 'attempt-002/doctor.json').exists())

    def test_modified_snapshot_and_uncertain_state_block_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / 'job'
            with patch.object(job.subprocess, 'run', return_value=response('doctor', False)):
                self.invoke(['start', '--input', str(ROOT / 'ch07/lesson.json'), '--job-dir', str(folder)])
            snapshot = folder / 'input.json'
            original = snapshot.read_bytes()
            snapshot.write_bytes(b'changed')
            with patch.object(job.subprocess, 'run') as run:
                self.assertEqual(self.invoke(['retry', '--job-dir', str(folder)]), 2)
                run.assert_not_called()
            snapshot.write_bytes(original)
            state = job.read_state(folder)
            state['status'] = 'building'
            job.write_json(folder / 'state.json', state)
            with patch.object(job.subprocess, 'run') as run:
                self.assertEqual(self.invoke(['retry', '--job-dir', str(folder)]), 2)
                run.assert_not_called()

    def test_success_requires_review_and_cannot_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / 'job'
            def run(args, **kwargs):
                command = args[6]
                data = {}
                if command == 'build':
                    output = Path(args[-1])
                    output.mkdir()
                    for name in job.FILES:
                        (output / name).write_bytes(b'fixture')
                    job.write_json(output / 'verification.json', {
                        'status': 'passed_basic_checks', 'source_sha256': job.digest((folder / 'input.json').read_bytes()),
                        'source_unchanged': True, 'pptx_slide_text_verified': True})
                    data = {'status': 'passed_basic_checks', 'needs_visual_review': True}
                return response(command, data=data)
            with patch.object(job.subprocess, 'run', side_effect=run):
                self.assertEqual(self.invoke(['start', '--input', str(ROOT / 'ch07/lesson.json'), '--job-dir', str(folder)]), 0)
            state = job.read_state(folder)
            self.assertEqual(state['status'], 'needs_review')
            self.assertEqual(len(state['attempts'][0]['artifact_sha256']), 5)
            before = (folder / 'state.json').read_bytes()
            self.assertEqual(self.invoke(['retry', '--job-dir', str(folder)]), 2)
            self.assertEqual((folder / 'state.json').read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
