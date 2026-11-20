from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEMVER = r"\d+\.\d+\.\d+"


def skill_version(skill_dir: Path) -> str:
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = text[4 : text.index("\n---\n", 4)]
    match = re.search(rf'(?m)^[ \t]+version:[ \t]*["\']?({SEMVER})["\']?[ \t]*$', frontmatter)
    return match.group(1)


class KitVersionSurfaceTests(unittest.TestCase):
    # The version bump tool moves SKILL.md, the README badge and skill.yaml only.
    # kit.yaml stayed at 0.2.1 from 0.3.0 to 0.3.5.

    def test_kit_manifest_carries_the_lov_bp_version(self) -> None:
        kit = (ROOT / "kit.yaml").read_text(encoding="utf-8")
        match = re.search(rf'(?m)^version:[ \t]*["\']?({SEMVER})["\']?[ \t]*$', kit)
        self.assertEqual(match.group(1), skill_version(ROOT))


if __name__ == "__main__":
    unittest.main()
