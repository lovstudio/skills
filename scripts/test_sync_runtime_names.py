import contextlib
import importlib.util
import io
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


def catalog_of(text):
    return {skill['name']: skill for skill in yaml.safe_load(text)['skills']}


class DependencySyncTest(unittest.TestCase):
    def test_inserts_missing_items_in_declared_order_and_keeps_extras(self):
        source = (
            'skills:\n- name: foo\n  runtime_name: lov-foo\n  depends_on:\n  - extra\n  - b\n  pricing:\n    model: free_entry\n'
            '- name: a\n  runtime_name: lov-a\n- name: b\n  runtime_name: lov-b\n- name: c\n  runtime_name: lov-c\n'
            '- name: extra\n  runtime_name: lov-extra\n'
        )
        expected = source.replace('  - extra\n  - b\n', '  - extra\n  - a\n  - b\n  - c\n')
        declared = {'foo': ['lov-a', 'lov-b', 'lov-c']}
        lists, warnings = runtime.plan_dependencies(catalog_of(source), {}, declared)
        self.assertEqual((lists, warnings), ({'foo': ['extra', 'a', 'b', 'c']}, []))
        updated = runtime.rewrite_dependencies(source, lists)
        self.assertEqual(updated, expected)
        self.assertEqual(runtime.plan_dependencies(catalog_of(updated), {}, declared), ({}, []))

    def test_new_block_follows_tagline_zh_and_replaces_a_flow_list(self):
        source = (
            'skills:\n- name: foo\n  tagline_en: Foo for\n    everyone.\n  tagline_zh: 第一行\n    第二行。\n  pricing:\n    model: free_entry\n'
            '- name: bar\n  depends_on: []\n  tagline_zh: 栏\n- name: a\n'
        )
        expected = (
            source.replace('    第二行。\n', '    第二行。\n  depends_on:\n  - a\n')
            .replace('  depends_on: []\n', '  depends_on:\n  - a\n')
        )
        self.assertEqual(runtime.rewrite_dependencies(source, {'foo': ['a'], 'bar': ['a']}), expected)

    def test_refuses_an_edit_that_would_change_other_fields(self):
        source = 'skills:\n- name: foo\n  depends_on:\n    - a\n  version: 1.0.0\n- name: a\n- name: b\n'
        with self.assertRaises((ValueError, yaml.YAMLError)):
            runtime.rewrite_dependencies(source, {'foo': ['a', 'b']})

    def test_leaves_out_what_free_installs_cannot_take(self):
        source = (
            'skills:\n- name: foo\n  depends_on:\n  - legacy-paid\n'
            '- name: legacy-paid\n  paid: true\n- name: paid\n  paid: true\n'
            '- name: secret\n  pricing:\n    visibility: internal\n'
            '- name: wrapper\n  depends_on:\n  - paid\n- name: loop\n  depends_on:\n  - foo\n'
        )
        declared = {'foo': ['lov-missing', 'foo', 'legacy-paid', 'lov-paid', 'lov-secret', 'lov-wrapper', 'lov-loop']}
        runtime_names = {name: f'lov-{name}' for name in ('foo', 'legacy-paid', 'paid', 'secret', 'wrapper', 'loop')}
        lists, warnings = runtime.plan_dependencies(catalog_of(source), runtime_names, declared)
        self.assertEqual(lists, {})
        self.assertEqual(len(warnings), 6)
        for fragment in ('lov-missing, which has no catalog entry', 'lists itself', 'the paid entry paid;',
                         'the internal entry secret', 'lov-wrapper, which depends on the paid entry paid',
                         'loop already depends on foo'):
            self.assertTrue(any(fragment in warning for warning in warnings), fragment)
        self.assertFalse(any('legacy-paid' in warning for warning in warnings))

    def test_resolves_mirrored_runtime_names_before_catalog_ones(self):
        source = 'skills:\n- name: foo\n- name: x\n  runtime_name: lov-x-old\n- name: y\n  runtime_name: lov-y\n'
        lists, warnings = runtime.plan_dependencies(catalog_of(source), {'x': 'lov-x'}, {'foo': ['lov-x', 'y']})
        self.assertEqual((lists, warnings), ({'foo': ['x', 'y']}, []))

    def test_reads_declarations_from_free_mirrors_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name, depends_on in (('free-tool', '[lov-a]'), ('paid-tool', '[lov-b]'), ('odd-tool', 'lov-a')):
                (Path(tmp) / name).mkdir()
                (Path(tmp) / name / 'SKILL.md').write_text(f'---\nname: lov-{name}\ndepends_on: {depends_on}\n---\n', encoding='utf-8')
            catalog = {'free-tool': {}, 'paid-tool': {'paid': True}, 'odd-tool': {}}
            with mock.patch.object(runtime, 'MIRROR_ROOT', Path(tmp)):
                declared, warnings = runtime.declared_dependencies(catalog)
        self.assertEqual(declared, {'free-tool': ['lov-a']})
        self.assertEqual(warnings, ['odd-tool: SKILL.md depends_on is not a list of Skill names'])

    def test_write_mode_fills_the_catalog_and_only_warns_about_the_rest(self):
        source = (
            'version: 1\nskills:\n- name: foo\n  runtime_name: lov-foo\n  version: 0.1.0\n  tagline_zh: 示例\n'
            '- name: a\n  runtime_name: lov-a\n  version: 0.1.0\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'skills.yaml').write_text(source, encoding='utf-8')
            for name, depends_on in (('foo', '[lov-a, lov-missing]'), ('a', '[]')):
                (root / 'skills' / name).mkdir(parents=True)
                (root / 'skills' / name / 'SKILL.md').write_text(
                    f'---\nname: lov-{name}\ndepends_on: {depends_on}\nmetadata:\n  version: 0.1.0\n---\n', encoding='utf-8'
                )
            summary = root / 'summary.md'

            def run(*args):
                out, err = io.StringIO(), io.StringIO()
                env = {'GITHUB_ACTIONS': 'true', 'GITHUB_STEP_SUMMARY': str(summary)}
                with mock.patch.object(runtime, 'YAML_PATH', root / 'skills.yaml'), \
                        mock.patch.object(runtime, 'MIRROR_ROOT', root / 'skills'), \
                        mock.patch.dict('os.environ', env), \
                        mock.patch('sys.argv', ['sync-runtime-names.py', *args]), \
                        contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    code = runtime.main()
                return code, out.getvalue(), err.getvalue()

            code, _, err = run()
            self.assertEqual(code, 1)
            self.assertIn('foo.depends_on: lacks a, which its mirrored SKILL.md declares', err)
            code, out, _ = run('--write')
            self.assertEqual(code, 0)
            self.assertIn('foo.depends_on: added a', out)
            self.assertIn('::warning title=Declared dependency not listed::foo: SKILL.md declares lov-missing', out)
            self.assertEqual(
                (root / 'skills.yaml').read_text(encoding='utf-8'),
                source.replace('  tagline_zh: 示例\n', '  tagline_zh: 示例\n  depends_on:\n  - a\n'),
            )
            self.assertIn('- foo: SKILL.md declares lov-missing, which has no catalog entry', summary.read_text(encoding='utf-8'))
            self.assertEqual(run()[0], 0)


if __name__ == '__main__':
    unittest.main()
