#!/usr/bin/env python3
"""Deterministic lint for investor BP outlines.

The audit checks structure and evidence hygiene. It intentionally does not pretend
to replace investor judgment or visual inspection. Only `## Slide NN — …` sections
are scored: version notes and other preamble text never reach a slide.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Pattern, Sequence, Tuple


# Matched against slide titles only. Body text mentions other topics, including
# negations such as "不设融资页", so it cannot show that a page answers the question.
BEATS: Sequence[Tuple[str, Tuple[str, ...]]] = (
    (
        "product definition",
        ("product definition", "who you are", "who we are", "what we do", "company overview",
         "定位", "你是谁", "我们是谁", "是什么", "一句话", "公司简介", "公司介绍"),
    ),
    ("problem", ("problem", "pain", "问题", "痛点")),
    ("solution", ("solution", "how the product solves", "how it works", "解决方案", "如何解决")),
    (
        "product demo",
        ("demo", "product:", "core experience", "product experience", "product tour",
         "产品：", "产品:", "产品演示", "产品展示", "产品介绍", "产品体验", "核心体验"),
    ),
    (
        "why now",
        ("why now", "why-now", "timing", "为什么现在", "为什么是现在", "为何现在", "为何是现在",
         "时机", "窗口期"),
    ),
    (
        "traction",
        ("traction", "validation", "metrics", "progress", "proof point",
         "验证", "进展", "留存", "运营数据", "关键数据", "核心数据", "业务数据", "业绩"),
    ),
    (
        "business model",
        ("business model", "revenue model", "monetization", "pricing",
         "商业模式", "收入模式", "盈利模式", "变现", "定价"),
    ),
    (
        "market",
        ("market", "tam", "sam", "som", "市场规模", "市场空间", "市场机会", "目标市场", "赛道", "切入路径"),
    ),
    ("competition", ("competition", "competitive", "competitor", "alternatives", "竞争", "竞品", "差异化")),
    (
        "growth",
        ("growth", "go-to-market", "gtm", "acquisition", "roadmap", "增长", "获客", "推广", "路线图"),
    ),
    ("team", ("team", "founder", "团队", "创始人", "管理层")),
    (
        "financing",
        ("financing", "fundraise", "fundraising", "funding", "the ask", "raise", "raising",
         "use of funds", "融资", "资金用途"),
    ),
)

PLACEHOLDER_RE = re.compile(r"\b(?:TODO|TBD|FIXME|XXX)\b|待补|待确认|missing", re.IGNORECASE)
SLIDE_RE = re.compile(r"^##\s+(?:Slide\s+)?(\d+)(?:\s+of\s+\d+)?\b(.*)$", re.IGNORECASE | re.MULTILINE)
SLIDE_ZH_RE = re.compile(r"^##\s*第\s*(\d+)\s*页(.*)$", re.MULTILINE)
SECTION_RE = re.compile(r"^#{1,2}\s", re.MULTILINE)
TITLE_PREFIX = " \t—–-:：.、|·"
HEADLINE_RE = re.compile(r"^(?:Headline|Title|标题|结论)\s*[:：]\s*(.+)$", re.IGNORECASE | re.MULTILINE)
EVIDENCE_RE = re.compile(r"^(?:Evidence|Source|Sources|证据|来源)\s*[:：]\s*(.+)$", re.IGNORECASE | re.MULTILINE)
VISUAL_RE = re.compile(r"^(?:Visual|Chart|图表|视觉)\s*[:：]\s*(.+)$", re.IGNORECASE | re.MULTILINE)
DEFINITION_RE = re.compile(r"^(?:Definition|定义|一句话定义|产品定义)\s*[:：]", re.IGNORECASE | re.MULTILINE)
AMOUNT_RE = re.compile(
    r"(?:[¥￥$€£]|\b(?:RMB|USD|CNY)\b)\s*\d|\d[\d,.]*\s*(?:万|亿|元|美元|million|billion|[KMB]\b)",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit a 12–15 slide investor BP outline.")
    parser.add_argument("--input", required=True, help="outline.md or a workspace containing it")
    parser.add_argument("--output", help="Markdown/JSON report path")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--min-slides", type=int, default=12)
    parser.add_argument("--max-slides", type=int, default=15)
    parser.add_argument("--strict", action="store_true", help="Exit 1 below 85 or with blockers")
    return parser.parse_args()


def resolve_input(raw: str) -> Path:
    path = Path(raw).expanduser().resolve()
    if path.is_dir():
        path = path / "outline.md"
    if not path.is_file():
        raise SystemExit(f"Outline not found: {path}")
    return path


def parse_slides(text: str) -> List[Dict[str, str]]:
    matches = list(SLIDE_RE.finditer(text))
    if not matches:
        matches = list(SLIDE_ZH_RE.finditer(text))
    slides: List[Dict[str, str]] = []
    for match in matches:
        # A slide section ends at the next level-1/2 heading, so a trailing appendix is not scored.
        following = SECTION_RE.search(text, match.end())
        end = following.start() if following else len(text)
        block = text[match.start() : end].strip()
        headline = HEADLINE_RE.search(block)
        evidence = EVIDENCE_RE.search(block)
        visual = VISUAL_RE.search(block)
        slides.append(
            {
                "number": match.group(1),
                "title": match.group(2).lstrip(TITLE_PREFIX).rstrip(),
                "block": block,
                "headline": headline.group(1).strip() if headline else "",
                "evidence": evidence.group(1).strip() if evidence else "",
                "visual": visual.group(1).strip() if visual else "",
            }
        )
    return slides


def present(value: str) -> bool:
    return bool(value and not PLACEHOLDER_RE.search(value))


@lru_cache(maxsize=None)
def term_pattern(terms: Tuple[str, ...]) -> Pattern[str]:
    # ASCII terms must stand alone ("sam" is not "same", "market" is not "go-to-market").
    parts = [
        rf"(?<![a-z0-9-]){re.escape(term)}s?(?![a-z0-9-])" if term.isascii() else re.escape(term)
        for term in terms
    ]
    return re.compile("|".join(parts), re.IGNORECASE)


def contains_any(text: str, terms: Tuple[str, ...]) -> bool:
    return bool(term_pattern(terms).search(text))


def slide_beats(slide: Dict[str, str]) -> List[str]:
    beats = [name for name, terms in BEATS if contains_any(slide["title"], terms)]
    # A cover that states the one-line definition answers "what are you?" under any title.
    if "product definition" not in beats and DEFINITION_RE.search(slide["block"]):
        beats.append("product definition")
    return beats


def audit(slides: List[Dict[str, str]], minimum: int, maximum: int) -> Dict[str, object]:
    count = len(slides)
    text = "\n\n".join(slide["block"] for slide in slides)
    beats = [slide_beats(slide) for slide in slides]
    covered = [name for name, _ in BEATS if any(name in found for found in beats)]
    missing_beats = [name for name, _ in BEATS if name not in covered]
    financing = "\n\n".join(slide["block"] for slide, found in zip(slides, beats) if "financing" in found)
    headlines = sum(1 for slide in slides if present(slide["headline"]))
    evidence = sum(1 for slide in slides if present(slide["evidence"]))
    visuals = sum(1 for slide in slides if present(slide["visual"]))
    placeholder_count = len(PLACEHOLDER_RE.findall(text))

    structure = min(25, len(covered) * 2 + (1 if minimum <= count <= maximum else 0))
    headline_ratio = headlines / count if count else 0
    readability = round(12 * headline_ratio)
    if contains_any(text, ("investor takeaway", "投资人 takeaway", "投资人结论")):
        readability += 4
    if contains_any(text, ("one-line", "一句话", "definition", "定义", "产品定位")):
        readability += 4
    readability = min(20, readability)

    evidence_ratio = evidence / count if count else 0
    evidence_score = round(14 * evidence_ratio)
    if contains_any(text, ("source", "来源", "evidence", "证据")):
        evidence_score += 4
    if contains_any(text, ("assumption", "假设", "inference", "推断", "fact", "事实")):
        evidence_score += 4
    if contains_any(text, ("as of", "截至", "截止", "updated", "更新", "snapshot", "快照")):
        evidence_score += 3
    evidence_score = max(0, min(25, evidence_score - min(10, placeholder_count)))

    visual_ratio = visuals / count if count else 0
    visual_score = round(14 * visual_ratio)
    if contains_any(text, ("screenshot", "产品截图", "真实截图", "demo")):
        visual_score += 3
    if contains_any(text, ("chart", "图表", "axis", "坐标轴", "source note", "来源")):
        visual_score += 3
    visual_score = min(20, visual_score)

    # Only the financing page itself can deliver the ask; a deck without one scores 0 here.
    delivery = 0
    if AMOUNT_RE.search(financing):
        delivery += 4
    if contains_any(financing, ("use of funds", "use-of-funds", "资金用途", "资金使用")):
        delivery += 3
    if contains_any(financing, ("milestone", "里程碑", "runway", "18–24", "18-24", "个月", "month")):
        delivery += 3

    blockers: List[str] = []
    if not (minimum <= count <= maximum):
        blockers.append(f"Slide count is {count}; expected {minimum}–{maximum}.")
    if missing_beats:
        blockers.append("Missing investor story beats: " + ", ".join(missing_beats) + ".")
    if placeholder_count:
        blockers.append(f"Found {placeholder_count} placeholder or missing markers.")
    if "financing" in missing_beats:
        blockers.append("No clear financing ask.")
    elif not AMOUNT_RE.search(financing):
        blockers.append("The financing slide states no amount.")
    if evidence_ratio < 0.75:
        blockers.append("Fewer than 75% of slides contain a non-placeholder evidence/source field.")

    score = structure + readability + evidence_score + visual_score + delivery
    score = max(0, min(100, score))
    findings: List[str] = []
    if headline_ratio < 1:
        findings.append(f"{count - headlines} slide(s) lack a conclusion headline.")
    if visual_ratio < 1:
        findings.append(f"{count - visuals} slide(s) lack an explicit visual/chart specification.")
    if evidence_ratio < 1:
        findings.append(f"{count - evidence} slide(s) lack an explicit evidence/source field.")
    if score >= 85 and not blockers:
        decision = "investor-ready for visual production"
    elif score >= 70:
        decision = "conditional — revise before rendering"
    else:
        decision = "not ready"

    return {
        "score": score,
        "decision": decision,
        "slide_count": count,
        "scorecard": {
            "story_structure": structure,
            "investor_readability": readability,
            "evidence_hygiene": evidence_score,
            "visual_specification": visual_score,
            "financing_delivery": delivery,
        },
        "coverage": covered,
        "missing_beats": missing_beats,
        "blockers": blockers,
        "findings": findings,
        "placeholder_count": placeholder_count,
    }


def markdown_report(result: Dict[str, object], source: Path) -> str:
    scorecard = result["scorecard"]
    blockers = result["blockers"] or ["None detected by deterministic audit."]
    findings = result["findings"] or ["No structural findings detected."]
    missing = result["missing_beats"] or ["None"]
    lines = [
        "# BP Audit Report",
        "",
        f"- Source: `{source}`",
        f"- Reviewed: {dt.date.today().isoformat()}",
        f"- Score: **{result['score']} / 100**",
        f"- Decision: **{result['decision']}**",
        f"- Slides: {result['slide_count']}",
        "",
        "## Scorecard",
        "",
        "| Dimension | Score | Max |",
        "|---|---:|---:|",
        f"| Story structure | {scorecard['story_structure']} | 25 |",
        f"| Investor readability | {scorecard['investor_readability']} | 20 |",
        f"| Evidence and data hygiene | {scorecard['evidence_hygiene']} | 25 |",
        f"| Charts and visual specification | {scorecard['visual_specification']} | 20 |",
        f"| Financing delivery | {scorecard['financing_delivery']} | 10 |",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in blockers)
    lines.extend(["", "## Findings", ""])
    lines.extend(f"- {item}" for item in findings)
    lines.extend(["", "## Missing story beats", ""])
    lines.extend(f"- {item}" for item in missing)
    lines.extend(
        [
            "",
            "Beats are matched against slide titles (`## Slide NN — <title>`); the preamble is",
            "not scored, and Financing delivery counts only the financing slide.",
            "",
            "## Required visual review",
            "",
            "This script cannot validate typography, optical alignment, chart truth, screenshot",
            "legibility, or QR decoding. Review every final rendered page using the visual QA",
            "checklist in `references/review-rubric.md`.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    source = resolve_input(args.input)
    text = source.read_text(encoding="utf-8")
    slides = parse_slides(text)
    result = audit(slides, args.min_slides, args.max_slides)

    if args.format == "json":
        report = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    else:
        report = markdown_report(result, source)

    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8")
        print(f"Wrote BP audit report: {output}")
    else:
        print(report, end="" if report.endswith("\n") else "\n")

    if args.strict and (int(result["score"]) < 85 or bool(result["blockers"])):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
