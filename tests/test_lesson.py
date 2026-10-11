"""課程資料檢查與 dry-run 的無寫入契約。"""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'ch07/build_lesson.py'
spec = importlib.util.spec_from_file_location('lesson_example', SCRIPT)
lesson = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lesson)


class LessonTests(unittest.TestCase):
    def test_dry_run_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'output'
            result = subprocess.run([sys.executable, str(SCRIPT), '--input', str(ROOT / 'ch07/lesson.json'),
                                     '--output', str(target), '--dry-run'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['slides'], 4)
            self.assertFalse(target.exists())

    def test_incomplete_or_overlong_content_is_rejected(self):
        original = lesson.load_lesson(ROOT / 'ch07/lesson.json')
        cases = []
        missing_notes = copy.deepcopy(original)
        del missing_notes['slides'][0]['notes']
        cases.append(missing_notes)
        too_long = copy.deepcopy(original)
        too_long['slides'][0]['points'][0] = '字' * 37
        cases.append(too_long)
        too_many = copy.deepcopy(original)
        too_many['slides'][0]['points'].append('第四個重點')
        cases.append(too_many)
        cases.append(dict(original, slides=[]))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'lesson.json'
            for index, case in enumerate(cases):
                path.write_text(json.dumps(case), encoding='utf-8')
                with self.subTest(index=index), self.assertRaises(ValueError):
                    lesson.load_lesson(path)


if __name__ == '__main__':
    unittest.main()
