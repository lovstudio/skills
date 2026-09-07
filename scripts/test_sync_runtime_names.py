import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('runtime_names', Path(__file__).with_name('sync-runtime-names.py'))
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


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


if __name__ == '__main__':
    unittest.main()
