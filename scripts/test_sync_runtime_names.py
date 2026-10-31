import importlib.util
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

import yaml

spec = importlib.util.spec_from_file_location('runtime_names', Path(__file__).with_name('sync-runtime-names.py'))
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

SYNCED_AT = datetime(2026, 10, 31, 12, 0, 5, tzinfo=timezone.utc)


class RuntimeNamesTest(unittest.TestCase):
    def test_runtime_field_can_follow_display_name(self):
        source = 'skills:\n- name: foo\n  display_name: Foo Studio\n  runtime_name: lov-foo\n  name_zh: 示例工坊\n'
        self.assertEqual(runtime.rewrite(source, {'foo': 'lov-foo'}), source)

    def test_repairs_duplicate_fields_without_changing_other_metadata(self):
        source = 'skills:\n- name: foo\n  runtime_name: lov-foo\n  display_name: Foo Studio\n  runtime_name: lov-foo\n  price_credits: 14\n'
        expected = 'skills:\n- name: foo\n  runtime_name: lov-foo\n  display_name: Foo Studio\n  price_credits: 14\n'
        self.assertTrue(runtime.duplicate_runtime_fields(source))
        updated = runtime.rewrite(source, {'foo': 'lov-foo'})
        self.assertEqual(updated, expected)
        self.assertEqual(runtime.duplicate_runtime_fields(updated), [])
        self.assertEqual(runtime.rewrite(updated, {'foo': 'lov-foo'}), updated)

    def test_adds_missing_field_and_preserves_unselected_entries(self):
        source = 'skills:\n- name: foo\n  display_name: Foo\n- name: bar\n  display_name: Bar\n'
        expected = source.replace('- name: foo\n', '- name: foo\n  runtime_name: lov-foo\n')
        self.assertEqual(runtime.rewrite(source, {'foo': 'lov-foo'}), expected)


class VersionSyncTest(unittest.TestCase):
    def test_bumped_version_restamps_updated_at_and_leaves_other_entries(self):
        source = (
            'skills:\n- name: foo\n  runtime_name: lov-foo\n  updated_at: 2026-09-25 16:54:46+00:00\n'
            '  display_name: Foo\n  version: 1.2.1\n  paid: false\n'
            "- name: bar\n  runtime_name: lov-bar\n  updated_at: '2026-09-10T03:05:00Z'\n  version: 0.1.0\n"
        )
        expected = source.replace('2026-09-25 16:54:46+00:00', '2026-10-31 12:00:05+00:00').replace('1.2.1', '1.2.2')
        versions = {'foo': '1.2.2', 'bar': '0.1.0'}
        catalog = {skill['name']: skill for skill in yaml.safe_load(source)['skills']}
        self.assertEqual(len(runtime.validate_versions(catalog, versions)), 1)
        updated = runtime.rewrite_versions(source, versions, SYNCED_AT)
        self.assertEqual(updated, expected)
        catalog = {skill['name']: skill for skill in yaml.safe_load(updated)['skills']}
        self.assertEqual(runtime.validate_versions(catalog, versions), [])
        self.assertEqual(runtime.rewrite_versions(updated, versions, datetime.now(timezone.utc)), updated)

    def test_keeps_quote_style_and_adds_missing_updated_at(self):
        source = "skills:\n- name: foo\n  runtime_name: lov-foo\n  version: '0.1.0'\n  display_name: Foo\n"
        expected = source.replace("  version: '0.1.0'\n", "  version: '0.2.0'\n  updated_at: 2026-10-31 12:00:05+00:00\n")
        self.assertEqual(runtime.rewrite_versions(source, {'foo': '0.2.0'}, SYNCED_AT), expected)

    def test_quotes_versions_yaml_would_load_as_numbers(self):
        source = 'skills:\n- name: foo\n  version: 1.9.0\n'
        updated = runtime.rewrite_versions(source, {'foo': '1.10'}, SYNCED_AT)
        self.assertEqual(yaml.safe_load(updated)['skills'][0]['version'], '1.10')

    def test_takes_metadata_version_from_free_mirrors_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ('free-tool', 'paid-tool'):
                (Path(tmp) / name).mkdir()
                (Path(tmp) / name / 'SKILL.md').write_text(
                    f'---\nname: lov-{name}\nversion: 0.0.1\nmetadata:\n  version: "1.2.3"\n---\n', encoding='utf-8'
                )
            catalog = {'free-tool': {'name': 'free-tool'}, 'paid-tool': {'name': 'paid-tool', 'paid': True}}
            with mock.patch.object(runtime, 'MIRROR_ROOT', Path(tmp)):
                self.assertEqual(runtime.expected_versions(catalog), ({'free-tool': '1.2.3'}, []))


if __name__ == '__main__':
    unittest.main()
