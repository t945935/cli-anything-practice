"""成品驗收：驗證能找出錯誤，不只測試正常輸出。"""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('audit_example', ROOT / 'ch10/audit_lesson.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class AuditTests(unittest.TestCase):
    def test_blocked_does_not_become_pass(self):
        status, code, counts = audit.summarize([{'status': 'passed'}, {'status': 'blocked'}])
        self.assertEqual((status, code, counts['blocked']), ('incomplete', 2, 1))

    def test_failed_has_priority_and_preserves_blocked_count(self):
        status, code, counts = audit.summarize([{'status': 'failed'}, {'status': 'blocked'}])
        self.assertEqual((status, code, counts['blocked']), ('failed', 1, 1))

    def test_expected_text_not_replaced_by_file_existence(self):
        with self.assertRaises(ValueError):
            audit.require_text('檔案存在，但不是指定內容', ['本週工作紀錄'])

    def test_image_extension_does_not_determine_real_format(self):
        with tempfile.TemporaryDirectory() as directory:
            fake = Path(directory) / 'square.png'
            fake.write_bytes((ROOT / 'reference/web.jpg').read_bytes())
            with self.assertRaises(ValueError):
                audit.check_image(fake, ('PNG', (600, 600)))

    def test_wrong_odf_mimetype_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            fake = Path(directory) / 'slides.odp'
            with zipfile.ZipFile(fake, 'w') as archive:
                archive.writestr('mimetype', 'application/vnd.oasis.opendocument.text')
                archive.writestr('content.xml', '<root/>')
            with self.assertRaisesRegex(ValueError, 'mimetype'):
                audit.check_odf(fake, {}, True)

    def test_existing_reference_pptx_and_wrong_source(self):
        module = audit.backend()
        lesson = module.load_lesson(ROOT / 'ch07/lesson.json')
        module.verify_pptx(ROOT / 'reference/lesson-slides.pptx', lesson['slides'])
        lesson['slides'][0]['title'] = '不在成品中的指定標題'
        with self.assertRaises(ValueError):
            module.verify_pptx(ROOT / 'reference/lesson-slides.pptx', lesson['slides'])


if __name__ == '__main__':
    unittest.main()
