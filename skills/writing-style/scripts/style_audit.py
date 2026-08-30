#!/usr/bin/env python3
"""Report observable writing metrics against the bundled v2 style profile."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


REFERENCE = {
    "source_articles": 19,
    "source_characters_approx": 124600,
    "average_sentence_length": 39.1,
    "short_sentence_ratio": 0.198,
    "medium_sentence_ratio": 0.317,
    "long_sentence_ratio": 0.486,
    "one_sentence_paragraph_ratio": 0.799,
    "average_sentences_per_paragraph": 1.11,
}

ADVISORY_BANDS = {
    "average_sentence_length": (30.0, 48.0),
    "short_sentence_ratio": (0.12, 0.30),
    "long_sentence_ratio": (0.38, 0.60),
    "one_sentence_paragraph_ratio": (0.65, 0.90),
}

ACTION_WORDS = (
    "跑通",
    "复盘",
    "拆解",
    "回滚",
    "发布",
    "验证",
    "维护",
    "迭代",
    "重做",
    "接入",
    "交付",
)

BOILERPLATE = (
    "随着时代发展",
    "在这个日新月异的时代",
    "赋能",
    "生态闭环",
    "颠覆性创新",
    "综上所述",
)


def strip_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    marker = text.find("\n---\n", 4)
    return text[marker + 5 :] if marker >= 0 else text


def clean_markdown(text: str) -> str:
    text = strip_frontmatter(text.replace("\r\n", "\n").replace("\r", "\n"))
    text = re.sub(r"\x60{3}[\s\S]*?\x60{3}", " ", text)
    text = re.sub(r"!\[[^\]]*]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)]\([^)]*\)", r"\1", text)
    text = re.sub(r"https?://\S+", " ", text)
    kept: List[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if re.fullmatch(r"\|?[\s:|-]+\|?", line):
            continue
        line = re.sub(r"^#{1,6}\s+", "", line)
        line = re.sub(r"^>\s?", "", line)
        line = re.sub(r"^(?:[-*+]|\d+[.)])\s+", "", line)
        line = re.sub(r"[*_~]+", "", line)
        kept.append(line)
    return "\n".join(kept)


def paragraph_blocks(text: str) -> List[str]:
    return [
        re.sub(r"\s+", " ", block).strip()
        for block in re.split(r"\n\s*\n", text)
        if re.sub(r"\s+", "", block)
    ]


def sentence_parts(text: str) -> List[str]:
    normalized = re.sub(r"\n+", "。", text)
    return [
        re.sub(r"\s+", "", part)
        for part in re.split(r"[。！？!?]+", normalized)
        if re.sub(r"\s+", "", part)
    ]


def visible_length(text: str) -> int:
    return len(re.sub(r"[\s，。！？!?；;：:“”‘’（）()《》〈〉、—…·,.]", "", text))


def ratio(count: int, total: int) -> float:
    return round(count / total, 4) if total else 0.0


def occurrences(text: str, terms: Sequence[str]) -> Dict[str, int]:
    return {term: text.count(term) for term in terms if text.count(term)}


def analyze(raw_text: str) -> Dict[str, Any]:
    cleaned = clean_markdown(raw_text)
    paragraphs = paragraph_blocks(cleaned)
    sentences = sentence_parts(cleaned)
    lengths = [visible_length(sentence) for sentence in sentences]
    lengths = [length for length in lengths if length > 0]

    short_count = sum(length < 15 for length in lengths)
    medium_count = sum(15 <= length <= 30 for length in lengths)
    long_count = sum(length > 30 for length in lengths)

    paragraph_sentence_counts = [
        max(1, len(sentence_parts(paragraph))) for paragraph in paragraphs
    ]
    one_sentence_count = sum(count == 1 for count in paragraph_sentence_counts)

    compact = re.sub(r"\s+", "", cleaned)
    numbers = re.findall(r"\d+(?:\.\d+)?(?:%|万|亿|元|天|小时|分钟|篇|个|次)?", cleaned)
    english_terms = re.findall(r"\b[A-Za-z][A-Za-z0-9+.#/-]*\b", cleaned)
    boilerplate_hits = occurrences(cleaned, BOILERPLATE)
    action_hits = occurrences(cleaned, ACTION_WORDS)

    sentence_total = len(lengths)
    paragraph_total = len(paragraphs)
    metrics: Dict[str, Any] = {
        "characters": visible_length(cleaned),
        "sentences": sentence_total,
        "paragraphs": paragraph_total,
        "average_sentence_length": round(sum(lengths) / sentence_total, 2)
        if sentence_total
        else 0.0,
        "short_sentence_ratio": ratio(short_count, sentence_total),
        "medium_sentence_ratio": ratio(medium_count, sentence_total),
        "long_sentence_ratio": ratio(long_count, sentence_total),
        "one_sentence_paragraph_ratio": ratio(one_sentence_count, paragraph_total),
        "average_sentences_per_paragraph": round(
            sum(paragraph_sentence_counts) / paragraph_total, 2
        )
        if paragraph_total
        else 0.0,
        "first_person_count": compact.count("我"),
        "second_person_count": compact.count("你"),
        "numeric_anchor_count": len(numbers),
        "unique_english_term_count": len(set(english_terms)),
        "action_word_hits": action_hits,
        "boilerplate_hits": boilerplate_hits,
        "exclamation_count": cleaned.count("！") + cleaned.count("!"),
        "ellipsis_count": cleaned.count("……") + cleaned.count("..."),
    }

    advisories: List[str] = []
    sample_sufficient = metrics["characters"] >= 300 and sentence_total >= 10
    if not sample_sufficient:
        advisories.append("文本少于 300 字或 10 句；比例只展示，不做区间判断。")
    else:
        for metric_name, band in ADVISORY_BANDS.items():
            value = float(metrics[metric_name])
            if value < band[0]:
                advisories.append(
                    "{} 低于跨题材参考区间 {:.0%}–{:.0%}。".format(
                        metric_name, band[0], band[1]
                    )
                    if "ratio" in metric_name
                    else "{} 低于跨题材参考区间 {:.1f}–{:.1f}。".format(
                        metric_name, band[0], band[1]
                    )
                )
            elif value > band[1]:
                advisories.append(
                    "{} 高于跨题材参考区间 {:.0%}–{:.0%}。".format(
                        metric_name, band[0], band[1]
                    )
                    if "ratio" in metric_name
                    else "{} 高于跨题材参考区间 {:.1f}–{:.1f}。".format(
                        metric_name, band[0], band[1]
                    )
                )

    if boilerplate_hits:
        advisories.append("发现禁忌或公关套话：" + "、".join(boilerplate_hits))
    if metrics["numeric_anchor_count"] == 0:
        advisories.append("未发现数字锚点；若题材需要可信度，请检查是否缺少可验证细节。")
    if metrics["first_person_count"] == 0:
        advisories.append("未发现第一人称；若是个人文风稿，请确认作者位置是否缺失。")
    if not advisories:
        advisories.append("未发现可由本地指标直接指出的问题；仍需人工检查事实与论证。")

    return {
        "schema": "lov-writing-style-audit/v1",
        "status": "diagnostic",
        "sample_sufficient_for_ratio_assessment": sample_sufficient,
        "metrics": metrics,
        "reference": REFERENCE,
        "advisory_bands": {
            key: {"min": value[0], "max": value[1]}
            for key, value in ADVISORY_BANDS.items()
        },
        "advisories": advisories,
        "limitations": [
            "指标不能判定作者身份，也不能证明文章质量。",
            "题材、长度与 Markdown 结构会影响比例。",
            "事实保真、论证成立和偶发特征适配必须人工验收。",
        ],
    }


def render_text(report: Dict[str, Any]) -> str:
    metrics = report["metrics"]
    lines = [
        "lov-writing-style v2 audit — diagnostic only",
        "",
        "规模",
        "- 字符：{characters}；句子：{sentences}；段落：{paragraphs}".format(**metrics),
        "",
        "节奏",
        "- 平均句长：{:.2f}".format(metrics["average_sentence_length"]),
        "- 短 / 中 / 长句：{:.1%} / {:.1%} / {:.1%}".format(
            metrics["short_sentence_ratio"],
            metrics["medium_sentence_ratio"],
            metrics["long_sentence_ratio"],
        ),
        "- 一句段：{:.1%}；平均每段：{:.2f} 句".format(
            metrics["one_sentence_paragraph_ratio"],
            metrics["average_sentences_per_paragraph"],
        ),
        "",
        "声音与证据",
        "- 我：{first_person_count}；你：{second_person_count}；数字锚点：{numeric_anchor_count}；英文词项：{unique_english_term_count}".format(
            **metrics
        ),
        "- 行动词：" + (json.dumps(metrics["action_word_hits"], ensure_ascii=False) if metrics["action_word_hits"] else "无"),
        "- 禁忌词：" + (json.dumps(metrics["boilerplate_hits"], ensure_ascii=False) if metrics["boilerplate_hits"] else "无"),
        "",
        "提示",
    ]
    lines.extend("- " + item for item in report["advisories"])
    lines.extend(["", "限制"])
    lines.extend("- " + item for item in report["limitations"])
    return "\n".join(lines)


def run_self_test() -> None:
    sample = (
        "两周前，我把 19 篇文章重新跑了一遍。\n\n"
        "结果很直接。\n\n"
        "平均句长、段落和数字都能量，但文风不是一个分数。\n\n"
        "所以这次我先守住事实，再谈节奏。"
    )
    report = analyze(sample)
    metrics = report["metrics"]
    assert metrics["sentences"] == 4
    assert metrics["paragraphs"] == 4
    assert metrics["one_sentence_paragraph_ratio"] == 1.0
    assert metrics["first_person_count"] == 2
    assert metrics["numeric_anchor_count"] == 1


def read_input(path: Optional[str], direct_text: Optional[str]) -> str:
    if direct_text is not None:
        return direct_text
    if path in (None, "-"):
        if sys.stdin.isatty():
            raise ValueError("provide a UTF-8 file, --text, or stdin")
        return sys.stdin.read()
    return Path(path).expanduser().read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", help="UTF-8 Markdown/text file, or - for stdin")
    parser.add_argument("--text", help="Short text supplied directly")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        try:
            run_self_test()
        except AssertionError as exc:
            print("FAILED: style_audit self-test: {}".format(exc), file=sys.stderr)
            return 1
        print("PASSED: style_audit self-test")
        return 0

    try:
        raw_text = read_input(args.input, args.text)
    except (OSError, UnicodeError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "status": "error",
                    "context_id": "lov-writing-style.input",
                    "error": str(exc),
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2

    report = analyze(raw_text)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
