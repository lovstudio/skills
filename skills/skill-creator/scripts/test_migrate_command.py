#!/usr/bin/env python3
"""Regression checks for non-execution, preservation and migration collisions."""
import hashlib
import tempfile
import unittest
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import migrate_command


class MigrationTests(unittest.TestCase):
    def test_original_is_never_executed_or_rewritten(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            command = root / "nested.md"
            original = b'---\ndescription: legacy\ndisable-model-invocation: true\n---\n!`touch should-not-exist`\n$ARGUMENTS\n'
            command.write_bytes(original)
            output = root / "migration"
            result = migrate_command.prepare(command, output, "sample", "microcopy")
            self.assertEqual(command.read_bytes(), original)
            self.assertEqual((output / "original.md").read_bytes(), original)
            self.assertEqual(result["source"]["sha256"], hashlib.sha256(original).hexdigest())
            self.assertFalse((root / "should-not-exist").exists())
            self.assertFalse(result["installed"])
            self.assertFalse(result["published"])
            self.assertTrue((output / "sample-skill" / "skill.yaml").is_file())
            with self.assertRaises(FileExistsError):
                migrate_command.prepare(command, output, "sample", "microcopy")

    def test_inventory_tracks_alias_and_invalid_yaml(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "command.md").write_text('---\nmodel: legacy\n---\n$ARGUMENTS\n')
            (root / "alias.md").symlink_to(root / "command.md")
            (root / "bad.md").write_text('---\nname: [\n---\n')
            report = migrate_command.inventory([root], [])
            self.assertEqual(report["count"], 2)
            self.assertEqual(sum(item["state"] == "blocked" for item in report["entries"]), 1)
            entry = next(item for item in report["entries"] if item["state"] != "blocked")
            self.assertEqual(len(entry["aliases"]), 1)
            self.assertIn("host-field:model", entry["findings"])


if __name__ == "__main__":
    unittest.main()
