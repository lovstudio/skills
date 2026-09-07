import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("render_readme", Path(__file__).with_name("render-readme.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class MetadataSyncTest(unittest.TestCase):
    def test_nested_skill_keeps_its_own_description(self):
        nested = {"repo": "lovstudio/skills", "skill_path": "skills/five", "description": "Five why analysis"}
        standalone = {"repo": "lovstudio/standalone", "description": "Old description"}
        with patch.object(module.subprocess, "check_output", return_value='{"description":"Repository description"}') as fetch:
            module.gh_sync([nested, standalone])
        self.assertEqual(nested["description"], "Five why analysis")
        self.assertEqual(standalone["description"], "Repository description")
        fetch.assert_called_once()
        self.assertIn("lovstudio/standalone", fetch.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
