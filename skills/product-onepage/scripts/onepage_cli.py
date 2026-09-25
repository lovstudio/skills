#!/usr/bin/env python3
"""Scaffold, render, and audit brand-led product OnePage posters."""

from __future__ import annotations

import argparse
import base64
import html as html_lib
import json
import mimetypes
import os
import re
import shutil
import struct
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT / "assets"
DEFAULT_BRAND = ASSETS_DIR / "brand-profile.template.json"
DEFAULT_USER_BRAND = Path("${SKILLS_CONFIG_DIR}/product-onepage-brand.json")
TEMPLATE_PATH = ASSETS_DIR / "onepage-template.html"

ASPECTS: Dict[str, Tuple[int, int]] = {
    "4:5": (1080, 1350),
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
    "16:9": (1600, 900),
    "a4": (1240, 1754),
}
LAYOUTS = (
    "launch-story",
    "problem-solution",
    "product-tour",
    "proof-led",
    "comparison",
    "event-launch",
)
STYLES = (
    "editorial-tech",
    "product-stage",
    "bold-launch",
    "premium-minimal",
    "warm-human",
    "technical-grid",
)
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
COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
PLACEHOLDER_RE = re.compile(
    r"\{\{|\[TODO|\bTODO\b|PLACEHOLDER|待补充|替换这里|核心能力[一二三]",
    re.IGNORECASE,
)
VAGUE_CTA = {"提交", "了解更多", "探索更多", "点击这里", "开始", "继续", "more"}


class CliError(RuntimeError):
    """Expected command-line failure with a concise user-facing message."""


def expand_path(value: str, base: Optional[Path] = None) -> Path:
    expanded = os.path.expandvars(os.path.expanduser(value))
    path = Path(expanded)
    if not path.is_absolute() and base is not None:
        path = base / path
    return path.resolve()


def read_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CliError(f"JSON file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CliError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CliError(f"JSON root must be an object: {path}")
    return value


def write_json(path: Path, value: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def shared_profile_path() -> Path:
    return expand_path(
        os.environ.get(
            "SKILL_PROFILE_PATH",
            "${SKILLS_CONFIG_DIR}/profile.json",
        )
    )


def configured_brand_path(explicit: Optional[str]) -> Path:
    candidates: List[Tuple[str, Optional[str]]] = [
        ("CLI", explicit),
        (
            "SKILL_PRODUCT_ONEPAGE_BRAND_PROFILE",
            os.environ.get("SKILL_PRODUCT_ONEPAGE_BRAND_PROFILE"),
        ),
        (
            "SKILL_PROFILE_PATH",
            os.environ.get("SKILL_PROFILE_PATH"),
        ),
    ]
    for label, value in candidates:
        if value:
            path = expand_path(value)
            if not path.exists():
                raise CliError(f"{label} brand profile does not exist: {path}")
            return path

    profile_path = shared_profile_path()
    if profile_path.exists():
        profile = read_json(profile_path)
        brand = profile.get("brand")
        if isinstance(brand, dict) and brand.get("profile"):
            path = expand_path(str(brand["profile"]), profile_path.parent)
            if path.exists():
                return path
            raise CliError(f"Shared profile points to a missing brand profile: {path}")

    return DEFAULT_BRAND


def validate_color(value: str, field: str) -> str:
    if not COLOR_RE.match(value):
        raise CliError(f"Brand field {field} must use six-digit hex color syntax")
    return value.upper()


def load_brand(explicit: Optional[str]) -> Tuple[Path, Dict[str, Any], Path]:
    profile_path = configured_brand_path(explicit)
    brand = read_json(profile_path)
    missing = [field for field in REQUIRED_BRAND_FIELDS if not brand.get(field)]
    if missing:
        raise CliError(f"Brand profile is missing: {', '.join(missing)}")
    for field in ("primary", "accent", "ink", "muted", "paper"):
        brand[field] = validate_color(str(brand[field]), field)
    logo = expand_path(str(brand["logo"]), profile_path.parent)
    if not logo.exists():
        raise CliError(f"Brand Logo does not exist: {logo}")
    return profile_path, brand, logo


def data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    content = path.read_bytes()
    if mime == "image/svg+xml":
        encoded = base64.b64encode(content).decode("ascii")
        return f"data:image/svg+xml;base64,{encoded}"
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def safe_font_family(value: str) -> str:
    value = re.sub(r"[{};<>]", "", value).strip()
    return value or "Inter, PingFang SC, Microsoft YaHei, sans-serif"


def semantic_units(value: str) -> int:
    cjk = len(re.findall(r"[\u3400-\u9fff\uf900-\ufaff]", value))
    latin = len(re.findall(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*", value))
    return cjk + latin


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:64] or "product-onepage"


def parse_feature(value: str) -> Tuple[str, str]:
    parts = [part.strip() for part in value.split("|", 1)]
    if len(parts) != 2 or not all(parts):
        raise CliError('--feature must use "Title|Explanation"')
    return parts[0], parts[1]


def parse_proof(value: str) -> Tuple[str, str, str]:
    parts = [part.strip() for part in value.split("|", 2)]
    if len(parts) != 3 or not all(parts):
        raise CliError('--proof must use "Claim|Evidence detail|S1"')
    if not re.fullmatch(r"S[1-9][0-9]*", parts[2]):
        raise CliError("Proof source ID must use S1, S2, and similar syntax")
    return parts[0], parts[1], parts[2]


def render_template(template: str, replacements: Dict[str, str]) -> str:
    result = template
    for key, value in replacements.items():
        result = result.replace("{{" + key + "}}", value)
    unresolved = sorted(set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", result)))
    if unresolved:
        raise CliError(f"Template has unresolved fields: {', '.join(unresolved)}")
    return result


def init_brand(args: argparse.Namespace) -> int:
    output = expand_path(args.output or str(DEFAULT_USER_BRAND))
    if output.exists() and not args.force:
        raise CliError(f"Brand profile already exists: {output}; use --force to replace it")
    logo = expand_path(args.logo)
    if not logo.exists():
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
        "copyright": args.copyright or f"Generated by {args.name}",
        "output_dir": args.output_dir or "$HOME/Documents/product-onepage",
    }
    write_json(output, brand)
    print(f"Brand profile created: {output}")
    return 0


def feature_html(features: Sequence[Tuple[str, str]]) -> str:
    return "\n".join(
        f'''<article class="feature" data-role="feature">
          <h2 data-audit="feature-title">{html_lib.escape(title)}</h2>
          <p data-audit="feature-detail">{html_lib.escape(detail)}</p>
        </article>'''
        for title, detail in features
    )


def proof_html(proofs: Sequence[Tuple[str, str, str]]) -> str:
    return "\n".join(
        f'''<article class="proof" data-role="proof" data-source-ref="{html_lib.escape(source_id)}">
          <p class="proof__claim" data-audit="proof-claim">{html_lib.escape(claim)}</p>
          <p class="proof__detail" data-audit="proof-detail">{html_lib.escape(detail)}</p>
          <span class="proof__source">{html_lib.escape(source_id)}</span>
        </article>'''
        for claim, detail, source_id in proofs
    )


def concept_visual(title: str) -> str:
    short_title = title if semantic_units(title) <= 12 else "Product system"
    return f'''<div class="concept-stage" data-authenticity="conceptual">
        <div class="concept-stage__bar"><span>{html_lib.escape(short_title)}</span><span>01 / ONEPAGE</span></div>
        <div class="concept-stage__body">
          <div class="concept-stage__index">01</div>
          <div class="concept-stage__flow">
            <div class="concept-stage__step"><span>01</span>输入真实意图</div>
            <div class="concept-stage__step"><span>02</span>产品机制发生</div>
            <div class="concept-stage__step"><span>03</span>获得可见结果</div>
          </div>
        </div>
      </div>'''


def product_visual(args: argparse.Namespace) -> Tuple[str, str]:
    if not args.hero_image:
        return concept_visual(args.title), "conceptual"
    path = expand_path(args.hero_image)
    if not path.exists():
        raise CliError(f"Hero image does not exist: {path}")
    if not args.hero_alt:
        raise CliError("--hero-alt is required with --hero-image")
    generated = args.product_authenticity == "synthetic"
    flags = (
        ' data-generated="true" data-text-free="true"'
        if generated
        else ""
    )
    markup = (
        f'<img src="{data_url(path)}" alt="{html_lib.escape(args.hero_alt)}"'
        f' data-authenticity="{html_lib.escape(args.product_authenticity)}"{flags}>'
    )
    return markup, args.product_authenticity


def output_root(brand: Dict[str, Any]) -> Path:
    for env_name in (
        "SKILL_PRODUCT_ONEPAGE_OUTPUT_DIR",
        "SKILL_OUTPUT_DIR",
    ):
        value = os.environ.get(env_name)
        if value:
            return expand_path(value)
    return expand_path(str(brand.get("output_dir", "$HOME/Documents/product-onepage")))


def brief_markdown(
    args: argparse.Namespace,
    features: Sequence[Tuple[str, str]],
    proofs: Sequence[Tuple[str, str, str]],
    brand: Dict[str, Any],
) -> str:
    proof_lines = []
    for claim, detail, source_id in proofs:
        proof_lines.append(
            f"- {source_id}\n"
            f"  - Claim: {claim}\n"
            f"  - Exact evidence: {detail}\n"
            "  - Location: source.md\n"
            "  - Type: fact | estimate | assumption | interpretation\n"
            "  - Unit / period: n/a unless source specifies\n"
            "  - Caveat: verify against the preserved source before release"
        )
    feature_lines = "\n".join(f"- **{title}:** {detail}" for title, detail in features)
    return f"""# Product OnePage brief

## Audience and viewing moment

- Audience: {args.audience}
- Viewing moment: {args.viewing_moment}
- Market / language: {args.market} / {args.lang}

## Truth ledger

- Internal context: keep planning notes and private background in this file.
- Publishable claim: {args.title}
- Verified proof: see evidence ledger below.
- Open evidence: replace incomplete claims before strict release.

## Brand Spine

- Brand: {brand['name']}
- Category: {args.category}
- Audience tension: document from source.
- Belief: document from source.
- Promise: {args.title}
- Mechanism: {args.tagline}
- Difference: document a visible product choice.
- Proof: see evidence ledger.
- Boundary: document what the product deliberately avoids.
- Action: {args.cta_label} → {args.cta_url}

## One public thesis

{args.title}

## Headline spine

1. {args.title}
2. {args.tagline}
3. Product mechanism through the staged artifact
4. Verified proof
5. {args.cta_label}

## Supporting features

{feature_lines}

## Evidence ledger

{chr(10).join(proof_lines)}

## Layout and art direction

- Layout: {args.layout}
- Style: {args.style}
- Aspect: {args.aspect}
- Product authenticity: {args.product_authenticity if args.hero_image else 'conceptual'}

## Conversion

- CTA label: {args.cta_label}
- Destination: {args.cta_url}
- Immediate next state: verify the destination and availability before release.

## Assumptions and gaps

- Every claim retains its evidence type, date, unit, and caveat where relevant.
- Conceptual product staging is illustrative and does not count as proof.

## Deliberate omissions

- Internal planning context, unsupported rankings, synthetic testimonials, and
  claims that compete with the single public thesis.
"""


def content_markdown(
    args: argparse.Namespace,
    features: Sequence[Tuple[str, str]],
    proofs: Sequence[Tuple[str, str, str]],
) -> str:
    return "\n".join(
        [
            "# Visible OnePage copy",
            "",
            f"- Category: {args.category}",
            f"- Headline: {args.title}",
            f"- Support: {args.tagline}",
            f"- CTA: {args.cta_label}",
            f"- Destination: {args.cta_url}",
            "",
            "## Features",
            *(f"- **{title}:** {detail}" for title, detail in features),
            "",
            "## Proof",
            *(f"- **{claim}:** {detail} ({source_id})" for claim, detail, source_id in proofs),
            "",
        ]
    )


def hero_prompt(args: argparse.Namespace, brand: Dict[str, Any]) -> str:
    return f"""# Hero visual prompt

Create one supporting product-launch visual for this OnePage poster.

- Product thesis: {args.title}
- Product mechanism: {args.tagline}
- Layout: {args.layout}
- Art direction: {args.style}
- Aspect: {args.aspect}
- Palette: {brand['primary']} {brand['accent']} {brand['paper']}
- Composition: one clear focal object or scene with intentional negative space
  for HTML copy and a crop-safe silhouette at thumbnail size.

Hard constraints: no words, letters, numbers, glyphs, charts, diagrams with
labels, interface text, fake UI, logos, signatures, watermarks, decorative
particles, or generic gradient glow. The asset is illustrative and must not
represent customer, usage, metric, award, or product proof.
"""


def scaffold(args: argparse.Namespace) -> int:
    brand_path, brand, logo = load_brand(args.brand_profile)
    project_dir = (
        expand_path(args.output_dir)
        if args.output_dir
        else output_root(brand) / slugify(args.title)
    )
    project_dir.mkdir(parents=True, exist_ok=True)
    managed = (
        "onepage.html",
        "source.md",
        "brief.md",
        "content.md",
        "project.json",
    )
    occupied = [name for name in managed if (project_dir / name).exists()]
    if occupied and not args.force:
        raise CliError(
            f"Project already contains managed files: {', '.join(occupied)}; use --force"
        )

    features = [parse_feature(item) for item in (args.feature or [])]
    if not features:
        features = [
            ("核心能力一", "替换这里：产品怎样把输入变成结果。"),
            ("核心能力二", "替换这里：真实用户可感知的差异。"),
            ("核心能力三", "替换这里：与 CTA 直接相关的价值。"),
        ]
    if not 2 <= len(features) <= 4:
        raise CliError("Provide two to four --feature values")

    proofs = [parse_proof(item) for item in (args.proof or [])]
    if not proofs:
        proofs = [("待补充真实证据", "替换这里：真实产品、案例或来源。", "S1")]
    if len(proofs) > 2:
        raise CliError("The packaged scaffold supports one or two --proof values")

    visual, authenticity = product_visual(args)
    width, height = ASPECTS[args.aspect]
    if args.source:
        source_path = expand_path(args.source)
        if not source_path.exists():
            raise CliError(f"Source file does not exist: {source_path}")
        source_text = source_path.read_text(encoding="utf-8")
    else:
        source_text = "# Source\n\nPreserve the relevant product brief or current-conversation source here.\n"

    source_note = args.source_note or "来源：source.md · 证据编号见 brief.md"
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    replacements = {
        "LANG": html_lib.escape(args.lang),
        "WIDTH": str(width),
        "HEIGHT": str(height),
        "ASPECT": html_lib.escape(args.aspect),
        "LAYOUT": html_lib.escape(args.layout),
        "STYLE": html_lib.escape(args.style),
        "BRAND_PRIMARY": str(brand["primary"]),
        "BRAND_ACCENT": str(brand["accent"]),
        "BRAND_INK": str(brand["ink"]),
        "BRAND_MUTED": str(brand["muted"]),
        "BRAND_PAPER": str(brand["paper"]),
        "FONT_FAMILY": safe_font_family(str(brand["font_family"])),
        "BRAND_NAME": html_lib.escape(str(brand["name"])),
        "LOGO_DATA_URL": data_url(logo),
        "CATEGORY": html_lib.escape(args.category),
        "TITLE": html_lib.escape(args.title),
        "TAGLINE": html_lib.escape(args.tagline),
        "CTA_LABEL": html_lib.escape(args.cta_label),
        "CTA_URL": html_lib.escape(args.cta_url, quote=True),
        "CTA_URL_TEXT": html_lib.escape(args.cta_url),
        "PRODUCT_VISUAL": visual,
        "PRODUCT_AUTHENTICITY": html_lib.escape(authenticity),
        "FEATURES_HTML": feature_html(features),
        "PROOFS_HTML": proof_html(proofs),
        "SOURCE_NOTE": html_lib.escape(source_note),
        "COPYRIGHT": html_lib.escape(
            args.attribution
            or f"本海报由 {brand['name']} 的 Product OnePage Skill 生成"
        ),
    }
    poster = render_template(template, replacements)

    (project_dir / "assets").mkdir(exist_ok=True)
    (project_dir / "prompts").mkdir(exist_ok=True)
    (project_dir / "onepage.html").write_text(poster, encoding="utf-8")
    (project_dir / "source.md").write_text(source_text, encoding="utf-8")
    (project_dir / "brief.md").write_text(
        brief_markdown(args, features, proofs, brand), encoding="utf-8"
    )
    (project_dir / "content.md").write_text(
        content_markdown(args, features, proofs), encoding="utf-8"
    )
    (project_dir / "prompts" / "hero-visual.md").write_text(
        hero_prompt(args, brand), encoding="utf-8"
    )
    write_json(
        project_dir / "project.json",
        {
            "schema_version": 1,
            "title": args.title,
            "tagline": args.tagline,
            "category": args.category,
            "layout": args.layout,
            "style": args.style,
            "aspect": args.aspect,
            "canvas": {"width": width, "height": height},
            "brand_profile": str(brand_path),
            "brand_name": brand["name"],
            "cta": {"label": args.cta_label, "url": args.cta_url},
            "product_authenticity": authenticity,
            "source": "source.md",
            "brief": "brief.md",
            "content": "content.md",
            "poster": "onepage.html",
            "prompt": "prompts/hero-visual.md",
        },
    )
    print(f"Project scaffolded: {project_dir}")
    return 0


def find_chrome() -> Optional[str]:
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)
    return None


def import_playwright() -> Any:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise CliError(
            'Playwright is required: python3 -m pip install "playwright>=1.45,<2"'
        ) from exc
    return sync_playwright


def launch_browser(playwright: Any) -> Any:
    executable = find_chrome()
    options: Dict[str, Any] = {
        "headless": True,
        "args": ["--font-render-hinting=none", "--disable-web-security"],
    }
    if executable:
        options["executable_path"] = executable
    try:
        return playwright.chromium.launch(**options)
    except Exception as exc:
        raise CliError(
            "Chromium launch failed; install it with: python3 -m playwright install chromium"
        ) from exc


def detect_canvas(markup: str) -> Tuple[str, int, int]:
    tag = re.search(r'<main[^>]*class=["\'][^"\']*onepage[^"\']*["\'][^>]*>', markup)
    if not tag:
        raise CliError("onepage.html must contain one <main class=\"onepage\">")
    text = tag.group(0)
    aspect_match = re.search(r'data-aspect=["\']([^"\']+)["\']', text)
    width_match = re.search(r'data-width=["\']([0-9]+)["\']', text)
    height_match = re.search(r'data-height=["\']([0-9]+)["\']', text)
    if not aspect_match or aspect_match.group(1) not in ASPECTS:
        raise CliError(f"data-aspect must be one of: {', '.join(ASPECTS)}")
    aspect = aspect_match.group(1)
    expected_width, expected_height = ASPECTS[aspect]
    width = int(width_match.group(1)) if width_match else expected_width
    height = int(height_match.group(1)) if height_match else expected_height
    return aspect, width, height


def wait_ready(page: Any, timeout_ms: int) -> None:
    page.wait_for_function(
        "window.__PRODUCT_ONEPAGE_READY__ === true",
        timeout=timeout_ms,
    )
    page.evaluate(
        """async () => {
          if (document.fonts && document.fonts.ready) await document.fonts.ready;
          await Promise.all([...document.images].map((img) => img.complete
            ? Promise.resolve()
            : new Promise((resolve) => {
                img.addEventListener('load', resolve, {once: true});
                img.addEventListener('error', resolve, {once: true});
              })));
        }"""
    )


def render(args: argparse.Namespace) -> int:
    input_path = expand_path(args.input)
    if not input_path.exists():
        raise CliError(f"HTML input does not exist: {input_path}")
    output_path = expand_path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    markup = input_path.read_text(encoding="utf-8")
    _, width, height = detect_canvas(markup)
    sync_playwright = import_playwright()
    with sync_playwright() as playwright:
        browser = launch_browser(playwright)
        try:
            context = browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=args.scale,
            )
            page = context.new_page()
            page.goto(input_path.as_uri(), wait_until="load", timeout=args.timeout)
            wait_ready(page, args.timeout)
            locator = page.locator(".onepage")
            if locator.count() != 1:
                raise CliError("Render target must contain exactly one .onepage")
            locator.screenshot(path=str(output_path), animations="disabled")
            context.close()
        finally:
            browser.close()
    print(f"Rendered: {output_path}")
    return 0


def png_dimensions(path: Path) -> Tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise CliError(f"Image is not a valid PNG: {path}")
    return struct.unpack(">II", data[16:24])


def browser_audit(input_path: Path, timeout_ms: int) -> Dict[str, Any]:
    markup = input_path.read_text(encoding="utf-8")
    _, width, height = detect_canvas(markup)
    sync_playwright = import_playwright()
    with sync_playwright() as playwright:
        browser = launch_browser(playwright)
        try:
            context = browser.new_context(viewport={"width": width, "height": height})
            page = context.new_page()
            page.goto(input_path.as_uri(), wait_until="load", timeout=timeout_ms)
            wait_ready(page, timeout_ms)
            result = page.evaluate(
                """() => {
                  const root = document.querySelector('.onepage');
                  if (!root) return {rootCount: 0};
                  const rootRect = root.getBoundingClientRect();
                  const visible = (selector) => [...root.querySelectorAll(selector)]
                    .filter((el) => {
                      const r = el.getBoundingClientRect();
                      const s = getComputedStyle(el);
                      return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden';
                    });
                  const count = (selector) => visible(selector).length;
                  const ratio = (selector) => {
                    const el = root.querySelector(selector);
                    if (!el) return 0;
                    const r = el.getBoundingClientRect();
                    return (r.width * r.height) / (rootRect.width * rootRect.height);
                  };
                  const rectTop = (selector) => {
                    const el = root.querySelector(selector);
                    return el ? el.getBoundingClientRect().top : null;
                  };
                  const audited = visible('[data-audit]').map((el) => {
                    const r = el.getBoundingClientRect();
                    const container = el.closest('[data-audit-container]');
                    const c = container ? container.getBoundingClientRect() : rootRect;
                    return {
                      kind: el.getAttribute('data-audit'),
                      text: (el.textContent || '').trim(),
                      width: r.width,
                      height: r.height,
                      scrollWidth: el.scrollWidth,
                      scrollHeight: el.scrollHeight,
                      containerOverflow: r.left < c.left - 2 || r.top < c.top - 2 ||
                        r.right > c.right + 2 || r.bottom > c.bottom + 2,
                    };
                  });
                  const images = visible('img').map((img) => ({
                    alt: img.getAttribute('alt'),
                    complete: img.complete,
                    naturalWidth: img.naturalWidth,
                    generated: img.getAttribute('data-generated'),
                    textFree: img.getAttribute('data-text-free'),
                    authenticity: img.getAttribute('data-authenticity'),
                  }));
                  const target = root.querySelector('[data-primary-cta]');
                  const genericCards = visible('.card, [data-card]');
                  const genericCardArea = genericCards.reduce((sum, el) => {
                    const r = el.getBoundingClientRect();
                    return sum + r.width * r.height;
                  }, 0) / (rootRect.width * rootRect.height);
                  const auditedOverflow = audited.filter((item) => item.containerOverflow).length;
                  return {
                    rootCount: document.querySelectorAll('.onepage').length,
                    layout: root.getAttribute('data-layout'),
                    style: root.getAttribute('data-style'),
                    aspect: root.getAttribute('data-aspect'),
                    width: Math.round(rootRect.width),
                    height: Math.round(rootRect.height),
                    categoryCount: count('[data-role="category"]'),
                    headlineCount: count('[data-role="headline"]'),
                    supportCount: count('[data-role="support"]'),
                    productStageCount: count('[data-role="product-stage"]'),
                    featureCount: count('[data-role="feature"]'),
                    proofCount: count('[data-role="proof"]'),
                    proofSourceCount: count('[data-role="proof"][data-source-ref]'),
                    ctaCount: count('[data-role="cta"]'),
                    primaryCtaCount: count('[data-primary-cta]'),
                    sourceCount: count('.source-note[data-audit="source"]'),
                    attributionCount: count('.generation-note[data-audit="attribution"]'),
                    brandLogoCount: count('.brand-lockup img'),
                    generatedImageCount: count('img[data-generated="true"]'),
                    generatedTextFreeCount: count('img[data-generated="true"][data-text-free="true"]'),
                    productAuthenticity: root.querySelector('[data-role="product-stage"]')?.getAttribute('data-authenticity'),
                    ctaLabel: target ? (target.textContent || '').trim() : '',
                    ctaHref: target ? target.getAttribute('href') : '',
                    placeholderCount: ((root.textContent || '').match(/\{\{|\[TODO|\bTODO\b|PLACEHOLDER|待补充|替换这里|核心能力[一二三]/gi) || []).length,
                    rootOverflow: root.scrollWidth > root.clientWidth + 2 || root.scrollHeight > root.clientHeight + 2,
                    auditedOverflow,
                    genericCardArea,
                    regionRatios: {
                      header: ratio('[data-region="header"]'),
                      hero: ratio('[data-region="hero"]'),
                      product: ratio('[data-region="product"]'),
                      proof: ratio('[data-region="proof"]'),
                      footer: ratio('[data-region="footer"]'),
                    },
                    regionTops: {
                      header: rectTop('[data-region="header"]'),
                      hero: rectTop('[data-region="hero"]'),
                      product: rectTop('[data-region="product"]'),
                      proof: rectTop('[data-region="proof"]'),
                      footer: rectTop('[data-region="footer"]'),
                    },
                    audited,
                    images,
                  };
                }"""
            )
            context.close()
            if not isinstance(result, dict):
                raise CliError("Browser audit returned an invalid result")
            return result
        finally:
            browser.close()


def add_issue(
    target: List[Dict[str, str]],
    code: str,
    message: str,
    selector: str,
) -> None:
    target.append({"code": code, "message": message, "selector": selector})


def proxy_score(result: Dict[str, Any], image_ok: bool) -> Dict[str, int]:
    brand = 0
    brand += 4 if result.get("categoryCount") == 1 else 0
    brand += 5 if result.get("headlineCount") == 1 else 0
    brand += 4 if result.get("brandLogoCount") == 1 else 0
    brand += 4 if result.get("productStageCount") == 1 else 0
    brand += 3 if result.get("placeholderCount") == 0 else 0

    story = 0
    story += 4 if result.get("supportCount") == 1 else 0
    story += 7 if result.get("productStageCount") == 1 else 0
    story += 5 if 2 <= int(result.get("featureCount", 0)) <= 4 else 0
    tops = result.get("regionTops", {})
    ordered = all(
        isinstance(tops.get(key), (int, float))
        for key in ("header", "hero", "product", "proof", "footer")
    ) and tops["header"] < tops["hero"] < tops["product"] < tops["proof"] < tops["footer"]
    story += 4 if ordered else 0

    proof = 0
    proof += 7 if int(result.get("proofCount", 0)) >= 1 else 0
    proof += 7 if result.get("proofSourceCount") == result.get("proofCount") else 0
    proof += 3 if result.get("sourceCount") == 1 else 0
    proof += 3 if result.get("placeholderCount") == 0 else 0

    conversion = 0
    conversion += 5 if result.get("primaryCtaCount") == 1 else 0
    href = str(result.get("ctaHref") or "").strip()
    conversion += 6 if href and href != "#" and not href.lower().startswith("javascript:") else 0
    label = str(result.get("ctaLabel") or "").strip().lower()
    conversion += 4 if label and label not in VAGUE_CTA else 0

    visual = 0
    visual += 5 if not result.get("rootOverflow") and int(result.get("auditedOverflow", 0)) == 0 else 0
    ratios = result.get("regionRatios", {})
    ratio_ok = (
        0.02 <= float(ratios.get("header", 0)) <= 0.12
        and 0.12 <= float(ratios.get("hero", 0)) <= 0.32
        and 0.28 <= float(ratios.get("product", 0)) <= 0.60
        and 0.10 <= float(ratios.get("proof", 0)) <= 0.28
    )
    visual += 5 if ratio_ok else 0
    visual += 3 if float(result.get("genericCardArea", 0)) <= 0.30 else 0
    images = result.get("images", [])
    images_ok = all(
        item.get("complete") and int(item.get("naturalWidth", 0)) > 0 and item.get("alt") is not None
        for item in images
    )
    generated_ok = result.get("generatedImageCount") == result.get("generatedTextFreeCount")
    visual += 2 if images_ok and generated_ok else 0

    delivery = 0
    delivery += 5 if image_ok else 0
    delivery += 2 if result.get("attributionCount") == 1 else 0
    delivery += 3 if result.get("width") and result.get("height") else 0

    return {
        "brand_and_orientation": min(20, brand),
        "story_and_product_stage": min(20, story),
        "proof_integrity": min(20, proof),
        "conversion": min(15, conversion),
        "visual_composition": min(15, visual),
        "delivery_and_ownership": min(10, delivery),
    }


def audit(args: argparse.Namespace) -> int:
    input_path = expand_path(args.input)
    if not input_path.exists():
        raise CliError(f"HTML input does not exist: {input_path}")
    result = browser_audit(input_path, args.timeout)
    errors: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []

    if result.get("rootCount") != 1:
        add_issue(errors, "root-count", "Exactly one .onepage root is required", ".onepage")
    if result.get("layout") not in LAYOUTS:
        add_issue(errors, "layout", f"data-layout must be one of: {', '.join(LAYOUTS)}", ".onepage")
    if result.get("style") not in STYLES:
        add_issue(errors, "style", f"data-style must be one of: {', '.join(STYLES)}", ".onepage")
    if result.get("aspect") not in ASPECTS:
        add_issue(errors, "aspect", f"data-aspect must be one of: {', '.join(ASPECTS)}", ".onepage")

    required_counts = {
        "categoryCount": (1, "[data-role='category']", "category"),
        "headlineCount": (1, "[data-role='headline']", "headline"),
        "supportCount": (1, "[data-role='support']", "supporting line"),
        "productStageCount": (1, "[data-role='product-stage']", "product stage"),
        "primaryCtaCount": (1, "[data-primary-cta]", "primary CTA"),
        "sourceCount": (1, ".source-note[data-audit='source']", "source note"),
        "attributionCount": (1, ".generation-note[data-audit='attribution']", "attribution"),
        "brandLogoCount": (1, ".brand-lockup img", "brand Logo"),
    }
    for key, (expected, selector, label) in required_counts.items():
        if result.get(key) != expected:
            add_issue(errors, f"{key}-count", f"Exactly one visible {label} is required", selector)

    feature_count = int(result.get("featureCount", 0))
    if not 2 <= feature_count <= 4:
        add_issue(errors, "feature-count", "Use two to four supporting features", "[data-role='feature']")
    proof_count = int(result.get("proofCount", 0))
    if proof_count < 1:
        add_issue(errors, "proof-count", "At least one visible proof item is required", "[data-role='proof']")
    if result.get("proofSourceCount") != proof_count:
        add_issue(errors, "proof-source", "Every proof item must map to data-source-ref", "[data-role='proof']")

    if int(result.get("placeholderCount", 0)):
        add_issue(errors, "placeholder-copy", "Replace all scaffold placeholder copy", ".onepage")
    href = str(result.get("ctaHref") or "").strip()
    if not href or href == "#" or href.lower().startswith("javascript:"):
        add_issue(errors, "cta-target", "Primary CTA needs a real destination", "[data-primary-cta]")
    label = str(result.get("ctaLabel") or "").strip()
    if not label or label.lower() in VAGUE_CTA:
        add_issue(errors, "cta-label", "CTA label must name the concrete next state", "[data-primary-cta]")

    for item in result.get("audited", []):
        text = str(item.get("text") or "").strip()
        kind = str(item.get("kind") or "copy")
        if not text:
            add_issue(errors, "empty-copy", f"Audited {kind} is empty", f"[data-audit='{kind}']")
        if item.get("containerOverflow"):
            add_issue(errors, "copy-overflow", f"Audited {kind} overflows its box", f"[data-audit='{kind}']")
        units = semantic_units(text)
        ceilings = {
            "category": 16,
            "headline": 36,
            "support": 56,
            "feature-title": 16,
            "feature-detail": 36,
            "proof-claim": 28,
        }
        if kind in ceilings and units > ceilings[kind]:
            add_issue(warnings, "copy-length", f"{kind} has {units} semantic units; target ≤ {ceilings[kind]}", f"[data-audit='{kind}']")

    if result.get("rootOverflow") or int(result.get("auditedOverflow", 0)):
        add_issue(errors, "overflow", "Canvas or audited content overflows", ".onepage")
    if float(result.get("genericCardArea", 0)) > 0.30:
        add_issue(errors, "card-wall", "Generic card containers occupy too much canvas area", ".card, [data-card]")
    if result.get("generatedImageCount") != result.get("generatedTextFreeCount"):
        add_issue(errors, "generated-text-contract", "Generated images must declare data-text-free=true", "img[data-generated='true']")
    for image in result.get("images", []):
        if image.get("alt") is None:
            add_issue(errors, "image-alt", "Every image needs an alt attribute", "img")
        if not image.get("complete") or int(image.get("naturalWidth", 0)) <= 0:
            add_issue(errors, "image-load", "Every image must load before release", "img")

    ratios = result.get("regionRatios", {})
    expected_ranges = {
        "header": (0.02, 0.12),
        "hero": (0.12, 0.32),
        "product": (0.28, 0.60),
        "proof": (0.10, 0.28),
    }
    for region, (low, high) in expected_ranges.items():
        value = float(ratios.get(region, 0))
        if not low <= value <= high:
            add_issue(warnings, "region-ratio", f"{region} area ratio {value:.3f} is outside {low:.2f}–{high:.2f}", f"[data-region='{region}']")

    image_ok = False
    image_dimensions: Optional[Tuple[int, int]] = None
    if args.image:
        image_path = expand_path(args.image)
        if not image_path.exists():
            add_issue(errors, "png-missing", f"Rendered PNG does not exist: {image_path}", "image")
        else:
            image_dimensions = png_dimensions(image_path)
            expected_w = int(result.get("width", 0))
            expected_h = int(result.get("height", 0))
            iw, ih = image_dimensions
            image_ok = (
                expected_w > 0
                and expected_h > 0
                and iw >= expected_w
                and ih >= expected_h
                and abs(iw / ih - expected_w / expected_h) < 0.002
            )
            if not image_ok:
                add_issue(errors, "png-dimensions", f"PNG {iw}×{ih} does not match canvas ratio/minimum {expected_w}×{expected_h}", "image")
    else:
        add_issue(warnings, "png-unchecked", "Provide --image for dimension and release checks", "image")

    dimensions = proxy_score(result, image_ok)
    score = sum(dimensions.values())
    critical_floors = {
        "brand_and_orientation": 16,
        "story_and_product_stage": 14,
        "proof_integrity": 12,
        "conversion": 12,
        "visual_composition": 10,
    }
    for name, minimum in critical_floors.items():
        if dimensions[name] < minimum:
            add_issue(errors, "critical-floor", f"{name} score {dimensions[name]} is below {minimum}", name)
    if score < 85:
        add_issue(errors, "quality-score", f"Machine proxy score {score} is below 85", "quality")

    human_status = args.human_review or "pending"
    review_note = (args.review_note or "").strip()
    if args.strict:
        if human_status != "passed":
            add_issue(errors, "human-review", "Strict release requires --human-review passed", "human-review")
        if not args.image or semantic_units(review_note) < 10:
            add_issue(errors, "review-note", "Strict release requires a specific original-size and thumbnail review note", "human-review")

    report = {
        "schema_version": 1,
        "input": str(input_path),
        "image": str(expand_path(args.image)) if args.image else None,
        "image_dimensions": list(image_dimensions) if image_dimensions else None,
        "layout": result.get("layout"),
        "style": result.get("style"),
        "aspect": result.get("aspect"),
        "score": score,
        "dimensions": dimensions,
        "threshold": 85,
        "human_review": {"status": human_status, "note": review_note},
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            key: value
            for key, value in result.items()
            if key not in {"audited", "images"}
        },
        "release_ready": not errors and (not args.strict or human_status == "passed"),
        "limits": [
            "Machine audit does not establish claim truth, brand distinctiveness, taste, or CTA availability.",
            "Human review must inspect the exact rendered PNG at original and thumbnail sizes.",
        ],
    }
    report_path = expand_path(args.report)
    write_json(report_path, report)
    print(f"Audit report: {report_path}")
    print(f"Score: {score}/100 · errors: {len(errors)} · warnings: {len(warnings)}")
    return 1 if errors else 0


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(
        description="Create, render, and audit product OnePage promotional posters."
    )
    subparsers = cli.add_subparsers(dest="command", required=True)

    brand = subparsers.add_parser("init-brand", help="Create a portable brand profile")
    brand.add_argument("--name", required=True)
    brand.add_argument("--logo", required=True)
    brand.add_argument("--site", default="")
    brand.add_argument("--primary", default="#24324A")
    brand.add_argument("--accent", default="#EB6637")
    brand.add_argument("--ink", default="#172033")
    brand.add_argument("--muted", default="#667085")
    brand.add_argument("--paper", default="#F7F4EF")
    brand.add_argument(
        "--font-family",
        default="Inter, PingFang SC, Microsoft YaHei, sans-serif",
    )
    brand.add_argument("--copyright")
    brand.add_argument("--output-dir")
    brand.add_argument("--output")
    brand.add_argument("--force", action="store_true")
    brand.set_defaults(handler=init_brand)

    scaffold_parser = subparsers.add_parser("scaffold", help="Create an auditable OnePage project")
    scaffold_parser.add_argument("--title", required=True)
    scaffold_parser.add_argument("--tagline", required=True)
    scaffold_parser.add_argument("--category", default="Product launch")
    scaffold_parser.add_argument("--audience", default="People evaluating the product")
    scaffold_parser.add_argument("--viewing-moment", default="Social feed or launch share")
    scaffold_parser.add_argument("--market", choices=("domestic", "overseas", "mixed"), default="domestic")
    scaffold_parser.add_argument("--lang", default="zh-CN")
    scaffold_parser.add_argument("--cta-label", required=True)
    scaffold_parser.add_argument("--cta-url", required=True)
    scaffold_parser.add_argument("--source")
    scaffold_parser.add_argument("--source-note")
    scaffold_parser.add_argument("--attribution")
    scaffold_parser.add_argument("--layout", choices=LAYOUTS, default="launch-story")
    scaffold_parser.add_argument("--style", choices=STYLES, default="editorial-tech")
    scaffold_parser.add_argument("--aspect", choices=tuple(ASPECTS), default="4:5")
    scaffold_parser.add_argument("--feature", action="append")
    scaffold_parser.add_argument("--proof", action="append")
    scaffold_parser.add_argument("--hero-image")
    scaffold_parser.add_argument("--hero-alt")
    scaffold_parser.add_argument(
        "--product-authenticity",
        choices=("real", "conceptual", "synthetic"),
        default="real",
    )
    scaffold_parser.add_argument("--brand-profile")
    scaffold_parser.add_argument("--output-dir")
    scaffold_parser.add_argument("--force", action="store_true")
    scaffold_parser.set_defaults(handler=scaffold)

    render_parser = subparsers.add_parser("render", help="Render onepage.html to PNG")
    render_parser.add_argument("--input", required=True)
    render_parser.add_argument("--output", required=True)
    render_parser.add_argument("--scale", type=int, choices=(1, 2, 3), default=2)
    render_parser.add_argument("--timeout", type=int, default=30000)
    render_parser.set_defaults(handler=render)

    audit_parser = subparsers.add_parser("audit", help="Audit semantic and rendered quality")
    audit_parser.add_argument("--input", required=True)
    audit_parser.add_argument("--image")
    audit_parser.add_argument("--report", required=True)
    audit_parser.add_argument("--human-review", choices=("passed", "failed", "pending"))
    audit_parser.add_argument("--review-note")
    audit_parser.add_argument("--strict", action="store_true")
    audit_parser.add_argument("--timeout", type=int, default=30000)
    audit_parser.set_defaults(handler=audit)
    return cli


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except CliError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
