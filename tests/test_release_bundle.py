"""交接資料的來源對應、雜湊與不覆寫規則。"""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('release_bundle', ROOT / 'ch16/make_bundle.py')
bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle)


def wheel(package, *, version='0.1.0', wrong_source=False):
    module, source, dependencies = bundle.PACKAGES[package]
    buffer = io.BytesIO()
    metadata = f'Name: {package}\nVersion: {version}\n'
    metadata += ''.join(f'Requires-Dist: {item}\n' for item in dependencies)
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr('example.dist-info/METADATA', metadata)
        archive.writestr(module, b'wrong source' if wrong_source else (ROOT / source).read_bytes())
    return buffer.getvalue()


class ReleaseBundleTests(unittest.TestCase):
    def test_wrong_version_or_source_is_rejected(self):
        package = next(iter(bundle.PACKAGES))
        for content in [wheel(package, version='9.9.9'), wheel(package, wrong_source=True)]:
            with self.subTest(content=content[:20]), self.assertRaises(ValueError):
                bundle.validate_wheel(content, package, ROOT)

    def test_corrupt_archive_is_rejected(self):
        with self.assertRaises(zipfile.BadZipFile):
            bundle.validate_wheel(b'not a wheel', next(iter(bundle.PACKAGES)), ROOT)

    def test_hash_pins_and_source_files_match_copied_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            wheels = root / 'wheels'
            wheels.mkdir()
            for package in bundle.PACKAGES:
                filename = package.replace('-', '_') + '-0.1.0-py3-none-any.whl'
                (wheels / filename).write_bytes(wheel(package))
            output = root / 'bundle'
            with patch.object(bundle.subprocess, 'run', side_effect=FileNotFoundError):
                bundle.make_bundle(wheels, output)
            for line in (output / 'SHA256SUMS').read_text().splitlines():
                expected, path = line.split('  ', 1)
                self.assertEqual(bundle.sha((output / path).read_bytes()), expected)
            requirements = (output / 'requirements.txt').read_text()
            for path in (output / 'wheels').iterdir():
                self.assertIn('--hash=sha256:' + bundle.sha(path.read_bytes()), requirements)
            self.assertEqual((output / 'check_cli.py').read_bytes(), (ROOT / 'ch15/check_cli.py').read_bytes())
            self.assertIsNone(json.loads((output / 'release.json').read_text())['repository_head'])

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sentinel = root / 'keep.txt'
            sentinel.write_text('keep')
            with self.assertRaises(ValueError):
                bundle.make_bundle(root / 'missing-wheels', root)
            self.assertEqual(sentinel.read_text(), 'keep')


if __name__ == '__main__':
    unittest.main()
