from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "skills" / "bp-deck" / "scripts" / "check_pptx_editable.py"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WIDE = (12192000, 6858000)


def picture(cx: int, cy: int) -> str:
    return (
        f'<p:pic><p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        "</p:spPr></p:pic>"
    )


def text_box(text: str) -> str:
    return f"<p:sp><p:txBody><a:p><a:r><a:t>{text}</a:t></a:r></a:p></p:txBody></p:sp>"


def write_deck(path: Path, slides: list) -> None:
    ids = "".join(f'<p:sldId id="{256 + i}" r:id="rId{i + 1}"/>' for i in range(len(slides)))
    rels = "".join(
        f'<Relationship Id="rId{i + 1}" Type="{R}/slide" Target="slides/slide{i + 1}.xml"/>'
        for i in range(len(slides))
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "ppt/presentation.xml",
            f'<p:presentation xmlns:p="{P}" xmlns:r="{R}"><p:sldIdLst>{ids}</p:sldIdLst>'
            f'<p:sldSz cx="{WIDE[0]}" cy="{WIDE[1]}"/></p:presentation>',
        )
        archive.writestr(
            "ppt/_rels/presentation.xml.rels",
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f"{rels}</Relationships>",
        )
        for i, body in enumerate(slides, start=1):
            archive.writestr(
                f"ppt/slides/slide{i}.xml",
                f'<p:sld xmlns:p="{P}" xmlns:a="{A}"><p:cSld><p:spTree>{body}</p:spTree></p:cSld></p:sld>',
            )


def check(slides: list) -> tuple:
    with tempfile.TemporaryDirectory() as tmp:
        deck = Path(tmp) / "deck.pptx"
        write_deck(deck, slides)
        result = subprocess.run(
            [sys.executable, str(CHECK), str(deck), "--format", "json"],
            capture_output=True,
            text=True,
        )
    return result.returncode, json.loads(result.stdout)


class EditablePptxTests(unittest.TestCase):
    def test_native_text_with_small_pictures_passes(self) -> None:
        code, result = check([text_box("投资亮点") + picture(900000, 400000), text_box("团队")])
        self.assertEqual(code, 0)
        self.assertTrue(result["editable"])

    def test_one_picture_per_page_fails(self) -> None:
        # v0.1–v0.4 shipped this shape: every slide is a single full-page picture.
        code, result = check([text_box("封面"), picture(*WIDE)])
        self.assertEqual(code, 1)
        self.assertEqual(result["failing_slides"], [2])
        self.assertEqual(result["slides_without_text"], 1)
        self.assertEqual(result["full_page_pictures"], 1)

    def test_full_page_picture_under_native_text_still_fails(self) -> None:
        code, result = check([picture(*WIDE) + text_box("可搜索的文字层")])
        self.assertEqual(code, 1)
        self.assertEqual(result["full_page_pictures"], 1)


if __name__ == "__main__":
    unittest.main()
