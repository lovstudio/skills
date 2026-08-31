#!/usr/bin/env python3
"""Validate a local WeChat article package and write its quality report."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from PIL import Image


ARTICLE_SCHEMA = "lovstudio/wechat-article-package/v2"
COVER_SCHEMA = "lovstudio/wechat-cover-package/v2"
LEGACY_ARTICLE_SCHEMA = "lovstudio/wechat-article-package/v1"
LEGACY_COVER_SCHEMA = "lovstudio/wechat-cover-package/v1"
REQUIRED_BASE = [
    "article.md",
    "article-manifest.json",
    "sources.md",
    "cover/art-master.png",
    "cover/wechat-cover-wide.png",
    "cover/wechat-cover-wide.jpg",
    "cover/cover-manifest.json",
]

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

SESSION_CONTEXT_LEAK = re.compile(
    r"(?:我|我们)?(?:前一版|上一版|前一稿|上一稿)|"
    r"(?:按你的要求|你之前说|我们(?:刚才|之前)讨论过)"
)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative(path_value: object) -> bool:
    if not isinstance(path_value, str) or not path_value:
        return False
    pure = PurePosixPath(path_value)
    return not pure.is_absolute() and ".." not in pure.parts and "\\" not in path_value


def local_markdown_image_paths(article: str) -> list[str]:
    paths: set[str] = set()
    for match in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", article):
        raw = match.group(1).strip()
        quoted = re.match(r"(.+?)\s+(['\"]).*\2\s*$", raw)
        target = (quoted.group(1) if quoted else raw).strip("<>")
        if target.startswith(("http://", "https://", "data:", "//")):
            continue
        paths.add(target)
    return sorted(paths)


def opening_context_leaks(article: str) -> list[str]:
    """Return session-dependent phrases from the title plus opening 300 chars."""
    without_fence = re.sub(r"```[\s\S]*?```", " ", article)
    visible = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", without_fence)
    visible = re.sub(r"(?m)^#\s+.*$", " ", visible, count=1)
    opening = re.sub(r"\s+", " ", visible).strip()[:300]
    return [match.group(0) for match in SESSION_CONTEXT_LEAK.finditer(opening)]


def benchmark_errors(article: str) -> list[str]:
    """Return reproducibility failures for articles that present a benchmark."""
    h1 = re.search(r"(?m)^#\s+(.+)$", article)
    title = h1.group(1) if h1 else ""
    quantified_claim = bool(re.search(r"排名|排行榜|第一名|总分|雷达图", article)) and bool(
        re.search(r"评分|得分|分数|权重", article)
    )
    is_benchmark = (
        bool(re.search(r"调研|评测|benchmark", title, re.IGNORECASE))
        or ("## 测试方法" in article and "## 测试结果" in article)
        or quantified_claim
    )
    if not is_benchmark:
        return []

    headings = [match.group(1).strip() for match in re.finditer(r"(?m)^##\s+(.+?)\s*$", article)]
    missing = [heading for heading in BENCHMARK_REQUIRED_SECTIONS if heading not in headings]
    errors = [f"benchmark article missing required section: {heading}" for heading in missing]
    if missing:
        return errors

    positions = [headings.index(heading) for heading in BENCHMARK_REQUIRED_SECTIONS]
    if positions != sorted(positions):
        errors.append("benchmark methodology, prompt, rubric, reproduction, results, and limitations are out of order")

    prompt_match = re.search(
        r"(?ms)^##\s+Prompt\s*$\n(.*?)(?=^##\s+)",
        article,
    )
    prompt_body = prompt_match.group(1) if prompt_match else ""
    fenced_prompts = re.findall(r"```[^\n]*\n(.*?)```", prompt_body, re.DOTALL)
    if not any(len(re.sub(r"\s+", " ", block).strip()) >= 40 for block in fenced_prompts):
        errors.append("benchmark Prompt section must expose at least one substantive verbatim prompt in a fenced block")
    return errors


def self_test() -> int:
    bad = "# 我调研了市面上所有的去 AI 味 Prompt\n\n我前一版 benchmark 做错了。"
    good = "# 我调研了市面上所有的去 AI 味 Prompt\n\n我把 5 套公开 Skill 和两个对照放到同一组输入上，跑了 63 次。"
    if not opening_context_leaks(bad):
        raise AssertionError("cold-reader regression was not detected")
    if opening_context_leaks(good):
        raise AssertionError("valid cold-reader opening was rejected")
    incomplete_benchmark = "# 我调研了去 AI 味 Prompt\n\n## 测试结果\n\n第一名。\n"
    if not benchmark_errors(incomplete_benchmark):
        raise AssertionError("incomplete benchmark article was not detected")
    complete_benchmark = """# 我调研了去 AI 味 Prompt

## 测试方法
固定模型与输入。
## Prompt
```text
请在保持全部事实、数字、专有名词、链接、引语和作者立场的前提下改写这篇文章，不得补造经历，也不得删除不确定性。
```
## 评价指标
事实保真、声音保留。
## 评分方法
使用离散量表和盲评。
## 评分示例
展示一项原始分和总分计算。
## 复现方法
给出环境、命令、随机种子和产物索引。
## 测试结果
公开原始结果。
## 局限性
说明样本与随机性。
"""
    if benchmark_errors(complete_benchmark):
        raise AssertionError("complete benchmark article was rejected")
    print("SELF-TEST PASSED")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if args.package is None:
        parser.error("provide --package or --self-test")

    package = args.package.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    checks: list[str] = []

    if not package.is_dir():
        parser.error(f"package not found: {package}")
    article_manifest_path = package / "article-manifest.json"
    article_schema = ""
    if article_manifest_path.is_file():
        try:
            article_schema = json.loads(article_manifest_path.read_text(encoding="utf-8")).get("schema", "")
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
    legacy_package = article_schema == LEGACY_ARTICLE_SCHEMA
    opening_files = (
        ["cover/article-opening-vertical.png", "cover/article-opening-vertical.jpg"]
        if legacy_package
        else ["cover/article-opening-4x3.png", "cover/article-opening-4x3.jpg"]
    )
    for relative in REQUIRED_BASE + opening_files:
        if not (package / relative).is_file():
            errors.append(f"missing required file: {relative}")
    if errors:
        report = {"schema": "lovstudio/wechat-article-quality/v1", "valid": False, "checks": checks, "errors": errors, "warnings": warnings, "checked_at": now_iso()}
        (package / "quality-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else "INVALID")
        return 1

    try:
        article_manifest = json.loads((package / "article-manifest.json").read_text(encoding="utf-8"))
        cover_manifest = json.loads((package / "cover/cover-manifest.json").read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        errors.append(f"manifest parse error: {error}")
        article_manifest = {}
        cover_manifest = {}

    if article_manifest.get("schema") not in {ARTICLE_SCHEMA, LEGACY_ARTICLE_SCHEMA}:
        errors.append("article manifest schema mismatch")
    else:
        checks.append("article manifest schema")
    if cover_manifest.get("schema") not in {COVER_SCHEMA, LEGACY_COVER_SCHEMA}:
        errors.append("cover manifest schema mismatch")
    else:
        checks.append("cover manifest schema")

    title = article_manifest.get("title", "")
    excerpt = article_manifest.get("excerpt", "")
    if not isinstance(title, str) or not title or len(title) > 32:
        errors.append("title must contain 1-32 Unicode characters")
    else:
        checks.append("title length")
    if not isinstance(excerpt, str) or not excerpt or len(excerpt) > 120:
        errors.append("excerpt must contain 1-120 Unicode characters")
    else:
        checks.append("excerpt length")

    expected_opening = (
        "cover/article-opening-vertical.jpg" if legacy_package else "cover/article-opening-4x3.jpg"
    )
    expected_paths = {
        "article_path": "article.md",
        "opening_image_path": expected_opening,
        "wide_cover_path": "cover/wechat-cover-wide.jpg",
    }
    for key, expected in expected_paths.items():
        value = article_manifest.get(key)
        if value != expected or not safe_relative(value):
            errors.append(f"invalid {key}: expected {expected}")
        else:
            checks.append(key)

    brand = article_manifest.get("brand", {})
    if not isinstance(brand, dict) or not brand.get("name") or brand.get("logo_source") != "profile:brand.logo":
        errors.append("article brand must name the publisher and reference profile:brand.logo")
    else:
        checks.append("article brand identity")
    if cover_manifest.get("brand", {}).get("name") != brand.get("name"):
        errors.append("article and cover brand names differ")
    else:
        checks.append("brand agreement")
    publication = article_manifest.get("publication", {})
    cover_publication = cover_manifest.get("publication", {})
    if not publication.get("name") or cover_publication.get("name") != publication.get("name"):
        errors.append("article and cover publication names differ")
    else:
        checks.append("publication identity")
    if (
        cover_publication.get("logo_source")
        != "profile:skills.lov-article-creator.records.cover_logo_path"
        or cover_publication.get("logo_variant") != "horizontal-lockup"
        or cover_publication.get("logo_color") != "white"
        or not isinstance(cover_publication.get("logo_aspect_ratio"), (int, float))
        or cover_publication.get("logo_aspect_ratio", 0) < 1.8
        or not isinstance(cover_publication.get("logo_white_pixel_ratio"), (int, float))
        or cover_publication.get("logo_white_pixel_ratio", 0) < 0.98
    ):
        errors.append("cover must use the configured official white horizontal publication lockup")
    else:
        checks.append("white horizontal publication lockup")

    article = (package / "article.md").read_text(encoding="utf-8")
    h1_matches = list(re.finditer(r"(?m)^#\s+\S.*$", article))
    if len(h1_matches) != 1:
        errors.append(f"article must contain exactly one H1, found {len(h1_matches)}")
    else:
        checks.append("single H1")
    image_index = article.find(expected_opening)
    first_h2 = re.search(r"(?m)^##\s+\S", article)
    if image_index < 0 or (first_h2 and image_index > first_h2.start()) or (h1_matches and image_index < h1_matches[0].end()):
        errors.append("body opening image must appear after H1 and before the first H2")
    else:
        checks.append("opening image placement")
    context_leaks = opening_context_leaks(article)
    if context_leaks:
        errors.append(
            "opening depends on session or draft history: "
            + ", ".join(context_leaks)
        )
    else:
        checks.append("cold-reader opening context")
    reproducibility_errors = benchmark_errors(article)
    if reproducibility_errors:
        errors.extend(reproducibility_errors)
    elif re.search(r"调研|评测|benchmark", title, re.IGNORECASE):
        checks.append("benchmark reproducibility contract")

    if not legacy_package:
        local_images = [path for path in local_markdown_image_paths(article) if path != expected_opening]
        manifest_images = article_manifest.get("body_image_paths")
        if manifest_images != local_images:
            errors.append("body_image_paths must list every packaged local body image")
        else:
            checks.append("body image manifest")
        for relative in local_images:
            if not safe_relative(relative) or not (package / relative).is_file():
                errors.append(f"missing packaged body image: {relative}")
            else:
                checks.append(f"packaged body image: {relative}")

    public_text = article + (package / "sources.md").read_text(encoding="utf-8") + json.dumps(article_manifest, ensure_ascii=False) + json.dumps(cover_manifest, ensure_ascii=False)
    if re.search(r"(?:/Users/|C:\\Users\\)", public_text):
        errors.append("package leaks a private absolute user path")
    else:
        checks.append("portable public paths")

    image_specs = [
        ("wide", 1880, 800, 2.35, "cover/wechat-cover-wide.png", "cover/wechat-cover-wide.jpg"),
    ]
    if legacy_package:
        image_specs.append(("vertical", 1200, 1600, 0.75, "cover/article-opening-vertical.png", "cover/article-opening-vertical.jpg"))
        warnings.append("legacy v1 package uses a 3:4 opening image; new packages must use the v2 4:3 body hero")
    else:
        image_specs.append(("opening", 1600, 1200, 4 / 3, "cover/article-opening-4x3.png", "cover/article-opening-4x3.jpg"))
    for key, min_width, min_height, expected_ratio, png_rel, jpg_rel in image_specs:
        spec = cover_manifest.get(key, {})
        for format_key, relative in (("png", png_rel), ("jpg", jpg_rel)):
            image_path = package / relative
            with Image.open(image_path) as image:
                width, height = image.size
            if width < min_width or height < min_height or abs(width / height - expected_ratio) > 0.01:
                errors.append(f"{relative} has invalid dimensions {width}x{height}")
            elif spec.get("width") != width or spec.get("height") != height:
                errors.append(f"{key} manifest dimensions do not match {relative}")
            else:
                checks.append(f"{relative} dimensions")
            expected_hash = spec.get("sha256", {}).get(format_key)
            if expected_hash != sha256(image_path):
                errors.append(f"{relative} SHA-256 mismatch")
            else:
                checks.append(f"{relative} SHA-256")

    if not article_manifest.get("read_original_url"):
        warnings.append("read_original_url is empty; acceptable only when no online version exists")

    valid = not errors
    if valid:
        article_manifest["status"] = "prepared"
        publication = article_manifest.setdefault("publication", {})
        publication["status"] = "prepared"
        (package / "article-manifest.json").write_text(json.dumps(article_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        checks.append("publication state promoted to prepared")

    report = {
        "schema": "lovstudio/wechat-article-quality/v1",
        "valid": valid,
        "status": "prepared" if valid else "failed",
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "checked_at": now_iso(),
    }
    (package / "quality-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else ("VALID" if valid else "INVALID"))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
