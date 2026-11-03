#!/usr/bin/env python3
"""Check that a BP deck PPTX is editable.

Every slide must carry native PowerPoint text, and no picture may cover the whole
slide. A deck exported as one screenshot per page fails both checks.
"""

from __future__ import annotations

import argparse
import json
import posixpath
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Dict, List

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
FULL_PAGE_RATIO = 0.9


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fail when a slide has no native text or carries a full-page picture."
    )
    parser.add_argument("pptx", help="Deck to check")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args()


def slide_parts(archive: zipfile.ZipFile, presentation: ET.Element) -> List[str]:
    rels = ET.fromstring(archive.read("ppt/_rels/presentation.xml.rels"))
    targets = {rel.get("Id"): rel.get("Target", "") for rel in rels.iter(f"{{{REL}}}Relationship")}
    parts = []
    # Presentation order lives in sldIdLst; slideN.xml file numbers drift after reordering.
    for slide_id in presentation.iter(f"{{{P}}}sldId"):
        target = targets[slide_id.get(f"{{{R}}}id")]
        parts.append(target.lstrip("/") if target.startswith("/") else posixpath.normpath(f"ppt/{target}"))
    return parts


def inspect(path: Path) -> Dict[str, object]:
    with zipfile.ZipFile(path) as archive:
        presentation = ET.fromstring(archive.read("ppt/presentation.xml"))
        size = presentation.find(f"{{{P}}}sldSz")
        page_area = int(size.get("cx")) * int(size.get("cy"))
        slides = []
        for number, part in enumerate(slide_parts(archive, presentation), start=1):
            root = ET.fromstring(archive.read(part))
            text = "".join(node.text or "" for node in root.iter(f"{{{A}}}t"))
            full_page = 0
            for picture in root.iter(f"{{{P}}}pic"):
                ext = picture.find(f"{{{P}}}spPr/{{{A}}}xfrm/{{{A}}}ext")
                if ext is not None and int(ext.get("cx")) * int(ext.get("cy")) >= FULL_PAGE_RATIO * page_area:
                    full_page += 1
            background = root.find(f"{{{P}}}cSld/{{{P}}}bg")
            if background is not None and background.find(f".//{{{A}}}blip") is not None:
                full_page += 1
            slides.append(
                {
                    "slide": number,
                    "text_chars": sum(1 for char in text if not char.isspace()),
                    "full_page_pictures": full_page,
                }
            )
    failing = [slide["slide"] for slide in slides if not slide["text_chars"] or slide["full_page_pictures"]]
    return {
        "pptx": str(path),
        "slides": len(slides),
        "slides_without_text": sum(1 for slide in slides if not slide["text_chars"]),
        "full_page_pictures": sum(slide["full_page_pictures"] for slide in slides),
        "editable": bool(slides) and not failing,
        "failing_slides": failing,
        "per_slide": slides,
    }


def main() -> int:
    args = parse_args()
    path = Path(args.pptx).expanduser().resolve()
    try:
        result = inspect(path)
    except (OSError, KeyError, ValueError, TypeError, zipfile.BadZipFile, ET.ParseError) as error:
        print(f"error: cannot read {path} as PPTX: {error}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"PPTX: {result['pptx']}")
        print(
            f"Slides: {result['slides']} · without native text: {result['slides_without_text']}"
            f" · full-page pictures: {result['full_page_pictures']}"
        )
        for slide in result["per_slide"]:
            if slide["slide"] in result["failing_slides"]:
                print(
                    f"- slide {slide['slide']}: {slide['text_chars']} native text characters,"
                    f" {slide['full_page_pictures']} full-page picture(s)"
                )
        print(f"Editable: {'yes' if result['editable'] else 'no'}")
    return 0 if result["editable"] else 1


if __name__ == "__main__":
    sys.exit(main())
