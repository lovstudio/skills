import tempfile
import unittest
from pathlib import Path

from skill_display_names import apply_catalog_names, apply_names, replace_title


class SkillDisplayNamesTest(unittest.TestCase):
    def test_title_keeps_identity_versions_and_code(self):
        source = '---\nname: lov-example\nmetadata:\n  version: "1.2.3"\n---\n\n```sh\n# shell comment\n```\n\n# Old title\n\nBody.\n'
        expected = source.replace('# Old title', '# 新名称 · New Name')
        self.assertEqual(replace_title(source, '新名称 · New Name'), expected)

    def test_paid_names_leave_ciphertext_and_manifest_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'SKILL.md').write_text('---\nname: lov-paid\n---\n# Old\nDecrypt with the helper.\n')
            (root / 'SKILL.md.enc').write_bytes(b'ciphertext')
            (root / 'MANIFEST.enc.json').write_text('{"version":"0.5.0"}')
            apply_names(root, '专业海报', 'Professional Poster')
            self.assertEqual((root / 'SKILL.md.enc').read_bytes(), b'ciphertext')
            self.assertEqual((root / 'MANIFEST.enc.json').read_text(), '{"version":"0.5.0"}')
            self.assertIn('name: lov-paid', (root / 'SKILL.md').read_text())

    def test_catalog_and_modules_are_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            parent = root / 'bp'
            child = parent / 'skills/deck'
            child.mkdir(parents=True)
            (parent / 'SKILL.md').write_text('---\nname: lov-bp\n---\n# Old\n')
            (child / 'SKILL.md').write_text('---\nname: lov-bp-deck\n---\n# Old deck\n')
            (parent / 'skill.yaml').write_text('id: lov-bp\nversion: 0.2.0\ndisplay_name: Old\n')
            rows = [{'name': 'bp', 'runtime_name': 'lov-bp', 'name_zh': 'BP 工坊', 'display_name': 'BP Studio'}]
            modules = {'lov-bp-deck': {'name_zh': 'BP 大师', 'display_name': 'BP Master'}}
            self.assertEqual(apply_catalog_names(root, rows, modules), 3)
            self.assertIn('# BP 大师 · BP Master', (child / 'SKILL.md').read_text())
            self.assertEqual(apply_catalog_names(root, rows, modules), 0)
            self.assertIn('version: 0.2.0', (parent / 'skill.yaml').read_text())

    def test_already_approved_title_is_preserved(self):
        original = '# GitHub 仓库简介优化\n\nBody.\n'
        self.assertEqual(replace_title(original, 'GitHub 仓库简介优化 · English Name', ('GitHub 仓库简介优化',)), original)


if __name__ == '__main__':
    unittest.main()
