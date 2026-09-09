#!/usr/bin/env python3
"""OCR article images with macOS Vision, falling back to Tesseract when available."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from json import JSONDecoder
from pathlib import Path
from typing import Dict, List


def images_in(directory: Path) -> List[Path]:
    return sorted(
        path
        for path in directory.rglob("*")
        if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
    )


def parse_json_records(text: str) -> List[Dict[str, object]]:
    decoder = JSONDecoder()
    records: List[Dict[str, object]] = []
    pos = 0
    while pos < len(text):
        while pos < len(text) and text[pos].isspace():
            pos += 1
        if pos >= len(text):
            break
        try:
            value, pos = decoder.raw_decode(text, pos)
        except json.JSONDecodeError:
            break
        if isinstance(value, dict):
            records.append(value)
    return records


def run_vision(script: Path, image_paths: List[Path]) -> List[Dict[str, object]]:
    command = ["swift", str(script), *[str(path) for path in image_paths]]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Swift OCR failed")
    return parse_json_records(result.stdout)


def run_tesseract(image_paths: List[Path]) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []
    for path in image_paths:
        result = subprocess.run(
            ["tesseract", str(path), "stdout", "-l", "chi_sim+eng", "--psm", "6"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"Tesseract failed for {path}")
        lines = [
            {"text": line.strip(), "x": 0.0, "y": 0.0, "w": 0.0, "h": 0.0, "conf": 1.0}
            for line in result.stdout.splitlines()
            if line.strip()
        ]
        records.append({"file": str(path), "lines": lines})
    return records


def tesseract_languages() -> set:
    if not shutil.which("tesseract"):
        return set()
    try:
        result = subprocess.run(
            ["tesseract", "--list-langs"], capture_output=True, text=True
        )
        return set(result.stdout.splitlines())
    except Exception:
        return set()


def doctor() -> int:
    print(json.dumps({
        "macos_vision": shutil.which("swift") is not None,
        "tesseract": shutil.which("tesseract") is not None,
        "tesseract_chinese": "chi_sim" in tesseract_languages(),
    }, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="*", help="Image files; or --image-dir")
    parser.add_argument("--image-dir", default="", help="Directory containing images")
    parser.add_argument("--output", default="", help="Write OCR JSON to this path")
    parser.add_argument("--doctor", action="store_true", help="Check OCR runtime")
    args = parser.parse_args()

    if args.doctor:
        return doctor()

    if args.image_dir:
        image_paths = images_in(Path(args.image_dir))
    else:
        image_paths = [Path(item) for item in args.images]
    if not image_paths:
        print("ERROR: no image files found", file=sys.stderr)
        return 2

    script = Path(__file__).resolve().parent / "vision_ocr.swift"
    records: List[Dict[str, object]]
    if shutil.which("swift"):
        records = run_vision(script, image_paths)
    elif shutil.which("tesseract"):
        records = run_tesseract(image_paths)
    else:
        print(
            "ERROR: no OCR runtime. Install Xcode Command Line Tools or tesseract "
            "with chi_sim, then run an agent-visible image review.",
            file=sys.stderr,
        )
        return 3

    payload = {
        "schema": "wechat-article-ocr/v1",
        "engine": "macos-vision" if shutil.which("swift") else "tesseract",
        "records": records,
    }
    output_text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).expanduser().write_text(output_text, encoding="utf-8")
        print(json.dumps({
            "engine": payload["engine"],
            "records": len(records),
            "output": str(Path(args.output).expanduser().resolve()),
        }, ensure_ascii=False, indent=2))
    else:
        print(output_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
