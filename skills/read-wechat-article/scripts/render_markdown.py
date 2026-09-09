#!/usr/bin/env python3
"""Render a fetched WeChat article manifest into an editable Markdown draft."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def markdown_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", " ")


def render_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    paragraphs: List[str] = []
    buffer: List[str] = []
    for line in lines:
        if not line:
            if buffer:
                paragraphs.append(" ".join(buffer))
                buffer = []
            continue
        if line.startswith(("#", "- ", "* ", "1.", "> ")):
            if buffer:
                paragraphs.append(" ".join(buffer))
                buffer = []
            paragraphs.append(line)
        else:
            buffer.append(line)
    if buffer:
        paragraphs.append(" ".join(buffer))
    return "\n\n".join(paragraphs) + "\n"


def render_ocr(records: List[dict], images: List[dict]) -> str:
    image_by_file = {item.get("file"): item for item in images}
    sections: List[str] = []
    for record in records:
        path = str(record.get("file", ""))
        label = Path(path).stem
        index = None
        for item in images:
            if Path(item.get("file", "")).name == Path(path).name:
                index = item.get("index")
                break
        heading = f"### {index}. 图片 {label}"
        lines = [
            item.get("text", "").strip()
            for item in record.get("lines", [])
            if item.get("text")
        ]
        sections.append(heading + "\n\n" + ("\n\n".join(lines) if lines else "（未识别到文字）"))
    return "\n\n".join(sections) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="manifest.json produced by read_wechat_article.py")
    parser.add_argument("--ocr", default="", help="Optional OCR JSON from ocr_images.py")
    parser.add_argument("--output", default="", help="Output Markdown path")
    args = parser.parse_args()

    manifest = load_json(Path(args.manifest))
    title = markdown_escape(manifest.get("title") or "WeChat Article")
    output_dir = Path(args.manifest).expanduser().resolve().parent
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else output_dir / f"{manifest.get('slug') or 'article'}.md"
    )

    parts: List[str] = []
    parts.append("---")
    parts.append(f"title: {title}")
    parts.append(f"source_url: {manifest.get('source_url', '')}")
    parts.append(f"account: {markdown_escape(manifest.get('account') or '')}")
    parts.append(f"publish_time: {markdown_escape(manifest.get('publish_time') or '')}")
    parts.append("---")
    parts.append("")
    parts.append(
        "> 本文件由公众号原文整理为 Markdown。正文文字若来自 OCR，需由使用者逐图核对；"
        "来源、标识符和原文表述不会在整理时被改写。"
    )
    parts.append("")

    text = manifest.get("extracted_text") or ""
    if not manifest.get("image_only") and text.strip():
        parts.append("# 正文")
        parts.append("")
        parts.append(render_text(text))
    else:
        parts.append("# 原始图片")
        parts.append("")
        parts.append(
            "公众号原文以图片形式发布，以下为按出现顺序提取的全部图片："
        )
        parts.append("")
        images = manifest.get("images", [])
        for image in images:
            relative = image.get("file") or ""
            if relative:
                parts.append(f"![第 {image.get('index', '')} 图]({relative})")
                parts.append("")

    if args.ocr:
        ocr_data = load_json(Path(args.ocr))
        records = ocr_data.get("records", [])
        images = manifest.get("images", [])
        if records:
            parts.append("## OCR 识别文本（草稿）")
            parts.append("")
            parts.append(
                "> 这是机器识别草稿，用于辅助整理；请以原图核对后再作为正式正文。"
            )
            parts.append("")
            parts.append(render_ocr(records, images))

    parts.append("---")
    parts.append("")
    parts.append("## 来源与说明")
    parts.append("")
    parts.append(f"- 原始链接：{manifest.get('source_url', '')}")
    parts.append(f"- 公众号：{manifest.get('account') or '未获取'}")
    parts.append(f"- 发布时间：{manifest.get('publish_time') or '未获取'}")
    parts.append("- 原图目录：`images/`")

    output_path.write_text("\n".join(parts), encoding="utf-8")
    print(f"markdown={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
