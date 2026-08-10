#!/usr/bin/env python3
"""Scaffold, render, and audit consulting-grade infographic projects."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import json
import mimetypes
import os
import re
import shutil
import struct
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


SKILL_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = SKILL_ROOT / "assets"
DEFAULT_BRAND = ASSETS_DIR / "brand-profile.template.json"
DEFAULT_USER_BRAND = Path("${SKILLS_CONFIG_DIR}/professional-infographic-brand.json")
DEFAULT_SHARED_PROFILE = Path("${SKILLS_CONFIG_DIR}/profile.json")

CANVASES: Dict[str, Tuple[int, int]] = {
    "4:5": (1080, 1350),
    "16:9": (1600, 900),
    "1:1": (1200, 1200),
    "A4": (1240, 1754),
}

TEMPLATE_NAMES = (
    "comparison-matrix",
    "decision-tree",
    "driver-tree",
    "positioning-map",
    "waterfall",
    "roadmap",
    "operating-model",
    "small-multiples",
)

ALLOWED_ENCODINGS = {
    "position",
    "length",
    "color",
    "shape",
    "connection",
    "order",
    "containment",
}

TEMPLATE_CONTRACTS: Dict[str, Dict[str, int]] = {
    "comparison-matrix": {
        "entities": 3,
        "dimensions": 3,
        "dataPoints": 6,
        "annotations": 1,
        "decisionMarkers": 1,
        "encodings": 2,
    },
    "decision-tree": {
        "conditions": 3,
        "branches": 4,
        "outcomes": 3,
        "connectors": 4,
        "decisionMarkers": 1,
        "encodings": 2,
    },
    "driver-tree": {
        "drivers": 5,
        "levels": 3,
        "connectors": 4,
        "annotations": 2,
        "decisionMarkers": 1,
        "encodings": 2,
    },
    "positioning-map": {
        "axes": 2,
        "axisEnds": 4,
        "zones": 4,
        "dataPoints": 4,
        "annotations": 2,
        "decisionMarkers": 1,
        "encodings": 2,
    },
    "waterfall": {
        "dataPoints": 4,
        "baselines": 1,
        "units": 1,
        "annotations": 2,
        "decisionMarkers": 1,
        "encodings": 2,
    },
    "roadmap": {
        "phases": 3,
        "milestones": 4,
        "gates": 2,
        "connectors": 3,
        "decisionMarkers": 1,
        "encodings": 2,
    },
    "operating-model": {
        "actors": 2,
        "capabilities": 3,
        "flows": 3,
        "outcomes": 2,
        "connectors": 3,
        "annotations": 2,
        "decisionMarkers": 1,
        "encodings": 2,
    },
    "small-multiples": {
        "panels": 3,
        "dataPoints": 6,
        "units": 1,
        "annotations": 2,
        "decisionMarkers": 1,
        "encodings": 2,
    },
}

REQUIRED_BRAND_FIELDS = (
    "name",
    "logo",
    "primary",
    "accent",
    "ink",
    "muted",
    "paper",
    "font_family",
    "copyright",
)

HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
PLACEHOLDER = re.compile(
    r"\b(?:TODO|TBD|FIXME|Lorem ipsum)\b|请替换|示例结构|占位",
    re.IGNORECASE,
)
EMOJI = re.compile(
    "["
    "\U0001F1E6-\U0001F1FF"
    "\U0001F300-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U0000FE0F"
    "]"
)


class CliError(RuntimeError):
    """An actionable user-facing CLI error."""


def expand_path(value: str, base: Optional[Path] = None) -> Path:
    expanded = os.path.expandvars(os.path.expanduser(value))
    path = Path(expanded)
    if not path.is_absolute() and base is not None:
        path = base / path
    return path.resolve()


def read_json(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except FileNotFoundError as exc:
        raise CliError(f"JSON file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CliError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CliError(f"Expected a JSON object in {path}")
    return value


def write_json(path: Path, value: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def report_path_value(path: Path, report_path: Optional[Path]) -> str:
    if report_path is None:
        return str(path)
    return os.path.relpath(path, report_path.parent)


def shared_profile_path() -> Path:
    raw = os.environ.get("SKILL_PROFILE_PATH", str(DEFAULT_SHARED_PROFILE))
    return expand_path(raw)


def load_shared_profile() -> Dict[str, Any]:
    path = shared_profile_path()
    if not path.is_file():
        return {}
    return read_json(path)


def configured_brand_path(explicit: Optional[str]) -> Path:
    candidates: List[Optional[str]] = [
        explicit,
        os.environ.get("SKILL_PROFESSIONAL_INFOGRAPHIC_BRAND_PROFILE"),
        os.environ.get("SKILL_PROFILE_PATH"),
    ]
    for candidate in candidates:
        if candidate:
            path = expand_path(candidate)
            if not path.is_file():
                raise CliError(f"Configured brand profile does not exist: {path}")
            return path

    profile = load_shared_profile()
    brand = profile.get("brand")
    if isinstance(brand, dict) and brand.get("profile"):
        path = expand_path(str(brand["profile"]), shared_profile_path().parent)
        if not path.is_file():
            raise CliError(
                "The shared profile points to a missing brand profile: "
                f"{path}. Run init-brand or fix brand.profile."
            )
        return path

    return DEFAULT_BRAND.resolve()


def validate_color(value: str, field: str) -> str:
    if not HEX_COLOR.fullmatch(value):
        raise CliError(f"{field} must be a six-digit hex color, got {value!r}")
    return value.upper()


def load_brand(explicit: Optional[str]) -> Tuple[Path, Dict[str, Any], Path]:
    profile_path = configured_brand_path(explicit)
    brand = read_json(profile_path)
    missing = [field for field in REQUIRED_BRAND_FIELDS if not brand.get(field)]
    if missing:
        raise CliError(
            f"Brand profile {profile_path} is missing: {', '.join(missing)}"
        )
    for field in ("primary", "accent", "ink", "muted", "paper"):
        brand[field] = validate_color(str(brand[field]), field)
    logo = expand_path(str(brand["logo"]), profile_path.parent)
    if not logo.is_file():
        raise CliError(f"Brand logo does not exist: {logo}")
    return profile_path, brand, logo


def logo_data_url(path: Path) -> str:
    media_type, _ = mimetypes.guess_type(path.name)
    if path.suffix.lower() == ".svg":
        media_type = "image/svg+xml"
    if not media_type or not media_type.startswith("image/"):
        raise CliError(f"Unsupported logo format: {path.suffix or path.name}")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def safe_font_family(value: str) -> str:
    cleaned = value.replace("<", "").replace(">", "").replace("{", "")
    cleaned = cleaned.replace("}", "").replace(";", "")
    if not cleaned.strip():
        raise CliError("font_family cannot be empty")
    return cleaned


def semantic_units(value: str) -> int:
    cjk = len(
        re.findall(
            r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]",
            value,
        )
    )
    without_cjk = re.sub(
        r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]",
        " ",
        value,
    )
    latin_words = len(re.findall(r"[A-Za-z0-9]+(?:[’'\-][A-Za-z0-9]+)*", without_cjk))
    return cjk + latin_words


def slugify(value: str) -> str:
    ascii_text = value.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    if slug:
        return slug[:48].rstrip("-")
    return f"infographic-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"


def resolve_output_root() -> Path:
    for key in (
        "SKILL_PROFESSIONAL_INFOGRAPHIC_OUTPUT_DIR",
        "SKILL_OUTPUT_DIR",
    ):
        if os.environ.get(key):
            return expand_path(os.environ[key])
    profile = load_shared_profile()
    workspace = profile.get("workspace")
    if isinstance(workspace, dict) and workspace.get("output_dir"):
        return expand_path(str(workspace["output_dir"]), shared_profile_path().parent)
    return (Path.cwd() / "professional-infographic").resolve()


def init_brand(args: argparse.Namespace) -> int:
    output = expand_path(args.output or str(DEFAULT_USER_BRAND))
    if output.exists() and not args.force:
        raise CliError(f"Refusing to overwrite existing brand profile: {output}")
    logo = expand_path(args.logo)
    if not logo.is_file():
        raise CliError(f"Logo does not exist: {logo}")

    brand = {
        "schema_version": 1,
        "name": args.name,
        "site": args.site or "",
        "logo": str(logo),
        "primary": validate_color(args.primary, "primary"),
        "accent": validate_color(args.accent, "accent"),
        "ink": validate_color(args.ink, "ink"),
        "muted": validate_color(args.muted, "muted"),
        "paper": validate_color(args.paper, "paper"),
        "font_family": safe_font_family(args.font_family),
        "copyright": args.copyright
        or f"Generated by {args.name}'s Professional Infographic Skill",
        "output_dir": args.output_dir or "$HOME/Documents/professional-infographic",
    }
    write_json(output, brand)
    print(f"Brand profile created: {output}")
    return 0


def render_template(template: str, replacements: Dict[str, str]) -> str:
    result = template
    for key, value in replacements.items():
        result = result.replace("{{" + key + "}}", value)
    unresolved = sorted(set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", result)))
    if unresolved:
        raise CliError(f"Unresolved template variables: {', '.join(unresolved)}")
    return result


def load_visual_template(name: str) -> Tuple[str, str]:
    path = ASSETS_DIR / "templates" / f"{name}.html"
    if not path.is_file():
        raise CliError(f"Visual template does not exist: {path}")
    value = path.read_text(encoding="utf-8")
    style_match = re.search(
        r"<style\s+data-template-style>(.*?)</style>",
        value,
        re.DOTALL | re.IGNORECASE,
    )
    body_match = re.search(
        r"<template\s+data-template-body>(.*?)</template>",
        value,
        re.DOTALL | re.IGNORECASE,
    )
    if not style_match or not body_match:
        raise CliError(
            f"Template {path.name} must contain data-template-style and "
            "data-template-body blocks"
        )
    return style_match.group(1).strip(), body_match.group(1).strip()


def recommendation_block(recommendation: str) -> str:
    value = recommendation.strip() or (
        "请替换：基于上方证据给出具体建议、适用条件或下一步行动。"
    )
    return f"""<section
      class="recommendation"
      data-region="recommendation"
      data-audit="recommendation"
      data-annotation
      data-decision
      data-source-ref="S1"
    >
      <strong>Recommendation</strong>
      <p>{html.escape(value)}</p>
    </section>"""


def scaffold_brief(
    title: str,
    template_name: str,
    mode: str,
    title_mode: str,
    recommendation: str,
) -> str:
    if title_mode == "topic":
        tail_recommendation = recommendation or "Not written yet."
    else:
        tail_recommendation = "Not applicable; the action title carries the conclusion."
    if title_mode == "topic":
        message_guidance = """Use the display title to explain the infographic's subject, purpose, or
reader job. Put the evidence-backed recommendation after the main visual so the
reader encounters context first, evidence second, and advice last."""
        copy_map = f"""- Figure label:
- Display title: {title}
- Optional deck:
- Tail recommendation: {recommendation or "Write the evidence-backed advice here."}
- Visual labels:
- Source / note:"""
        review_items = """- [ ] The title explains what the infographic is for or what it compares.
- [ ] The recommendation appears after the evidence and before the source footer.
- [ ] The recommendation is not duplicated in the title."""
    else:
        message_guidance = """Use one answer-first title supported by visible evidence. Do not add a
separate recommendation band that repeats the same sentence."""
        copy_map = f"""- Figure label:
- Action title: {title}
- Optional deck:
- Visual labels:
- Source / note:"""
        review_items = """- [ ] The action title states a non-obvious conclusion.
- [ ] The visual proves the title rather than restating it.
- [ ] No separate recommendation band duplicates the title."""

    return f"""# Infographic brief

Working title: {title}
Title mode: {title_mode}
Tail recommendation: {tail_recommendation}
Template: {template_name}
Evidence mode: {mode}

## Audience and decision

- Audience:
- Decision or use moment:
- What should change after reading:

## Governing message

{message_guidance}

## Argument and evidence map

| ID | Claim or decision criterion | Exact evidence | Visual encoding | Annotation |
|---|---|---|---|---|
| C1 | | | | |
| C2 | | | | |
| C3 | | | | |

## Evidence ledger

- Evidence ID:
  - Supports claim:
  - Exact source:
  - Location:
  - Type: fact | estimate | assumption | interpretation
  - Unit / period:
  - Caveat:

## Assumptions and gaps

- None recorded yet.

## Exhibit specification

- Primary relationship: compare | decide | decompose | locate | bridge | sequence | system | trend
- Template: {template_name}
- Evidence mode: {mode}
- Required encodings:
- Direct annotations:
- Decision marker:
- Source-reference mapping:

## Copy map

{copy_map}

## Deliberate omissions

- List material excluded to preserve a single visual argument.

## Human review

{review_items}
- [ ] Color, position, length, shape, or connection each has one explicit meaning.
- [ ] Every plotted point or decision cell maps to evidence.
- [ ] The Exhibit is legible at 100% and intelligible at thumbnail size.
"""


def scaffold(args: argparse.Namespace) -> int:
    title = args.title.strip()
    if not title:
        raise CliError("--title cannot be empty")
    recommendation = (args.recommendation or "").strip()
    if args.title_mode == "action" and recommendation:
        raise CliError(
            "--recommendation is only valid with --title-mode topic; "
            "an action title already carries the recommendation"
        )
    width, height = CANVASES[args.aspect]
    brand_path, brand, logo = load_brand(args.brand_profile)

    if args.output_dir:
        project_dir = expand_path(args.output_dir)
    else:
        project_dir = resolve_output_root() / slugify(title)
    if project_dir.exists() and any(project_dir.iterdir()):
        raise CliError(
            f"Refusing to write into non-empty project directory: {project_dir}"
        )
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "assets").mkdir(exist_ok=True)

    source_text = ""
    if args.source:
        source_path = expand_path(args.source)
        if not source_path.is_file():
            raise CliError(f"Source file does not exist: {source_path}")
        source_text = source_path.read_text(encoding="utf-8")
    if not source_text.strip():
        source_text = (
            "# Source\n\n"
            "Paste or preserve the exact source material here before authoring.\n"
        )

    template = (ASSETS_DIR / "poster-template.html").read_text(encoding="utf-8")
    template_style, visual_body = load_visual_template(args.template)
    replacements = {
        "TITLE": html.escape(title),
        "TITLE_MODE": args.title_mode,
        "RECOMMENDATION_BLOCK": (
            recommendation_block(recommendation)
            if args.title_mode == "topic"
            else ""
        ),
        "ASPECT": args.aspect,
        "CANVAS_WIDTH": str(width),
        "CANVAS_HEIGHT": str(height),
        "BRAND_NAME": html.escape(str(brand["name"])),
        "BRAND_LOGO_DATA_URL": logo_data_url(logo),
        "BRAND_PRIMARY": str(brand["primary"]),
        "BRAND_ACCENT": str(brand["accent"]),
        "BRAND_INK": str(brand["ink"]),
        "BRAND_MUTED": str(brand["muted"]),
        "BRAND_PAPER": str(brand["paper"]),
        "FONT_FAMILY": safe_font_family(str(brand["font_family"])),
        "COPYRIGHT": html.escape(str(brand["copyright"])),
        "SITE": html.escape(str(brand.get("site", ""))),
        "TEMPLATE_NAME": args.template,
        "EVIDENCE_MODE": args.mode,
        "TEMPLATE_STYLE": template_style,
        "VISUAL_BODY": visual_body,
    }
    poster = render_template(template, replacements)

    (project_dir / "source.md").write_text(source_text, encoding="utf-8")
    (project_dir / "brief.md").write_text(
        scaffold_brief(
            title,
            args.template,
            args.mode,
            args.title_mode,
            recommendation,
        ),
        encoding="utf-8",
    )
    (project_dir / "poster.html").write_text(poster, encoding="utf-8")
    project = {
        "schema_version": 3,
        "title": title,
        "title_mode": args.title_mode,
        "recommendation": recommendation,
        "aspect": args.aspect,
        "template": args.template,
        "evidence_mode": args.mode,
        "canvas": {"width": width, "height": height},
        "brand_profile": str(brand_path),
        "brand_name": brand["name"],
        "source": "source.md",
        "brief": "brief.md",
        "poster": "poster.html",
    }
    write_json(project_dir / "project.json", project)
    print(f"Project scaffolded: {project_dir}")
    print(f"Editable source: {project_dir / 'poster.html'}")
    return 0


def find_chrome() -> Optional[str]:
    candidates = [
        os.environ.get("CHROME_PATH"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate).resolve())
    return None


def import_playwright() -> Tuple[Any, Any]:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise CliError(
            "Playwright is required. Install it with: "
            'python3 -m pip install "playwright>=1.45,<2" && '
            "python3 -m playwright install chromium"
        ) from exc
    return sync_playwright, PlaywrightError


def launch_browser(playwright: Any, playwright_error: Any) -> Any:
    try:
        return playwright.chromium.launch(
            headless=True,
            args=["--font-render-hinting=none"],
        )
    except playwright_error as first_error:
        chrome = find_chrome()
        if not chrome:
            raise CliError(
                "Chromium is unavailable. Run `python3 -m playwright install "
                "chromium` or set CHROME_PATH."
            ) from first_error
        try:
            return playwright.chromium.launch(
                headless=True,
                executable_path=chrome,
                args=["--font-render-hinting=none"],
            )
        except playwright_error as second_error:
            raise CliError(f"Could not launch Chromium or Chrome: {second_error}") from second_error


def detect_aspect(markup: str) -> str:
    poster_tag = re.search(
        r"<[^>]*\bclass=[\"'][^\"']*\bposter\b[^\"']*[\"'][^>]*>",
        markup,
        re.IGNORECASE,
    )
    match = (
        re.search(r'data-aspect=["\']([^"\']+)["\']', poster_tag.group(0))
        if poster_tag
        else None
    )
    if not match or match.group(1) not in CANVASES:
        raise CliError(
            "poster.html must set .poster data-aspect to one of: "
            + ", ".join(CANVASES)
        )
    return match.group(1)


def wait_until_ready(page: Any, timeout_ms: int) -> None:
    try:
        page.wait_for_function(
            "window.__INFOGRAPHIC_READY__ === true",
            timeout=timeout_ms,
        )
    except Exception as exc:
        raise CliError(
            "The poster did not set window.__INFOGRAPHIC_READY__ = true "
            f"within {timeout_ms} ms."
        ) from exc


def render(args: argparse.Namespace) -> int:
    input_path = expand_path(args.input)
    if not input_path.is_file():
        raise CliError(f"Input HTML does not exist: {input_path}")
    output_path = expand_path(args.output)
    if output_path.suffix.lower() != ".png":
        raise CliError("--output must end in .png")
    markup = input_path.read_text(encoding="utf-8")
    aspect = detect_aspect(markup)
    width, height = CANVASES[aspect]
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sync_playwright, playwright_error = import_playwright()
    with sync_playwright() as playwright:
        browser = launch_browser(playwright, playwright_error)
        try:
            context = browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=args.scale,
            )
            page = context.new_page()
            page.goto(input_path.as_uri(), wait_until="load", timeout=args.timeout)
            wait_until_ready(page, args.timeout)
            poster = page.locator(".poster")
            if poster.count() != 1:
                raise CliError("poster.html must contain exactly one .poster element")
            poster.screenshot(
                path=str(output_path),
                animations="disabled",
                type="png",
            )
        finally:
            browser.close()

    image_width, image_height = png_dimensions(output_path)
    print(
        f"Rendered: {output_path} "
        f"({image_width}x{image_height}, {args.scale}x)"
    )
    return 0


def png_dimensions(path: Path) -> Tuple[int, int]:
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
    except FileNotFoundError as exc:
        raise CliError(f"PNG does not exist: {path}") from exc
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise CliError(f"Not a valid PNG: {path}")
    return struct.unpack(">II", header[16:24])


def browser_audit(input_path: Path, timeout_ms: int) -> Dict[str, Any]:
    markup = input_path.read_text(encoding="utf-8")
    aspect = detect_aspect(markup)
    width, height = CANVASES[aspect]
    sync_playwright, playwright_error = import_playwright()

    with sync_playwright() as playwright:
        browser = launch_browser(playwright, playwright_error)
        try:
            context = browser.new_context(viewport={"width": width, "height": height})
            page = context.new_page()
            page.goto(input_path.as_uri(), wait_until="load", timeout=timeout_ms)
            wait_until_ready(page, timeout_ms)
            result = page.evaluate(
                """() => {
                  const poster = document.querySelector('.poster');
                  if (!poster) return {missingPoster: true};
                  const posterRect = poster.getBoundingClientRect();

                  function rgba(value) {
                    const match = value.match(
                      /rgba?\\(\\s*([\\d.]+)[, ]+([\\d.]+)[, ]+([\\d.]+)(?:\\s*[,/]\\s*([\\d.]+))?\\s*\\)/
                    );
                    if (!match) return null;
                    return [
                      Number(match[1]), Number(match[2]), Number(match[3]),
                      match[4] === undefined ? 1 : Number(match[4])
                    ];
                  }

                  function backgroundFor(element) {
                    let node = element;
                    while (node) {
                      const parsed = rgba(getComputedStyle(node).backgroundColor);
                      if (parsed && parsed[3] > 0.01) return parsed;
                      node = node.parentElement;
                    }
                    return [255, 255, 255, 1];
                  }

                  function luminance(rgb) {
                    const channels = rgb.slice(0, 3).map((v) => {
                      const n = v / 255;
                      return n <= 0.03928 ? n / 12.92 : Math.pow((n + 0.055) / 1.055, 2.4);
                    });
                    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
                  }

                  function contrast(fg, bg) {
                    if (!fg || !bg) return null;
                    const l1 = luminance(fg);
                    const l2 = luminance(bg);
                    return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
                  }

                  function areaRatio(element) {
                    if (!element) return 0;
                    const rect = element.getBoundingClientRect();
                    return (rect.width * rect.height) / (posterRect.width * posterRect.height);
                  }

                  function occupancy(element) {
                    const rect = element.getBoundingClientRect();
                    const blockArea = Math.max(1, rect.width * rect.height);
                    const marks = [...element.querySelectorAll(
                      '[data-data-point], [data-annotation], [data-condition], ' +
                      '[data-outcome], [data-driver], [data-milestone], [data-capability], ' +
                      '[data-zone], [data-phase], [data-panel], ' +
                      'svg text, svg rect, svg circle, svg path, svg line, h2, h3, p, span'
                    )];
                    let occupied = 0;
                    for (const mark of marks) {
                      const style = getComputedStyle(mark);
                      if (style.display === 'none' || style.visibility === 'hidden') continue;
                      const item = mark.getBoundingClientRect();
                      const width = Math.max(
                        0,
                        Math.min(rect.right, item.right) - Math.max(rect.left, item.left)
                      );
                      const height = Math.max(
                        0,
                        Math.min(rect.bottom, item.bottom) - Math.max(rect.top, item.top)
                      );
                      occupied += width * height;
                    }
                    return Math.min(1, occupied / blockArea);
                  }

                  function visibleElements(selector) {
                    return [...poster.querySelectorAll(selector)].filter((element) => {
                      const style = getComputedStyle(element);
                      const rect = element.getBoundingClientRect();
                      return style.display !== 'none' &&
                             style.visibility !== 'hidden' &&
                             rect.width > 0 &&
                             rect.height > 0;
                    });
                  }

                  function visibleCount(selector) {
                    return visibleElements(selector).length;
                  }

                  const audited = [...document.querySelectorAll('[data-audit]')].map((el) => {
                    const rect = el.getBoundingClientRect();
                    const style = getComputedStyle(el);
                    const fg = rgba(style.color);
                    const bg = backgroundFor(el);
                    return {
                      kind: el.dataset.audit,
                      text: (el.innerText || el.textContent || '').trim(),
                      fontSize: Number.parseFloat(style.fontSize),
                      outside: rect.left < posterRect.left - 1 ||
                               rect.top < posterRect.top - 1 ||
                               rect.right > posterRect.right + 1 ||
                               rect.bottom > posterRect.bottom + 1,
                      contrast: contrast(fg, bg)
                    };
                  });

                  const containerNodes = [
                    ...poster.querySelectorAll(
                      '[data-audit-container], [data-region="visual"], [data-primary-block]'
                    )
                  ];
                  const containers = containerNodes.map((el) => {
                    const rect = el.getBoundingClientRect();
                    const name = el.hasAttribute('data-region')
                        ? `[data-region="${el.getAttribute('data-region')}"]`
                        : el.hasAttribute('data-primary-block')
                          ? '[data-primary-block]'
                          : '[data-audit-container]';
                    return {
                      name,
                      text: (el.innerText || '').trim().slice(0, 80),
                      overflow: el.scrollWidth > el.clientWidth + 2 ||
                                el.scrollHeight > el.clientHeight + 2,
                      outside: rect.left < posterRect.left - 1 ||
                               rect.top < posterRect.top - 1 ||
                               rect.right > posterRect.right + 1 ||
                               rect.bottom > posterRect.bottom + 1
                    };
                  });

                  const images = [...poster.querySelectorAll('img')].map((img) => ({
                    alt: img.alt,
                    src: img.getAttribute('src') || '',
                    complete: img.complete,
                    naturalWidth: img.naturalWidth,
                    naturalHeight: img.naturalHeight
                  }));

                  const encodings = new Set();
                  for (const element of visibleElements('[data-encoding]')) {
                    for (const token of (element.dataset.encoding || '').split(/\\s+/)) {
                      if (token) encodings.add(token);
                    }
                  }

                  const blocks = visibleElements('[data-primary-block]').map((el) => ({
                    occupancy: occupancy(el),
                    areaRatio: areaRatio(el),
                    text: (el.innerText || '').trim().slice(0, 80)
                  }));
                  const header = poster.querySelector('[data-region="header"]');
                  const visual = poster.querySelector('[data-region="visual"]');
                  const recommendation = poster.querySelector(
                    '[data-region="recommendation"][data-audit="recommendation"]'
                  );
                  const footer = poster.querySelector('[data-region="footer"]');
                  const visualRect = visual ? visual.getBoundingClientRect() : null;
                  const recommendationRect = recommendation
                    ? recommendation.getBoundingClientRect()
                    : null;
                  const footerRect = footer ? footer.getBoundingClientRect() : null;
                  const cardNodes = [...poster.querySelectorAll(
                    '.card, .pillar, .bento, [data-card]'
                  )];
                  const cardAreaRatio = cardNodes.reduce(
                    (sum, el) => sum + areaRatio(el),
                    0
                  );

                  return {
                    missingPoster: false,
                    width: Math.round(posterRect.width),
                    height: Math.round(posterRect.height),
                    template: poster.dataset.template || '',
                    evidenceMode: poster.dataset.mode || '',
                    titleMode: poster.dataset.titleMode || 'action',
                    titleModeExplicit: Boolean(poster.dataset.titleMode),
                    titleCount: visibleCount('.poster__title[data-audit="title"]'),
                    recommendationCount: visibleCount(
                      '[data-region="recommendation"][data-audit="recommendation"]'
                    ),
                    recommendationAfterVisual: Boolean(
                      visualRect &&
                      recommendationRect &&
                      recommendationRect.top >= visualRect.bottom - 2
                    ),
                    recommendationBeforeFooter: Boolean(
                      recommendationRect &&
                      footerRect &&
                      recommendationRect.bottom <= footerRect.top + 2
                    ),
                    recommendationSourceRefs: recommendation
                      ? visibleCount(
                          '[data-region="recommendation"] [data-source-ref], ' +
                          '[data-region="recommendation"][data-source-ref]'
                        )
                      : 0,
                    visualCount: visibleCount('[data-region="visual"]'),
                    sourceCount: visibleCount('.source-note[data-audit="source"]'),
                    attributionCount: visibleCount('.generation-note[data-audit="attribution"]'),
                    brandLogoCount: visibleCount('.brand-lockup img'),
                    primaryBlocks: visibleCount('[data-primary-block]'),
                    headerAreaRatio: areaRatio(header),
                    visualAreaRatio: areaRatio(visual),
                    footerAreaRatio: areaRatio(footer),
                    cardAreaRatio,
                    blocks,
                    encodings: [...encodings],
                    dataPoints: visibleCount('[data-data-point]'),
                    annotations: visibleCount('[data-annotation]'),
                    sourceRefs: visibleCount('[data-source-ref]'),
                    decisionMarkers: visibleCount('[data-decision]'),
                    entities: visibleCount('[data-entity]'),
                    dimensions: visibleCount('[data-dimension]'),
                    conditions: visibleCount('[data-condition]'),
                    branches: visibleCount('[data-branch]'),
                    outcomes: visibleCount('[data-outcome]'),
                    connectors: visibleCount('[data-connector]'),
                    drivers: visibleCount('[data-driver]'),
                    levels: new Set(
                      visibleElements('[data-level]')
                        .map((el) => el.getAttribute('data-level'))
                    ).size,
                    axes: visibleCount('[data-axis]'),
                    axisEnds: visibleCount('[data-axis-end]'),
                    zones: visibleCount('[data-zone]'),
                    baselines: visibleCount('[data-baseline]'),
                    units: visibleCount('[data-unit]'),
                    phases: visibleCount('[data-phase]'),
                    milestones: visibleCount('[data-milestone]'),
                    gates: visibleCount('[data-gate]'),
                    actors: visibleCount('[data-actor]'),
                    capabilities: visibleCount('[data-capability]'),
                    flows: visibleCount('[data-flow]'),
                    panels: visibleCount('[data-panel]'),
                    text: poster.innerText.trim(),
                    audited,
                    containers,
                    images
                  };
                }"""
            )
            if not isinstance(result, dict):
                raise CliError("Browser audit returned an invalid result")
            result["aspect"] = aspect
            return result
        finally:
            browser.close()


def add_issue(
    items: List[Dict[str, str]],
    code: str,
    message: str,
    selector: str = "",
) -> None:
    item = {"code": code, "message": message}
    if selector:
        item["selector"] = selector
    items.append(item)


def bounded_score(value: float, maximum: int) -> int:
    return max(0, min(maximum, int(round(value))))


def professional_proxy_score(
    result: Dict[str, Any],
    audited: Sequence[Dict[str, Any]],
    errors: Sequence[Dict[str, str]],
    warnings: Sequence[Dict[str, str]],
    contract_passed: bool,
) -> Dict[str, Any]:
    title_items = [item for item in audited if item.get("kind") == "title"]
    title_units = semantic_units(str(title_items[0].get("text", ""))) if title_items else 999
    recommendation_items = [
        item for item in audited if item.get("kind") == "recommendation"
    ]
    recommendation_units = (
        semantic_units(str(recommendation_items[0].get("text", "")))
        if recommendation_items
        else 999
    )
    title_mode = str(result.get("titleMode", "action"))
    conclusion = 0
    if result.get("titleCount") == 1:
        conclusion += 6
    if 8 <= title_units <= 34:
        conclusion += 4
    elif title_units < 44:
        conclusion += 2
    if int(result.get("decisionMarkers", 0)) >= 1:
        conclusion += 4
    if title_mode == "topic":
        if result.get("recommendationCount") == 1:
            conclusion += 4
        if 6 <= recommendation_units <= 48:
            conclusion += 2
    else:
        conclusion += 6

    data_points = int(result.get("dataPoints", 0))
    source_refs = int(result.get("sourceRefs", 0))
    annotations = int(result.get("annotations", 0))
    evidence_marks = (
        data_points
        + int(result.get("outcomes", 0))
        + int(result.get("drivers", 0))
        + int(result.get("milestones", 0))
        + int(result.get("capabilities", 0))
    )
    evidence = (
        bounded_score(evidence_marks / 8 * 8, 8)
        + bounded_score(source_refs / 4 * 8, 8)
        + bounded_score(annotations / 2 * 4, 4)
    )
    if result.get("evidenceMode") in {"quantitative", "mixed"} and int(
        result.get("units", 0)
    ) == 0:
        evidence = max(0, evidence - 5)

    encoding_count = len(result.get("encodings", []))
    encoding = (
        bounded_score(encoding_count / 2 * 8, 8)
        + (8 if contract_passed else 0)
        + bounded_score(annotations / 2 * 4, 4)
    )

    visual_ratio = float(result.get("visualAreaRatio") or 0)
    header_ratio = float(result.get("headerAreaRatio") or 0)
    low_occupancy = sum(
        1
        for block in result.get("blocks", [])
        if float(block.get("occupancy") or 0) < 0.18
    )
    density = 0
    if 0.58 <= visual_ratio <= 0.82:
        density += 5
    elif visual_ratio >= 0.50:
        density += 2
    if 0.07 <= header_ratio <= 0.18:
        density += 3
    elif header_ratio <= 0.22:
        density += 1
    if low_occupancy == 0:
        density += 3
    elif low_occupancy == 1:
        density += 1
    density += bounded_score((data_points + annotations) / 10 * 4, 4)

    copy_issue_codes = {
        "empty-copy",
        "placeholder-copy",
        "title-length",
        "recommendation-length",
        "label-length",
        "description-length",
        "copy-density",
    }
    copy_issues = [
        issue
        for issue in [*errors, *warnings]
        if str(issue.get("code")) in copy_issue_codes
    ]
    copy_score = (5 if not copy_issues else 1) + bounded_score(annotations / 3 * 5, 5)

    technical_codes = {
        "out-of-bounds",
        "container-overflow",
        "container-out-of-bounds",
        "font-size",
        "contrast",
        "broken-image",
        "canvas-size",
    }
    technical_issues = [
        issue for issue in errors if str(issue.get("code")) in technical_codes
    ]
    layout = 6 if not technical_issues else max(0, 6 - len(technical_issues) * 2)
    layout += 2 if float(result.get("cardAreaRatio") or 0) <= 0.35 else 0
    layout += 2 if low_occupancy == 0 else 0

    trust = 0
    if result.get("sourceCount") == 1 and source_refs >= 1:
        trust += 2
    if result.get("brandLogoCount") == 1:
        trust += 1
    if result.get("attributionCount") == 1:
        trust += 1
    if source_refs >= 2:
        trust += 1

    dimensions = {
        "core_conclusion": min(20, conclusion),
        "evidence_quality": min(20, evidence),
        "visual_encoding": min(20, encoding),
        "information_density": min(15, density),
        "copy_and_annotations": min(10, copy_score),
        "layout_and_type": min(10, layout),
        "source_and_brand": min(5, trust),
    }
    critical_minimums = {
        "core_conclusion": 16,
        "evidence_quality": 12,
        "visual_encoding": 14,
        "information_density": 10,
    }
    critical_failures = [
        key
        for key, minimum in critical_minimums.items()
        if int(dimensions.get(key, 0)) < minimum
    ]
    total = sum(dimensions.values())
    return {
        "total": total,
        "threshold": 85,
        "dimensions": dimensions,
        "critical_minimums": critical_minimums,
        "critical_failures": critical_failures,
        "machine_proxy_only": True,
        "human_review_required": True,
    }


def audit(args: argparse.Namespace) -> int:
    input_path = expand_path(args.input)
    if not input_path.is_file():
        raise CliError(f"Input HTML does not exist: {input_path}")
    markup = input_path.read_text(encoding="utf-8")
    aspect = detect_aspect(markup)
    expected_width, expected_height = CANVASES[aspect]
    report_path = expand_path(args.report) if args.report else None
    result = browser_audit(input_path, args.timeout)
    errors: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []

    if result.get("missingPoster"):
        add_issue(errors, "missing-poster", "Missing .poster canvas")
    if result.get("width") != expected_width or result.get("height") != expected_height:
        add_issue(
            errors,
            "canvas-size",
            "Canvas is "
            f"{result.get('width')}x{result.get('height')}; expected "
            f"{expected_width}x{expected_height} for {aspect}",
            ".poster",
        )

    required_counts = {
        "titleCount": (".poster__title[data-audit='title']", "title"),
        "visualCount": ("[data-region='visual']", "main visual"),
        "sourceCount": (".source-note[data-audit='source']", "source note"),
        "attributionCount": (
            ".generation-note[data-audit='attribution']",
            "generation attribution",
        ),
        "brandLogoCount": (".brand-lockup img", "brand logo"),
    }
    for key, (selector, label) in required_counts.items():
        if result.get(key) != 1:
            add_issue(
                errors,
                f"required-{key}",
                f"Expected exactly one {label}; found {result.get(key, 0)}",
                selector,
            )

    template_name = str(result.get("template", "")).strip()
    evidence_mode = str(result.get("evidenceMode", "")).strip()
    title_mode = str(result.get("titleMode", "action")).strip()
    contract_passed = True
    if template_name not in TEMPLATE_CONTRACTS:
        contract_passed = False
        add_issue(
            errors,
            "template-contract",
            "Set .poster data-template to a supported semantic Exhibit template",
            ".poster",
        )
    if evidence_mode not in {"qualitative", "quantitative", "mixed"}:
        add_issue(
            errors,
            "evidence-mode",
            "Set .poster data-mode to qualitative, quantitative, or mixed",
            ".poster",
        )
    if title_mode not in {"topic", "action"}:
        add_issue(
            errors,
            "title-mode",
            "Set .poster data-title-mode to topic or action",
            ".poster",
        )

    recommendation_count = int(result.get("recommendationCount", 0))
    if title_mode == "topic":
        if recommendation_count != 1:
            add_issue(
                errors,
                "required-recommendation",
                "Topic-title infographics require exactly one tail recommendation; "
                f"found {recommendation_count}",
                "[data-region='recommendation'][data-audit='recommendation']",
            )
        else:
            if not result.get("recommendationAfterVisual") or not result.get(
                "recommendationBeforeFooter"
            ):
                add_issue(
                    errors,
                    "recommendation-placement",
                    "Place the recommendation after the main visual and before the source footer",
                    "[data-region='recommendation']",
                )
            if int(result.get("recommendationSourceRefs", 0)) < 1:
                add_issue(
                    errors,
                    "recommendation-evidence",
                    "The recommendation must map to evidence with data-source-ref",
                    "[data-region='recommendation']",
                )
    elif recommendation_count:
        add_issue(
            errors,
            "duplicate-recommendation",
            "Action-title infographics must not repeat the conclusion in a tail recommendation",
            "[data-region='recommendation']",
        )

    audited_items = list(result.get("audited", []))
    title_text = next(
        (
            str(item.get("text", "")).strip()
            for item in audited_items
            if item.get("kind") == "title"
        ),
        "",
    )
    recommendation_text = next(
        (
            str(item.get("text", "")).strip()
            for item in audited_items
            if item.get("kind") == "recommendation"
        ),
        "",
    )
    normalized_title = re.sub(r"[\W_]+", "", title_text, flags=re.UNICODE)
    normalized_recommendation = re.sub(
        r"[\W_]+",
        "",
        recommendation_text,
        flags=re.UNICODE,
    )
    if (
        title_mode == "topic"
        and len(normalized_title) >= 6
        and len(normalized_recommendation) >= 6
        and (
            normalized_title == normalized_recommendation
            or normalized_recommendation in normalized_title
        )
    ):
        add_issue(
            errors,
            "duplicate-title-recommendation",
            "The display title and tail recommendation must play different roles",
            "[data-audit='recommendation']",
        )

    encodings = [str(value) for value in result.get("encodings", [])]
    invalid_encodings = sorted(set(encodings) - ALLOWED_ENCODINGS)
    if invalid_encodings:
        contract_passed = False
        add_issue(
            errors,
            "encoding-token",
            "Unsupported visual encoding token(s): " + ", ".join(invalid_encodings),
            "[data-encoding]",
        )

    if template_name in TEMPLATE_CONTRACTS:
        for metric, minimum in TEMPLATE_CONTRACTS[template_name].items():
            actual = len(encodings) if metric == "encodings" else int(result.get(metric, 0))
            if actual < minimum:
                contract_passed = False
                add_issue(
                    errors,
                    "semantic-contract",
                    f"{template_name} requires at least {minimum} {metric}; found {actual}",
                    f"[data-template='{template_name}']",
                )

    if int(result.get("sourceRefs", 0)) < 1:
        add_issue(
            errors,
            "evidence-linkage",
            "At least one visible mark must map to evidence with data-source-ref",
            "[data-source-ref]",
        )
    if evidence_mode in {"quantitative", "mixed"} and int(result.get("units", 0)) < 1:
        add_issue(
            errors,
            "missing-unit",
            f"{evidence_mode} Exhibits require at least one visible data-unit",
            "[data-unit]",
        )

    header_ratio = float(result.get("headerAreaRatio") or 0)
    visual_ratio = float(result.get("visualAreaRatio") or 0)
    if header_ratio > 0.20:
        add_issue(
            errors,
            "header-area",
            f"Header occupies {header_ratio:.1%} of the canvas; maximum is 20%",
            "[data-region='header']",
        )
    elif header_ratio > 0.18:
        add_issue(
            warnings,
            "header-area",
            f"Header occupies {header_ratio:.1%}; target range is 7%–18%",
            "[data-region='header']",
        )
    if visual_ratio < 0.52:
        add_issue(
            errors,
            "visual-area",
            f"Main visual occupies only {visual_ratio:.1%} of the canvas; minimum is 52%",
            "[data-region='visual']",
        )
    elif visual_ratio < 0.58:
        add_issue(
            warnings,
            "visual-area",
            f"Main visual occupies {visual_ratio:.1%}; target is at least 58%",
            "[data-region='visual']",
        )

    card_area_ratio = float(result.get("cardAreaRatio") or 0)
    if card_area_ratio > 0.55:
        add_issue(
            errors,
            "card-wall",
            f"Generic card-like containers occupy {card_area_ratio:.1%} of the canvas",
            ".card, .pillar, .bento, [data-card]",
        )
    elif card_area_ratio > 0.35:
        add_issue(
            warnings,
            "card-wall",
            f"Generic card-like containers occupy {card_area_ratio:.1%}; verify they encode meaning",
            ".card, .pillar, .bento, [data-card]",
        )

    low_occupancy_blocks = [
        block
        for block in result.get("blocks", [])
        if float(block.get("occupancy") or 0) < 0.18
        and float(block.get("areaRatio") or 0) > 0.04
    ]
    if len(low_occupancy_blocks) >= 2:
        add_issue(
            errors,
            "empty-blocks",
            f"{len(low_occupancy_blocks)} large primary blocks have less than 18% encoded occupancy",
            "[data-primary-block]",
        )
    elif low_occupancy_blocks:
        add_issue(
            warnings,
            "empty-block",
            "A large primary block has less than 18% encoded occupancy",
            "[data-primary-block]",
        )

    primary_blocks = int(result.get("primaryBlocks", 0))
    if primary_blocks < 1 or primary_blocks > 8:
        add_issue(
            errors,
            "primary-block-count",
            f"Primary visual blocks must be between 1 and 8; found {primary_blocks}",
            "[data-primary-block]",
        )
    elif primary_blocks > 5:
        add_issue(
            warnings,
            "primary-block-count",
            f"More than five primary blocks needs a clear shared scale; found {primary_blocks}",
            "[data-primary-block]",
        )

    full_text = str(result.get("text", ""))
    if PLACEHOLDER.search(full_text):
        add_issue(
            errors,
            "placeholder-copy",
            "Visible placeholder or demonstration copy remains in the poster",
            ".poster",
        )
    if EMOJI.search(full_text):
        add_issue(
            errors,
            "emoji",
            "Emoji detected; use a restrained icon or typographic label",
            ".poster",
        )

    text_limits = {
        "title": (28, 42),
        "recommendation": (36, 56),
        "label": (12, 20),
        "description": (32, 56),
        "annotation": (18, 28),
    }
    for item in result.get("audited", []):
        kind = str(item.get("kind", ""))
        text_value = str(item.get("text", "")).strip()
        units = semantic_units(text_value)
        if not text_value:
            add_issue(errors, "empty-copy", f"Empty audited {kind}", f"[data-audit='{kind}']")
        if kind in text_limits:
            recommended, hard = text_limits[kind]
            if units > hard:
                add_issue(
                    errors,
                    f"{kind}-length",
                    f"{kind} has {units} semantic units; hard ceiling is {hard}",
                    f"[data-audit='{kind}']",
                )
            elif units > recommended:
                add_issue(
                    warnings,
                    f"{kind}-length",
                    f"{kind} has {units} semantic units; recommended maximum is {recommended}",
                    f"[data-audit='{kind}']",
                )
        if item.get("outside"):
            add_issue(
                errors,
                "out-of-bounds",
                f"Content extends beyond the poster: {text_value[:80]}",
                f"[data-audit='{kind}']",
            )
        font_size = float(item.get("fontSize") or 0)
        minimum_font_size = 10 if kind in {"source", "attribution"} else 11
        if font_size < minimum_font_size:
            add_issue(
                errors,
                "font-size",
                f"Audited text is {font_size:.1f}px; minimum is {minimum_font_size}px",
                f"[data-audit='{kind}']",
            )
        contrast = item.get("contrast")
        if isinstance(contrast, (int, float)):
            threshold = 3.0 if font_size >= 24 else 4.5
            if contrast + 0.01 < threshold:
                add_issue(
                    errors,
                    "contrast",
                    f"Contrast ratio {contrast:.2f}:1 is below {threshold:.1f}:1",
                    f"[data-audit='{kind}']",
                )

    for container in result.get("containers", []):
        if container.get("overflow"):
            add_issue(
                errors,
                "container-overflow",
                f"Content overflows {container.get('name')}: "
                f"{str(container.get('text', ''))[:80]}",
                str(container.get("name", "")),
            )
        if container.get("outside"):
            add_issue(
                errors,
                "container-out-of-bounds",
                f"{container.get('name')} extends beyond the poster canvas",
                str(container.get("name", "")),
            )

    total_limits = {"4:5": 620, "16:9": 560, "1:1": 480, "A4": 760}
    total_units = semantic_units(full_text)
    encoded_copy_allowance = min(int(result.get("dataPoints", 0)) * 5, 150)
    effective_copy_limit = total_limits[aspect] + encoded_copy_allowance
    if total_units > effective_copy_limit:
        add_issue(
            warnings,
            "copy-density",
            f"Poster has {total_units} semantic units; target maximum is "
            f"{effective_copy_limit} for {aspect} after encoded-mark allowance",
            ".poster",
        )

    images = result.get("images", [])
    for index, image in enumerate(images):
        if not image.get("complete") or int(image.get("naturalWidth") or 0) <= 0:
            add_issue(
                errors,
                "broken-image",
                f"Image {index + 1} did not load",
                f".poster img:nth-of-type({index + 1})",
            )
        if not str(image.get("alt", "")).strip():
            add_issue(
                warnings,
                "missing-alt",
                f"Image {index + 1} has no alt text",
                f".poster img:nth-of-type({index + 1})",
            )

    logo_images = [
        image for image in images if str(image.get("src", "")).startswith("data:image/")
    ]
    if result.get("brandLogoCount") == 1 and not logo_images:
        add_issue(
            errors,
            "logo-portability",
            "Brand logo must be embedded as a data URL in the generated project",
            ".brand-lockup img",
        )

    image_info: Optional[Dict[str, Any]] = None
    if args.image:
        image_path = expand_path(args.image)
        image_width, image_height = png_dimensions(image_path)
        image_info = {
            "path": report_path_value(image_path, report_path),
            "width": image_width,
            "height": image_height,
        }
        if (
            image_width % expected_width != 0
            or image_height % expected_height != 0
            or image_width // expected_width != image_height // expected_height
        ):
            add_issue(
                errors,
                "png-size",
                f"PNG is {image_width}x{image_height}; expected an integer scale "
                f"of {expected_width}x{expected_height}",
            )
        else:
            image_info["scale"] = image_width // expected_width

    quality_proxy = professional_proxy_score(
        result,
        result.get("audited", []),
        errors,
        warnings,
        contract_passed,
    )
    if int(quality_proxy["total"]) < int(quality_proxy["threshold"]):
        add_issue(
            warnings,
            "professional-score",
            "Machine proxy score is "
            f"{quality_proxy['total']}/{quality_proxy['threshold']}; "
            "revise evidence, encoding, density, or annotations",
            ".poster",
        )
    if quality_proxy["critical_failures"]:
        add_issue(
            warnings,
            "critical-dimension",
            "Critical quality dimension(s) below minimum: "
            + ", ".join(quality_proxy["critical_failures"]),
            ".poster",
        )

    if args.human_review == "pending":
        add_issue(
            warnings,
            "human-review-pending",
            "Rendered-image review is still pending",
            ".poster",
        )
    elif args.human_review == "failed":
        add_issue(
            errors,
            "human-review-failed",
            args.review_note or "Rendered image failed human visual review",
            ".poster",
        )
    elif not args.image:
        add_issue(
            errors,
            "human-review-image",
            "A passed human review requires --image so the reviewed artifact is explicit",
            ".poster",
        )
    elif semantic_units(args.review_note or "") < 8:
        add_issue(
            errors,
            "human-review-note",
            "A passed human review requires a specific --review-note "
            "covering the argument, visual encoding, and legibility",
            ".poster",
        )

    report: Dict[str, Any] = {
        "schema_version": 3,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "input": report_path_value(input_path, report_path),
        "aspect": aspect,
        "canvas": {"width": expected_width, "height": expected_height},
        "image": image_info,
        "metrics": {
            "primary_blocks": primary_blocks,
            "semantic_units": total_units,
            "audited_elements": len(result.get("audited", [])),
            "images": len(images),
            "template": template_name,
            "evidence_mode": evidence_mode,
            "title_mode": title_mode,
            "recommendation_count": recommendation_count,
            "header_area_ratio": round(header_ratio, 4),
            "visual_area_ratio": round(visual_ratio, 4),
            "footer_area_ratio": round(float(result.get("footerAreaRatio") or 0), 4),
            "card_area_ratio": round(card_area_ratio, 4),
            "data_points": int(result.get("dataPoints", 0)),
            "annotations": int(result.get("annotations", 0)),
            "source_refs": int(result.get("sourceRefs", 0)),
            "decision_markers": int(result.get("decisionMarkers", 0)),
            "encodings": encodings,
            "low_occupancy_blocks": len(low_occupancy_blocks),
        },
        "quality_proxy": quality_proxy,
        "human_review": {
            "required": True,
            "status": args.human_review,
            "note": args.review_note
            or (
                "Automatic audit cannot judge whether the argument is true, "
                "the title is insightful, or the visual feels commissioned."
            ),
        },
        "errors": errors,
        "warnings": warnings,
        "status": "fail" if errors or (args.strict and warnings) else "pass",
        "strict": bool(args.strict),
    }

    if report_path:
        write_json(report_path, report)

    print(
        f"Audit {report['status'].upper()}: "
        f"{len(errors)} error(s), {len(warnings)} warning(s), "
        f"quality proxy {quality_proxy['total']}/100"
    )
    for label, issues in (("ERROR", errors), ("WARN", warnings)):
        for issue in issues:
            selector = f" [{issue['selector']}]" if issue.get("selector") else ""
            print(f"{label} {issue['code']}: {issue['message']}{selector}")

    if errors:
        return 2
    if args.strict and warnings:
        return 1
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description="Create, render, and audit professional infographic projects."
    )
    subparsers = root.add_subparsers(dest="command", required=True)

    brand_parser = subparsers.add_parser(
        "init-brand",
        help="Create a portable user brand profile.",
    )
    brand_parser.add_argument("--name", required=True, help="Brand name.")
    brand_parser.add_argument("--logo", required=True, help="SVG, PNG, JPEG, or WebP logo.")
    brand_parser.add_argument("--site", default="", help="Brand website.")
    brand_parser.add_argument("--primary", default="#24324A")
    brand_parser.add_argument("--accent", default="#4F46E5")
    brand_parser.add_argument("--ink", default="#172033")
    brand_parser.add_argument("--muted", default="#697386")
    brand_parser.add_argument("--paper", default="#F7F4EF")
    brand_parser.add_argument(
        "--font-family",
        default="Inter, PingFang SC, Hiragino Sans GB, Microsoft YaHei, sans-serif",
    )
    brand_parser.add_argument("--copyright", help="Attribution printed on every image.")
    brand_parser.add_argument("--output-dir", help="Default infographic output directory.")
    brand_parser.add_argument("--output", help="Brand-profile JSON path.")
    brand_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing profile.",
    )
    brand_parser.set_defaults(handler=init_brand)

    scaffold_parser = subparsers.add_parser(
        "scaffold",
        help="Create a non-destructive editable infographic project.",
    )
    scaffold_parser.add_argument(
        "--title",
        required=True,
        help="Display title; describe the subject/purpose in topic mode or the conclusion in action mode.",
    )
    scaffold_parser.add_argument(
        "--title-mode",
        choices=("topic", "action"),
        default="topic",
        help=(
            "topic (default) puts subject/purpose in the header and advice at the tail; "
            "action uses a conclusion-first title without a separate recommendation band."
        ),
    )
    scaffold_parser.add_argument(
        "--recommendation",
        help="Evidence-backed tail advice for topic mode.",
    )
    scaffold_parser.add_argument("--source", help="UTF-8 source Markdown/text file.")
    scaffold_parser.add_argument(
        "--aspect",
        choices=list(CANVASES),
        default="16:9",
        help="16:9 is the default consulting Exhibit; other ratios are derivatives.",
    )
    scaffold_parser.add_argument(
        "--template",
        choices=TEMPLATE_NAMES,
        required=True,
        help="Semantic Exhibit template selected from the source relationship.",
    )
    scaffold_parser.add_argument(
        "--mode",
        choices=("qualitative", "quantitative", "mixed"),
        required=True,
        help="Evidence mode; controls required units and source semantics.",
    )
    scaffold_parser.add_argument(
        "--output-dir",
        help="Exact project directory; must be empty or absent.",
    )
    scaffold_parser.add_argument("--brand-profile", help="Brand-profile JSON path.")
    scaffold_parser.set_defaults(handler=scaffold)

    render_parser = subparsers.add_parser(
        "render",
        help="Render .poster from HTML to a high-resolution PNG.",
    )
    render_parser.add_argument("--input", required=True, help="poster.html path.")
    render_parser.add_argument("--output", required=True, help="Output .png path.")
    render_parser.add_argument("--scale", type=int, choices=(1, 2, 3), default=2)
    render_parser.add_argument("--timeout", type=int, default=15000, help="Timeout in ms.")
    render_parser.set_defaults(handler=render)

    audit_parser = subparsers.add_parser(
        "audit",
        help="Audit structure, copy budgets, overflow, contrast, assets, and PNG size.",
    )
    audit_parser.add_argument("--input", required=True, help="poster.html path.")
    audit_parser.add_argument("--image", help="Rendered PNG path to verify.")
    audit_parser.add_argument("--report", help="Write JSON audit report.")
    audit_parser.add_argument("--timeout", type=int, default=15000, help="Timeout in ms.")
    audit_parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat editorial warnings as a non-zero result.",
    )
    audit_parser.add_argument(
        "--human-review",
        choices=("pending", "passed", "failed"),
        default="pending",
        help="Record rendered-image review status; strict release requires passed.",
    )
    audit_parser.add_argument(
        "--review-note",
        help="Concise evidence from the rendered-image review.",
    )
    audit_parser.set_defaults(handler=audit)
    return root


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except CliError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("error: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
