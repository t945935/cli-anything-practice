"""盤點與差異報告的範圍，不觸發升級或外部軟體。"""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('toolbox_example', ROOT / 'ch12/toolbox.py')
toolbox = importlib.util.module_from_spec(spec)
spec.loader.exec_module(toolbox)


class ToolboxTests(unittest.TestCase):
    def snapshot(self):
        return {'schema_version': 1, 'kind': 'toolbox_snapshot', 'captured_at': 'first',
                'runtime': {}, 'packages': {'pillow': {'version': '12.3.0'}},
                'tools': {}, 'repository': {}, 'checks': {'tests': {'status': 'not_run'}}}

    def test_time_and_test_log_noise_not_in_environment_comparison(self):
        first = self.snapshot()
        second = copy.deepcopy(first)
        second['captured_at'] = 'second'
        second['checks']['tests'] = {'returncode': 0, 'stderr': 'Ran tests in 0.123s'}
        self.assertEqual(toolbox.differences(toolbox.comparison_view(first), toolbox.comparison_view(second)), [])

    def test_changed_added_and_removed_are_distinct(self):
        changes = toolbox.differences({'package': {'version': '1'}, 'old': True}, {'package': {'version': '2'}, 'new': True})
        self.assertEqual({row['field']: row['change'] for row in changes},
                         {'package.version': 'changed', 'old': 'removed', 'new': 'added'})

    def test_probe_diagnostics_do_not_masquerade_as_version_changes(self):
        first = self.snapshot()
        first['tools']['libreoffice'] = {'path': '/example/libreoffice', 'file_sha256': 'abc',
                                       'returncode': 0, 'identifier': 'LibreOffice example', 'stderr': 'process 123 at 12:00'}
        second = copy.deepcopy(first)
        second['tools']['libreoffice']['stderr'] = 'process 456 at 12:01'
        self.assertEqual(toolbox.differences(toolbox.comparison_view(first), toolbox.comparison_view(second)), [])
        second['tools']['libreoffice']['identifier'] = 'LibreOffice changed'
        self.assertEqual(len(toolbox.differences(toolbox.comparison_view(first), toolbox.comparison_view(second))), 1)

    def test_unknown_snapshot_schema_is_rejected(self):
        for value in [True, 2, '1']:
            data = self.snapshot()
            data['schema_version'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                toolbox.comparison_view(data)

    def test_direct_install_records_commit_without_url(self):
        class Distribution:
            metadata = {'Name': 'Example_Package'}
            version = '1.0'
            def read_text(self, name):
                return json.dumps({'url': 'https://example.invalid/private-source',
                                   'vcs_info': {'vcs': 'git', 'commit_id': 'abc123'}})
        with patch.object(toolbox.metadata, 'distributions', return_value=[Distribution()]):
            packages = toolbox.installed_packages()
        self.assertEqual(packages['example-package']['source']['commit_id'], 'abc123')
        self.assertNotIn('url', packages['example-package']['source'])
        self.assertNotIn('example.invalid', json.dumps(packages))

    def test_manifest_detects_same_version_source_edit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'cli.py').write_text('print(1)')
            before = toolbox.tracked_manifest(root, 'cli.py\0')
            (root / 'cli.py').write_text('print(2)')
            after = toolbox.tracked_manifest(root, 'cli.py\0')
            self.assertNotEqual(before, after)


if __name__ == '__main__':
    unittest.main()
