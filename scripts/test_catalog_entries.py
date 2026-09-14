import importlib.util
import unittest
from pathlib import Path

import catalog_entries

SCRIPTS = Path(__file__).parent


def load(filename, module_name):
    spec = importlib.util.spec_from_file_location(module_name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


INTERNAL = {"name": "staff-tool", "pricing": {"visibility": "internal"}}
FREE = {"name": "free-tool"}
PAID_ENCRYPTED = {"name": "paid-bundle", "paid": True, "encrypted_bundle": True}
PAID_PUBLIC_SOURCE = {"name": "paid-open", "paid": True, "public_source": True}


class ClassificationTest(unittest.TestCase):
    def test_internal_entry_is_never_installable(self):
        self.assertTrue(catalog_entries.is_internal(INTERNAL))
        self.assertFalse(catalog_entries.is_installable(INTERNAL))

    def test_internal_free_entry_is_not_installable(self):
        """The case that broke CI: free by price, internal by visibility, never mirrored."""
        entry = {"name": "lovstudio-web", "paid": False, "pricing": {"visibility": "internal"}}
        self.assertFalse(catalog_entries.is_installable(entry))

    def test_free_and_encrypted_paid_entries_are_installable(self):
        self.assertTrue(catalog_entries.is_installable(FREE))
        self.assertTrue(catalog_entries.is_installable(PAID_ENCRYPTED))

    def test_public_source_paid_entry_has_no_mirror(self):
        self.assertFalse(catalog_entries.is_installable(PAID_PUBLIC_SOURCE))

    def test_entry_without_pricing_block_is_not_internal(self):
        self.assertFalse(catalog_entries.is_internal(FREE))
        self.assertFalse(catalog_entries.is_internal({"name": "x", "pricing": None}))


class NoMirrorDemandedForInternalTest(unittest.TestCase):
    """sync-runtime-names must not demand a mirror that sync-skills never creates."""

    def test_internal_entry_reports_no_error(self):
        runtime = load("sync-runtime-names.py", "runtime_names_for_internal")
        catalog = {"staff-tool": INTERNAL, "paid-open": PAID_PUBLIC_SOURCE}
        names, errors = runtime.expected_runtime_names(catalog)
        self.assertEqual(errors, [])
        self.assertEqual(names, {})

    def test_missing_mirror_for_public_free_entry_still_errors(self):
        runtime = load("sync-runtime-names.py", "runtime_names_for_free")
        _, errors = runtime.expected_runtime_names({"free-tool": FREE})
        self.assertEqual(len(errors), 1)
        self.assertIn("no mirrored SKILL.md", errors[0])


class SharedDefinitionTest(unittest.TestCase):
    """Every generated surface must read the same definition, not its own copy."""

    def test_scripts_import_the_shared_helper(self):
        for filename in (
            "sync-skills.py",
            "sync-runtime-names.py",
            "render-marketplace.py",
            "render-readme.py",
        ):
            with self.subTest(script=filename):
                source = (SCRIPTS / filename).read_text(encoding="utf-8")
                self.assertIn("from catalog_entries import", source)
                self.assertNotIn('.get("visibility") == "internal"', source)
                self.assertNotIn('.get("visibility") != "internal"', source)


if __name__ == "__main__":
    unittest.main()
