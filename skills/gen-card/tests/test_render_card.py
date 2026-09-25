from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_card.py"
CASE = ROOT / "cases" / "bauhaus-card.json"


class RenderCardTests(unittest.TestCase):
    def test_html_is_self_contained_and_actionable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(CASE), "--out", directory, "--format", "html"],
                capture_output=True,
                text=True,
                check=True,
            )
            output = Path(directory).resolve() / "bauhaus.html"
            self.assertIn(f"html={output}", result.stdout)
            page = output.read_text(encoding="utf-8")
            self.assertIn("data:image/jpeg;base64,", page)
            self.assertIn("复制 Prompt", page)
            self.assertIn("下载 PNG", page)
            self.assertIn("modernScreenshot", page)
            self.assertNotIn("@@TITLE@@", page)

    def test_invalid_rating_is_rejected(self) -> None:
        card = json.loads(CASE.read_text(encoding="utf-8"))
        card["ratings"][0]["score"] = 6
        card["visual"]["path"] = str((ROOT / "cases" / "assets" / "bauhaus-visual.jpg").resolve())
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "invalid.json"
            source.write_text(json.dumps(card, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(source), "--validate-only"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("must be an integer from 1 to 5", result.stderr)

    def test_five_ratings_use_multi_rating_layout(self) -> None:
        card = json.loads(CASE.read_text(encoding="utf-8"))
        card["ratings"] = [
            {"label": f"维度 {index}", "score": index}
            for index in range(1, 6)
        ]
        card["visual"]["path"] = str((ROOT / "cases" / "assets" / "bauhaus-visual.jpg").resolve())
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "five-ratings.json"
            source.write_text(json.dumps(card, ensure_ascii=False), encoding="utf-8")
            subprocess.run(
                [sys.executable, str(SCRIPT), str(source), "--out", directory, "--format", "html"],
                capture_output=True,
                text=True,
                check=True,
            )
            page = (Path(directory) / "bauhaus.html").read_text(encoding="utf-8")
            self.assertIn('class="basic-info is-multi-rating"', page)
            self.assertEqual(page.count('class="info-item rating"'), 5)


if __name__ == "__main__":
    unittest.main()
