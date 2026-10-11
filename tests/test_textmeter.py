"""第十四章起始後端與練習複本；不代表生成的 CLI 已通過測試。"""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


backend = load('textmeter_starter', ROOT / 'ch14/textmeter/textmeter.py')
lab = load('textmeter_lab', ROOT / 'ch14/prepare_lab.py')


class TextMeterTests(unittest.TestCase):
    def analyze(self, content):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / '中文 空白.txt'
            path.write_bytes(content)
            result = backend.analyze_file(path)
            self.assertEqual(path.read_bytes(), content)
            return result

    def test_sample_matches_independently_counted_values(self):
        folder = ROOT / 'ch14/textmeter/samples'
        result = backend.analyze_file(folder / '中文 範例.txt')
        self.assertEqual(result, json.loads((folder / 'expected.json').read_text()))
        self.assertEqual(result['nonspace_characters'], 20)

    def test_empty_and_whitespace_are_not_paragraphs(self):
        self.assertEqual(self.analyze(b'')['lines'], 0)
        result = self.analyze(' \t\n\u3000\n'.encode())
        self.assertEqual((result['lines'], result['nonempty_lines'], result['paragraphs'], result['nonspace_characters']), (2, 0, 0, 0))

    def test_newline_variants_and_trailing_blank_line(self):
        for newline in ['\n', '\r\n', '\r']:
            with self.subTest(newline=repr(newline)):
                result = self.analyze(newline.join(['A', 'B', '', 'C', '']).encode())
                self.assertEqual((result['lines'], result['paragraphs']), (4, 2))
        self.assertEqual(self.analyze(b'A\n\n')['lines'], 2)

    def test_bom_is_counted_in_bytes_but_not_characters(self):
        result = self.analyze(b'\xef\xbb\xbfA\n')
        self.assertEqual((result['bytes'], result['nonspace_characters']), (5, 1))

    def test_invalid_utf8_and_nul_are_rejected(self):
        for content in [b'\xff', b'A\x00B']:
            with self.subTest(content=content), self.assertRaises(ValueError):
                self.analyze(content)

    def test_size_boundary(self):
        self.assertEqual(self.analyze(b'A' * backend.MAX_BYTES)['bytes'], backend.MAX_BYTES)
        with self.assertRaises(ValueError):
            self.analyze(b'A' * (backend.MAX_BYTES + 1))

    def test_missing_path_and_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            for path in [Path(folder), Path(folder) / 'missing.txt']:
                with self.subTest(path=path), self.assertRaises(ValueError):
                    backend.analyze_file(path)

    def test_lab_preserves_source_and_refuses_existing_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / '練習 空間'
            target = lab.prepare(output)
            self.assertEqual((target / 'textmeter.py').read_bytes(), (ROOT / 'ch14/textmeter/textmeter.py').read_bytes())
            (target / 'textmeter.py').write_text('reader changes')
            with self.assertRaises(FileExistsError):
                lab.prepare(output)
            self.assertEqual((target / 'textmeter.py').read_text(), 'reader changes')
            self.assertNotEqual((ROOT / 'ch14/textmeter/textmeter.py').read_text(), 'reader changes')


if __name__ == '__main__':
    unittest.main()
