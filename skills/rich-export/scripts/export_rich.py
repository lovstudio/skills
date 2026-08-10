#!/usr/bin/env python3
"""Export one Markdown/HTML/manifest source into user-facing delivery formats."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALL_FORMATS = ("html-single", "html-dir", "md", "docx", "pdf")
VIDEO_RE = re.compile(r"<video\b(?P<attrs>[^>]*)>(?P<body>.*?)</video\s*>", re.I | re.S)
AUDIO_RE = re.compile(r"<audio\b(?P<attrs>[^>]*)>(?P<body>.*?)</audio\s*>", re.I | re.S)
IFRAME_RE = re.compile(r"<iframe\b(?P<attrs>[^>]*)>(?P<body>.*?)</iframe\s*>", re.I | re.S)
ATTR_RE = re.compile(r'''([:\w-]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+))''')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export Markdown, HTML, or rich-export.json to web and document formats."
    )
    parser.add_argument("--input", type=Path, help=".md, .html, or rich-export.json input")
    parser.add_argument("--out", type=Path, help="Output directory")
    parser.add_argument(
        "--formats", default=",".join(ALL_FORMATS),
        help="Comma-separated: " + ", ".join(ALL_FORMATS),
    )
    parser.add_argument("--zip", action="store_true", help="Create a ZIP of all generated files")
    parser.add_argument("--docx-reference", type=Path, help="Optional Pandoc reference.docx")
    parser.add_argument("--pdf-format", default="A4", help="PDF paper format, default A4")
    parser.add_argument("--title", help="Override document title")
    parser.add_argument("--self-test", action="store_true", help="Run a local Markdown → HTML/DOCX smoke test")
    return parser.parse_args()


def attrs(raw: str) -> dict[str, str]:
    return {
        key.lower(): next(value for value in values if value is not None)
        for key, *values in ATTR_RE.findall(raw)
    }


def clean_name(value: str) -> str:
    normalized = re.sub(r"[^\w._-]+", "-", value.strip(), flags=re.UNICODE)
    return normalized.strip(".-") or "document"


def title_from_markdown(markdown: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+?)\s*$", markdown, re.M)
    return re.sub(r"[*`_]", "", match.group(1)).strip() if match else fallback


def run(command: list[str], *, cwd: Path | None = None) -> None:
    process = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if process.returncode:
        detail = process.stderr.strip() or process.stdout.strip() or "未知错误"
        raise RuntimeError(f"命令失败：{' '.join(command[:2])}…\n{detail}")


def require_pandoc() -> str:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError("未找到 Pandoc。请安装 Pandoc 3.x 后重试。")
    return pandoc


def media_html(item: dict[str, Any]) -> str:
    kind = str(item.get("kind", ""))
    source = html.escape(str(item["src"]), quote=True)
    title = html.escape(str(item.get("title", "")))
    caption = html.escape(str(item.get("caption", "")))
    transcript = item.get("transcript_url")
    if kind == "image":
        body = f'<img src="{source}" alt="{title}">'
    elif kind == "video":
        poster = item.get("poster")
        poster_attr = f' poster="{html.escape(str(poster), quote=True)}"' if poster else ""
        body = f'<video controls src="{source}"{poster_attr}>{title}</video>'
    elif kind == "audio":
        body = f'<audio controls src="{source}">{title}</audio>'
    elif kind == "iframe":
        body = f'<iframe src="{source}" title="{title}" loading="lazy"></iframe>'
    else:
        raise ValueError(f"不支持的媒体 kind：{kind}")
    extras = f"<figcaption>{caption}</figcaption>" if caption else ""
    if transcript:
        extras += f' <a href="{html.escape(str(transcript), quote=True)}">文字稿</a>'
    return f"<figure>{body}{extras}</figure>"


def source_from_manifest(path: Path) -> tuple[str, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != 1 or not isinstance(data.get("content"), dict):
        raise ValueError("rich-export.json 必须包含 version: 1 与 content 对象。")
    content = data["content"].get("markdown")
    if not isinstance(content, str):
        raise ValueError("当前版本要求 content.markdown 为字符串。")
    media = {str(item.get("id")): item for item in data.get("media", []) if isinstance(item, dict)}

    def replace(match: re.Match[str]) -> str:
        media_id = match.group(1)
        if media_id not in media:
            raise ValueError(f"正文引用了不存在的媒体：{media_id}")
        return media_html(media[media_id])

    return re.sub(r"\{\{media:([A-Za-z0-9_.-]+)\}\}", replace, content), data


def normalize_source(path: Path, pandoc: str) -> tuple[str, dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return source_from_manifest(path)
    if suffix in {".md", ".markdown", ".mdown"}:
        return path.read_text(encoding="utf-8"), {}
    if suffix in {".html", ".htm"}:
        process = subprocess.run(
            [pandoc, "--from=html", "--to=gfm", str(path)], text=True, capture_output=True
        )
        if process.returncode:
            raise RuntimeError(process.stderr.strip() or "HTML 转 Markdown 失败")
        return process.stdout, {}
    raise ValueError("输入只支持 .md、.html 或 rich-export.json。")


def markdown_for_static_output(markdown: str) -> tuple[str, list[str]]:
    warnings: list[str] = []

    def project(kind: str, match: re.Match[str]) -> str:
        data = attrs(match.group("attrs"))
        source = data.get("src", "")
        title = data.get("title") or ("视频" if kind == "video" else "音频" if kind == "audio" else "嵌入内容")
        poster = data.get("poster")
        lines: list[str] = [""]
        if poster:
            lines.append(f"![{title}封面]({poster})")
        lines.append(f"**{title}**")
        if source:
            label = "观看视频" if kind == "video" else "收听音频" if kind == "audio" else "打开交互内容"
            lines.append(f"[{label}]({source})")
        else:
            warnings.append(f"{kind} 缺少 src，静态导出仅保留说明。")
        return "\n\n".join(lines) + "\n"

    result = VIDEO_RE.sub(lambda match: project("video", match), markdown)
    result = AUDIO_RE.sub(lambda match: project("audio", match), result)
    result = IFRAME_RE.sub(lambda match: project("iframe", match), result)
    return result, warnings


def pandoc_html(pandoc: str, source: Path, output: Path, resource_root: Path, *, embedded: bool, title: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        pandoc, str(source), "--from=markdown+raw_html", "--to=html5", "--standalone",
        f"--resource-path={resource_root}", f"--metadata=title:{title}", "--output", str(output),
    ]
    if embedded:
        command.insert(-2, "--embed-resources")
    else:
        assets = output.parent / "assets"
        command.insert(-2, f"--extract-media={assets}")
    run(command)


def pandoc_docx(pandoc: str, source: Path, output: Path, resource_root: Path, title: str, reference: Path | None) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        pandoc, str(source), "--from=markdown+raw_html", "--to=docx",
        f"--resource-path={resource_root}", f"--metadata=title:{title}", "--output", str(output),
    ]
    if reference:
        command.extend(["--reference-doc", str(reference)])
    run(command)


def render_pdf(html_path: Path, output: Path, paper: str) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("PDF 需要 Playwright：python3 -m pip install playwright && playwright install chromium") from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as browser_api:
        browser = browser_api.chromium.launch()
        page = browser.new_page()
        page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
        page.emulate_media(media="print")
        page.pdf(path=str(output), format=paper, print_background=True, prefer_css_page_size=True)
        browser.close()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def make_zip(output_root: Path, bundle_name: str) -> Path:
    zip_path = output_root / f"{bundle_name}-export.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in output_root.rglob("*"):
            if file_path.is_file() and file_path != zip_path:
                archive.write(file_path, file_path.relative_to(output_root))
    return zip_path


def export(args: argparse.Namespace) -> list[Path]:
    if not args.input or not args.out:
        raise ValueError("--input 和 --out 为必填参数。")
    formats = tuple(item.strip() for item in args.formats.split(",") if item.strip())
    unknown = sorted(set(formats) - set(ALL_FORMATS))
    if unknown:
        raise ValueError("不支持的格式：" + ", ".join(unknown))
    pandoc = require_pandoc()
    input_path = args.input.resolve()
    output_root = args.out.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    markdown, document = normalize_source(input_path, pandoc)
    title = args.title or str(document.get("document", {}).get("title") or title_from_markdown(markdown, input_path.stem))
    bundle_name = clean_name(title)
    source_path = output_root / "source.md"
    source_path.write_text(markdown, encoding="utf-8")
    static_markdown, warnings = markdown_for_static_output(markdown)
    static_path = output_root / ".static.md"
    static_path.write_text(static_markdown, encoding="utf-8")
    generated: list[Path] = [source_path]
    resource_root = input_path.parent

    if "md" in formats:
        markdown_path = output_root / "markdown" / f"{bundle_name}.md"
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(static_markdown, encoding="utf-8")
        generated.append(markdown_path)
    if "html-single" in formats:
        single_path = output_root / "html-single" / f"{bundle_name}.html"
        pandoc_html(pandoc, source_path, single_path, resource_root, embedded=True, title=title)
        generated.append(single_path)
    if "html-dir" in formats:
        folder_path = output_root / "html" / bundle_name / "index.html"
        pandoc_html(pandoc, source_path, folder_path, resource_root, embedded=False, title=title)
        generated.append(folder_path)
    if "docx" in formats:
        docx_path = output_root / "docx" / f"{bundle_name}.docx"
        pandoc_docx(pandoc, static_path, docx_path, resource_root, title, args.docx_reference)
        generated.append(docx_path)
    if "pdf" in formats:
        pdf_html = output_root / ".pdf-source.html"
        pandoc_html(pandoc, static_path, pdf_html, resource_root, embedded=True, title=title)
        pdf_path = output_root / "pdf" / f"{bundle_name}.pdf"
        render_pdf(pdf_html, pdf_path, args.pdf_format)
        generated.append(pdf_path)

    static_path.unlink(missing_ok=True)
    (output_root / ".pdf-source.html").unlink(missing_ok=True)
    manifest = {
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "title": title,
        "source": {"path": str(input_path), "sha256": sha256(input_path)},
        "formats": list(formats),
        "media_policy": "interactive-html-static-projection-for-md-docx-pdf",
        "files": [str(path.relative_to(output_root)) for path in generated],
        "warnings": warnings,
    }
    manifest_path = output_root / "export-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    generated.append(manifest_path)
    if args.zip:
        generated.append(make_zip(output_root, bundle_name))
    return generated


def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="lov-rich-export-") as temporary:
        root = Path(temporary)
        source = root / "sample.md"
        source.write_text("# 验收样稿\n\n你好，世界。\n\n<video controls src=\"demo.mp4\">演示</video>\n", encoding="utf-8")
        args = argparse.Namespace(
            input=source, out=root / "out", formats="html-single,html-dir,md,docx,pdf", zip=True,
            docx_reference=None, pdf_format="A4", title=None,
        )
        exported = export(args)
        required = {"source.md", "验收样稿.html", "验收样稿.docx", "验收样稿.pdf", "export-manifest.json", "验收样稿-export.zip"}
        names = {path.name for path in exported}
        missing = required - names
        if missing:
            raise RuntimeError("自检缺少：" + ", ".join(sorted(missing)) + "；实际：" + ", ".join(sorted(names)))
        manifest = root / "rich-export.json"
        manifest.write_text(json.dumps({
            "version": 1,
            "document": {"title": "媒体样稿", "lang": "zh-CN"},
            "content": {"markdown": "# 媒体样稿\n\n{{media:demo}}"},
            "media": [{"id": "demo", "kind": "video", "src": "demo.mp4", "title": "产品演示"}],
        }, ensure_ascii=False), encoding="utf-8")
        manifest_args = argparse.Namespace(
            input=manifest, out=root / "manifest-out", formats="html-single,md", zip=False,
            docx_reference=None, pdf_format="A4", title=None,
        )
        manifest_files = export(manifest_args)
        static_markdown = (root / "manifest-out" / "markdown" / "媒体样稿.md").read_text(encoding="utf-8")
        single_html = next(path for path in manifest_files if path.suffix == ".html").read_text(encoding="utf-8")
        if "观看视频" not in static_markdown or "<video" not in single_html:
            raise RuntimeError("rich-export.json 未正确保留 HTML 交互或静态媒体投影。")
    print("PASS: Markdown → HTML single / HTML directory / Markdown / DOCX / PDF / ZIP")


def main() -> int:
    args = parse_args()
    try:
        if args.self_test:
            self_test()
            return 0
        for path in export(args):
            print(path)
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"导出失败：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
