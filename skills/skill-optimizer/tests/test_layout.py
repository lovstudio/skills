import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))


def module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


layout = module("inspect_layout")
sync = module("sync_installation")


class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.sources = self.root / "sources"
        self.installs = self.root / "installs"
        self.installs.mkdir()
        self.addCleanup(patch.stopall)
        patch.object(layout.Path, "home", return_value=self.root / "home").start()
        patch.dict(layout.os.environ, {}, clear=True).start()
        patch.object(layout, "run_git", return_value=None).start()

    def skill(self, relative="source-skill", name="lov-source", paid=False):
        root = self.sources / relative
        spec = root / ("src/SKILL.md" if paid else "SKILL.md")
        spec.parent.mkdir(parents=True, exist_ok=True)
        spec.write_text("---\nname: " + name + "\n---\nTest instructions.\n")
        if paid:
            public = root / "public"
            public.mkdir()
            (public / "SKILL.md").write_text("---\nname: " + name + "\n---\nEncrypted wrapper.\n")
        return root

    def inspect(self, source):
        return layout.inspect(source, [str(self.installs)], [])

    def test_alias_is_discovered_by_frontmatter_identity(self):
        source = self.skill(name="lov-publisher")
        alias = self.installs / "old-publish-name"
        alias.symlink_to(source, target_is_directory=True)
        result = self.inspect(source)
        self.assertEqual(result["installations"][0]["path"], str(alias))
        self.assertEqual(result["distribution_state"], "complete")
        self.assertEqual(result["source"]["worktree"], "not_versioned")

    def test_equal_copy_is_not_a_canonical_symlink_target(self):
        source = self.skill()
        other = self.root / "copy"
        shutil.copytree(source, other)
        (self.installs / "lov-source").symlink_to(other, target_is_directory=True)
        self.assertEqual(self.inspect(source)["installations"][0]["state"], "wrong_target")

    def test_paid_source_link_is_not_publishable(self):
        source = self.skill(paid=True)
        installed = self.installs / "lov-source"
        installed.symlink_to(source, target_is_directory=True)
        self.assertEqual(self.inspect(source)["installations"][0]["state"], "wrong_target")
        self.assertEqual(sync.sync_target(source / "public", installed, False, False, source)["state"], "drifted")

    def test_paid_public_link_is_synced(self):
        source = self.skill(paid=True)
        (self.installs / "lov-source").symlink_to(source / "public", target_is_directory=True)
        self.assertEqual(self.inspect(source)["installations"][0]["state"], "synced")

    def test_missing_public_payload_does_not_fall_back_to_plaintext(self):
        source = self.skill(paid=True)
        shutil.rmtree(source / "public")
        with self.assertRaisesRegex(ValueError, "no installable"):
            sync.distribution_payload(source)
        self.assertIsNone(self.inspect(source)["payload"]["digest"])

    def test_broken_link_is_reported(self):
        source = self.skill()
        (self.installs / "lov-source").symlink_to(self.root / "missing")
        self.assertEqual(self.inspect(source)["installations"][0]["state"], "broken_link")

    def test_plan_does_not_create_missing_installation_directory(self):
        source = self.skill()
        target = self.root / "not-created" / "skill"
        before = sorted(str(p.relative_to(self.root)) for p in self.root.rglob("*"))
        result = sync.sync_target(source, target, False, False)
        self.assertEqual(result["before"]["missing"], ["SKILL.md"])
        self.assertFalse(target.parent.exists())
        self.assertEqual(before, sorted(str(p.relative_to(self.root)) for p in self.root.rglob("*")))

    def test_discovery_counts_paid_package_once_and_skips_generated_copies(self):
        paid = self.skill(paid=True)
        child = self.skill("kit-skill/skills/part", "lov-part")
        self.skill("output/export", "lov-output-copy")
        self.skill("kit-skill/assets/template", "lov-template")
        self.assertEqual(set(layout.discover_sources(self.sources)), {paid, child})

    def test_duplicate_sources_stay_ambiguous_until_install_target_is_unique(self):
        first = self.skill("one")
        self.skill("two")
        result = layout.inspect_all(self.sources, [str(self.installs)], [])
        self.assertEqual(result["summary"]["duplicate_ids"], 1)
        self.assertIsNone(result["identities"][0]["canonical_candidate"])
        (self.installs / "lov-source").symlink_to(first, target_is_directory=True)
        result = layout.inspect_all(self.sources, [str(self.installs)], [])
        self.assertEqual(result["identities"][0]["canonical_candidate"], str(first))
        self.assertEqual(result["identities"][0]["selection_evidence"], "unique_installation_target")

    def test_archived_split_catalog_is_legacy_unless_explicit(self):
        source = self.skill()
        for catalog, body in (("lovstudio-skills", "Test instructions.\n"), ("lovstudio-dev-skills", "Stale mirror.\n")):
            mirror = self.sources / catalog / "skills" / "source"
            mirror.mkdir(parents=True)
            (mirror / "SKILL.md").write_text("---\nname: lov-source\n---\n" + body)
        result = self.inspect(source)
        states = {Path(item["path"]).name: item["state"] for item in result["catalogs"]}
        self.assertEqual(states, {"lovstudio-skills": "synced", "lovstudio-dev-skills": "legacy"})
        self.assertEqual(result["catalog_state"], "complete")
        explicit = layout.inspect(source, [str(self.installs)], [str(self.sources / "lovstudio-dev-skills")])
        states = {Path(item["path"]).name: item["state"] for item in explicit["catalogs"]}
        self.assertEqual(states["lovstudio-dev-skills"], "drifted")
        self.assertEqual(explicit["catalog_state"], "partial")


if __name__ == "__main__":
    unittest.main()
