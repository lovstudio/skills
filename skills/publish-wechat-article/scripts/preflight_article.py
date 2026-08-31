#!/usr/bin/env python3
"""Validate a WeChat Official Account article before choosing a transport."""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlparse

from PIL import Image

from publication_artifacts import ArtifactContractError, validate_cover_composition_receipt
from editorial_components import EditorialComponentError, validate_editorial_components


MIB = 1024 * 1024
SUPPORTED_COVER_SUFFIXES = {".bmp", ".gif", ".jpeg", ".jpg", ".png"}
SUPPORTED_BODY_SUFFIXES = {".jpeg", ".jpg", ".png"}
MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
MARKDOWN_H1_RE = re.compile(r"^\s*#\s+(.+?)\s*$", re.MULTILINE)
MARKDOWN_REFERENCE_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\[([^\]]*)\]")
MARKDOWN_SHORTCUT_IMAGE_RE = re.compile(r"!\[([^\]]+)\](?!\s*[\[(])")
MARKDOWN_REFERENCE_DEFINITION_RE = re.compile(
    r"^[ \t]{0,3}\[([^\]]+)\]:[ \t]*(?:<([^>\n]+)>|(\S+))",
    re.MULTILINE,
)
BENCHMARK_REQUIRED_SECTIONS = [
    "测试方法",
    "Prompt",
    "评价指标",
    "评分方法",
    "评分示例",
    "复现方法",
    "测试结果",
    "局限性",
]


@dataclass(frozen=True)
class ImageReference:
    source: str
    kind: str
    path: Path | None

    def as_dict(self) -> dict[str, object]:
        result: dict[str, object] = {"source": self.source, "kind": self.kind}
        if self.path is not None:
            result["path"] = str(self.path)
            result["exists"] = self.path.is_file()
            if self.path.is_file():
                result["bytes"] = self.path.stat().st_size
        return result


class ArticleHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.images: list[str] = []
        self._capture: str | None = None
        self._parts: dict[str, list[str]] = {"h1": [], "title": []}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if lowered in self._parts and not self._parts[lowered]:
            self._capture = lowered
        if lowered == "img":
            source = dict(attrs).get("src")
            if source:
                self.images.append(source.strip())

    def handle_endtag(self, tag: str) -> None:
        if self._capture == tag.lower():
            self._capture = None

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._parts[self._capture].append(data)

    def inferred_title(self) -> tuple[str | None, str | None]:
        for key in ("h1", "title"):
            value = "".join(self._parts[key]).strip()
            if value:
                return value, f"html_{key}"
        return None, None


def _clean_markdown_title(value: str) -> str:
    return re.sub(r"[`*_]", "", value).strip()


def infer_title(source: Path, content: str, explicit: str | None) -> tuple[str, str]:
    if explicit and explicit.strip():
        return explicit.strip(), "explicit"

    suffix = source.suffix.lower()
    if suffix in {".md", ".markdown", ".mdown"}:
        match = MARKDOWN_H1_RE.search(content)
        if match:
            return _clean_markdown_title(match.group(1)), "markdown_h1"
    elif suffix in {".html", ".htm"}:
        parser = ArticleHTMLParser()
        parser.feed(content)
        inferred, origin = parser.inferred_title()
        if inferred and origin:
            return inferred, origin

    first_line = next((line.strip() for line in content.splitlines() if line.strip()), "")
    return first_line, "first_nonempty_line" if first_line else "missing"


def _markdown_target(raw: str) -> str:
    value = raw.strip()
    if value.startswith("<") and ">" in value:
        return value[1:value.index(">")].strip()
    quoted = re.match(r"(.+?)\s+(['\"]).*\2\s*$", value)
    return (quoted.group(1) if quoted else value).strip()


def _classify_image(source: str, base_dir: Path) -> ImageReference:
    normalized = source.strip()
    parsed = urlparse(normalized)
    if parsed.scheme in {"http", "https", "data"} or normalized.startswith("//"):
        return ImageReference(normalized, "remote", None)
    if parsed.scheme == "file":
        return ImageReference(normalized, "local", Path(unquote(parsed.path)).resolve())
    local = Path(unquote(normalized))
    if not local.is_absolute():
        local = base_dir / local
    return ImageReference(normalized, "local", local.resolve())


def _reference_label(value: str) -> str:
    return " ".join(value.split()).casefold()


def _markdown_reference_images(content: str) -> list[str]:
    definitions = {
        _reference_label(match.group(1)): match.group(2) or match.group(3)
        for match in MARKDOWN_REFERENCE_DEFINITION_RE.finditer(content)
    }
    sources: list[str] = []
    for match in MARKDOWN_REFERENCE_IMAGE_RE.finditer(content):
        label = match.group(2) or match.group(1)
        target = definitions.get(_reference_label(label))
        if target:
            sources.append(target)
    for match in MARKDOWN_SHORTCUT_IMAGE_RE.finditer(content):
        target = definitions.get(_reference_label(match.group(1)))
        if target:
            sources.append(target)
    return sources


def find_images(source: Path, content: str) -> list[ImageReference]:
    raw_sources: list[str] = []
    if source.suffix.lower() in {".html", ".htm"}:
        parser = ArticleHTMLParser()
        parser.feed(content)
        raw_sources.extend(parser.images)
    else:
        raw_sources.extend(_markdown_target(match.group(1)) for match in MARKDOWN_IMAGE_RE.finditer(content))
        raw_sources.extend(_markdown_reference_images(content))
        parser = ArticleHTMLParser()
        parser.feed(content)
        raw_sources.extend(parser.images)

    seen: set[str] = set()
    references: list[ImageReference] = []
    for raw in raw_sources:
        if not raw or raw in seen:
            continue
        seen.add(raw)
        references.append(_classify_image(raw, source.parent))
    return references


def _benchmark_reproducibility_errors(content: str, title: str) -> list[str]:
    quantified_claim = bool(re.search(r"排名|排行榜|第一名|总分|雷达图", content)) and bool(
        re.search(r"评分|得分|分数|权重", content)
    )
    is_benchmark = (
        bool(re.search(r"调研|评测|benchmark", title, re.IGNORECASE))
        or ("## 测试方法" in content and "## 测试结果" in content)
        or quantified_claim
    )
    if not is_benchmark:
        return []
    headings = [match.group(1).strip() for match in re.finditer(r"(?m)^##\s+(.+?)\s*$", content)]
    missing = [heading for heading in BENCHMARK_REQUIRED_SECTIONS if heading not in headings]
    errors = [f"研究评测文章缺少“{heading}”章节。" for heading in missing]
    if missing:
        return errors
    positions = [headings.index(heading) for heading in BENCHMARK_REQUIRED_SECTIONS]
    if positions != sorted(positions):
        errors.append("研究评测文章必须先公开方法、Prompt、评分与复现，再展示测试结果和局限性。")
    prompt_match = re.search(r"(?ms)^##\s+Prompt\s*$\n(.*?)(?=^##\s+)", content)
    prompt_body = prompt_match.group(1) if prompt_match else ""
    fenced_prompts = re.findall(r"```[^\n]*\n(.*?)```", prompt_body, re.DOTALL)
    if not any(len(re.sub(r"\s+", " ", block).strip()) >= 40 for block in fenced_prompts):
        errors.append("研究评测文章的 Prompt 章节必须公开至少一份实质性的实际执行文本。")
    return errors


def _first_markdown_body_image(content: str, base_dir: Path) -> ImageReference | None:
    lines = content.splitlines()
    index = 0
    if lines and lines[0].strip() == "---":
        index = 1
        while index < len(lines) and lines[index].strip() != "---":
            index += 1
        index += 1
    while index < len(lines) and not re.match(r"^#\s+\S", lines[index].strip()):
        if lines[index].strip():
            return None
        index += 1
    if index < len(lines):
        index += 1
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index >= len(lines):
        return None
    line = lines[index].strip()
    match = MARKDOWN_IMAGE_RE.fullmatch(line)
    if match:
        return _classify_image(_markdown_target(match.group(1)), base_dir)
    html_match = re.fullmatch(r"<img\b[^>]*\bsrc=['\"]([^'\"]+)['\"][^>]*>", line, re.IGNORECASE)
    if html_match:
        return _classify_image(html_match.group(1), base_dir)
    return None


def _body_hero_errors(source: Path, content: str, cover: Path) -> tuple[list[str], dict[str, object]]:
    if source.suffix.lower() not in {".md", ".markdown", ".mdown"}:
        return ["常规发布的 canonical source 必须是 Markdown，才能验收正文第一块 4:3 首图。"], {}
    hero = _first_markdown_body_image(content, source.parent)
    if hero is None:
        return ["正文第一块必须是独立的 4:3 横向首图，并位于导语之前。"], {}
    info: dict[str, object] = {"source": hero.source, "kind": hero.kind}
    if hero.kind != "local" or hero.path is None:
        return ["发布前的 4:3 正文首图必须是可回读尺寸的本地 JPG 或 PNG。"], info
    info["path"] = str(hero.path)
    if not hero.path.is_file():
        return [f"正文首图不存在：{hero.source}"], info
    if hero.path.resolve() == cover.resolve():
        return ["正文首图与分享封面必须是两个独立文件，不能复用同一成品。"], info
    try:
        with Image.open(hero.path) as image:
            width, height = image.size
    except (OSError, ValueError) as error:
        return [f"无法读取正文首图尺寸：{error}"], info
    info.update(
        {
            "width": width,
            "height": height,
            "ratio": round(width / height, 4),
            "distinctFromShareCover": True,
        }
    )
    if abs(width / height - 4 / 3) > 0.01:
        return [f"正文首图必须为 4:3 横向比例；当前为 {width}×{height}。"], info
    return [], info


def _append_length_error(
    errors: list[str],
    name: str,
    value: str | None,
    maximum: int,
) -> None:
    if value and len(value.strip()) > maximum:
        errors.append(f"{name}为 {len(value.strip())} 字，平台上限为 {maximum} 字。")


def analyze_article(
    source: Path,
    cover: Path,
    *,
    title: str | None = None,
    author: str | None = None,
    digest: str | None = None,
    source_url: str | None = None,
    transport: str = "auto",
    lovpen_wechat_html: Path | None = None,
    cover_composition_receipt: Path | None = None,
    require_lovpen: bool = False,
    require_composed_cover: bool = False,
    require_body_hero: bool = False,
    brand_profile: Path | None = None,
) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []

    source = source.expanduser().resolve()
    cover = cover.expanduser().resolve()
    if not source.is_file():
        return {
            "ok": False,
            "errors": [f"正文文件不存在：{source}"],
            "warnings": [],
            "source": str(source),
            "cover": str(cover),
            "transport": transport,
        }

    try:
        content = source.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return {
            "ok": False,
            "errors": ["正文需使用 UTF-8 编码。"],
            "warnings": [],
            "source": str(source),
            "cover": str(cover),
            "transport": transport,
        }
    except OSError as error:
        return {
            "ok": False,
            "errors": [f"读取正文文件失败：{error}"],
            "warnings": [],
            "source": str(source),
            "cover": str(cover),
            "transport": transport,
        }

    inferred_title, title_origin = infer_title(source, content, title)
    if not inferred_title:
        errors.append("未找到文章标题，请通过 --title 提供。")
    elif len(inferred_title) > 32:
        errors.append(f"标题为 {len(inferred_title)} 字，平台上限为 32 字。")
    if source.suffix.lower() in {".md", ".markdown", ".mdown"}:
        errors.extend(_benchmark_reproducibility_errors(content, inferred_title))

    _append_length_error(errors, "作者", author, 16)
    _append_length_error(errors, "摘要", digest, 120)
    if source_url and len(source_url.encode("utf-8")) >= 1024:
        errors.append("阅读原文 URL 需小于 1 KiB。")

    content_chars = len(content)
    content_bytes = len(content.encode("utf-8"))
    if not content.strip():
        errors.append("正文为空。")
    if content_chars >= 20_000:
        warnings.append(
            f"源文件为 {content_chars} 字符；微信的 20,000 字符限制不按原始 HTML/Markdown 计数，"
            "发布脚本会在渲染后按可见正文复核。"
        )
    if content_bytes >= MIB:
        warnings.append(
            f"源文件为 {content_bytes} 字节；发布脚本会在渲染后按最终 UTF-8 HTML 复核 1M 上限。"
        )

    cover_info: dict[str, object] = {"path": str(cover)}
    if not cover.is_file():
        errors.append(f"封面文件不存在：{cover}")
    else:
        cover_bytes = cover.stat().st_size
        cover_info.update({
            "bytes": cover_bytes,
            "mime": mimetypes.guess_type(cover.name)[0],
            "suffix": cover.suffix.lower(),
        })
        if cover.suffix.lower() not in SUPPORTED_COVER_SUFFIXES:
            errors.append("封面格式需为 JPG、PNG、GIF 或 BMP。")
        if cover_bytes > 10 * MIB:
            errors.append(f"封面为 {cover_bytes} 字节，平台上限为 10 MiB。")

    cover_composition: dict[str, object] = {"coverCompositionVerified": False}
    if cover_composition_receipt:
        try:
            cover_composition = validate_cover_composition_receipt(
                cover_composition_receipt,
                cover,
            )
        except ArtifactContractError as error:
            errors.append(str(error))
    elif require_composed_cover:
        errors.append(
            "常规草稿创建必须提供 --cover-composition-receipt；"
            "先用 lov-wechat-branding-cover-composition 生成最终分享封面。"
        )

    lovpen_info: dict[str, object] = {"lovpenArtifactVerified": False}
    if lovpen_wechat_html:
        artifact = lovpen_wechat_html.expanduser().resolve()
        if not artifact.is_file():
            errors.append(f"Lovpen 微信复制态 HTML 不存在：{artifact}")
        else:
            lovpen_info = {
                "lovpenArtifactVerified": True,
                "lovpenArtifact": str(artifact),
                "lovpenArtifactBytes": artifact.stat().st_size,
            }
    elif require_lovpen:
        errors.append(
            "常规草稿创建必须提供 --lovpen-wechat-html；"
            "先用 lovpen-cli render --format wechat 生成微信复制态 HTML。"
        )

    images = find_images(source, content)
    local_images = [image for image in images if image.kind == "local"]
    remote_images = [image for image in images if image.kind == "remote"]

    for image in local_images:
        if image.path is None or not image.path.is_file():
            errors.append(f"正文图片不存在：{image.source}")
            continue
        if image.path.suffix.lower() not in SUPPORTED_BODY_SUFFIXES:
            errors.append(f"正文图片需转为 JPG 或 PNG：{image.path}")
        if image.path.stat().st_size >= MIB:
            errors.append(f"正文图片需小于 1 MiB：{image.path}")

    if transport == "oneshot" and images:
        errors.append("OneShot 当前文章 transport 只上传封面；正文含图片时请选择 gateway 或 browser transport。")
    elif transport == "auto" and images:
        warnings.append("正文含图片；自动路由应选择统一网关，由服务端执行 media/uploadimg 并重写 URL。")

    if remote_images:
        warnings.append("正文含远程图片；微信会过滤外部图片 URL，发布前需下载并经 media/uploadimg 重写。")

    body_hero_info: dict[str, object] = {"bodyHeroVerified": False}
    if require_body_hero:
        body_hero_errors, hero = _body_hero_errors(source, content, cover)
        errors.extend(body_hero_errors)
        body_hero_info = {
            "bodyHeroVerified": not body_hero_errors,
            "bodyHero": hero,
        }

    publication_components: dict[str, object] = {"publicationComponentsVerified": False}
    if brand_profile:
        try:
            publication_components = validate_editorial_components(
                source,
                content,
                brand_profile,
            )
        except EditorialComponentError as error:
            errors.append(str(error))

    if source.suffix.lower() not in {".md", ".markdown", ".mdown", ".html", ".htm", ".txt"}:
        warnings.append("正文扩展名不常见；确认 transport 会把它作为 UTF-8 文本处理。")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "source": str(source),
        "sourceFormat": source.suffix.lower().lstrip(".") or "text",
        "title": inferred_title,
        "titleOrigin": title_origin,
        "author": author.strip() if author else None,
        "digest": digest.strip() if digest else None,
        "sourceUrl": source_url.strip() if source_url else None,
        "contentChars": content_chars,
        "contentBytes": content_bytes,
        "cover": cover_info,
        **cover_composition,
        **lovpen_info,
        **body_hero_info,
        **publication_components,
        "images": [image.as_dict() for image in images],
        "localImageCount": len(local_images),
        "remoteImageCount": len(remote_images),
        "transport": transport,
    }


def _print_human(report: dict[str, object]) -> None:
    status = "通过" if report.get("ok") else "需处理"
    print(f"公众号文章预检：{status}")
    if report.get("title"):
        print(f"标题：{report['title']}（{report.get('titleOrigin')}）")
    if report.get("contentChars") is not None:
        print(f"正文：{report['contentChars']} 字符 / {report['contentBytes']} 字节")
    print(f"transport：{report.get('transport')}")
    for label, key in (("错误", "errors"), ("提示", "warnings")):
        for item in report.get(key, []):
            print(f"{label}：{item}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Markdown、HTML 或纯文本正文")
    parser.add_argument("--cover", type=Path, required=True, help="文章封面图片")
    parser.add_argument(
        "--cover-composition-receipt",
        type=Path,
        help="由 lov-wechat-branding-cover-composition 生成的 cover-composition.json",
    )
    parser.add_argument(
        "--lovpen-wechat-html",
        type=Path,
        help="由 lovpen-cli render --format wechat 生成的微信复制态 HTML",
    )
    parser.add_argument(
        "--brand-profile",
        type=Path,
        help="包含永久品牌尾注与当前活动状态的公众号品牌 Profile。",
    )
    parser.add_argument(
        "--allow-unverified-cover",
        action="store_true",
        help="仅用于诊断旧链路；允许跳过品牌封面合成收据。",
    )
    parser.add_argument(
        "--allow-compact-markdown",
        action="store_true",
        help="仅用于诊断旧链路；允许跳过 Lovpen 微信复制态产物。",
    )
    parser.add_argument(
        "--allow-unverified-body-hero",
        action="store_true",
        help="仅用于诊断旧链路；允许跳过正文第一块 4:3 首图验收。",
    )
    parser.add_argument("--title", help="显式标题；省略时从正文推断")
    parser.add_argument("--author")
    parser.add_argument("--digest")
    parser.add_argument("--source-url")
    parser.add_argument(
        "--transport",
        choices=("auto", "gateway", "oneshot", "api", "browser"),
        default="auto",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = analyze_article(
        args.source,
        args.cover,
        title=args.title,
        author=args.author,
        digest=args.digest,
        source_url=args.source_url,
        transport=args.transport,
        lovpen_wechat_html=args.lovpen_wechat_html,
        cover_composition_receipt=args.cover_composition_receipt,
        require_lovpen=not args.allow_compact_markdown,
        require_composed_cover=not args.allow_unverified_cover,
        require_body_hero=not args.allow_unverified_body_hero,
        brand_profile=args.brand_profile,
    )
    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_human(report)
    return 0 if report.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())
