#!/usr/bin/env python3
"""Conservative detector for production-language leaks in visible copy."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


PATTERNS = [
    (
        "component_self_reference",
        re.compile(r"正文首图|封面图|配图|按钮文案|此处文案|当前页面|本图(?:展示|说明)"),
        "可见文案正在解释它属于哪个组件；改为读者需要的内容，或删除。",
    ),
    (
        "production_metadata",
        re.compile(r"官方\s*[Ll]ogo|品牌色|(?:由.{0,24})?构成(?:的)?|AI\s*生成|渲染(?:结果|输出)?|导出(?:图片|结果)?|Prompt"),
        "检测到制作链或设计交付信息；默认移出读者文案。",
    ),
    (
        "agent_meta",
        re.compile(r"^(?:下面是|以下是|我会|我已经|已为你|根据你的要求|为你生成)"),
        "检测到 Agent 汇报口吻；只交付目标场景需要的成品。",
    ),
    (
        "empty_self_praise",
        re.compile(r"专业(?:级)?|高端|高级感|精心设计|用心打造|重磅来袭"),
        "检测到缺少证据的自我评价；用事实、结果或具体差异替代。",
    ),
]


def audit(text: str, surface: str, component: str) -> dict:
    findings = []
    for finding_id, pattern, suggestion in PATTERNS:
        for match in pattern.finditer(text):
            findings.append(
                {
                    "id": finding_id,
                    "match": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                    "suggestion": suggestion,
                }
            )

    if component == "caption" and len(text.strip()) > 60:
        findings.append(
            {
                "id": "caption_length",
                "match": str(len(text.strip())),
                "start": 0,
                "end": len(text),
                "suggestion": "Caption 过长；只保留识别、理解或必要归属。",
            }
        )

    if component in {"button", "cta"} and re.search(r"[。！？!?]$", text.strip()):
        findings.append(
            {
                "id": "control_sentence_punctuation",
                "match": text.strip()[-1:],
                "start": max(0, len(text.strip()) - 1),
                "end": len(text.strip()),
                "suggestion": "按钮或 CTA 默认使用动作短语，不写成完整说明句。",
            }
        )

    return {
        "ok": not findings,
        "surface": surface,
        "component": component,
        "chars": len(text.strip()),
        "findings": findings,
        "limitations": [
            "This audit detects observable wording only.",
            "Audience fit, brand voice, truth, and in-place hierarchy require semantic review.",
        ],
    }


def self_test() -> int:
    bad = "Piet Mondrian《Composition (No. 1) Gray-Red》与手工川官方 Logo 构成的正文首图"
    good = "Piet Mondrian，《Composition (No. 1) Gray-Red》，1935。"
    bad_result = audit(bad, "wechat", "caption")
    good_result = audit(good, "wechat", "caption")
    expected = {"production_metadata", "component_self_reference"}
    actual = {item["id"] for item in bad_result["findings"]}
    if not expected.issubset(actual):
        raise AssertionError(f"missing findings: {sorted(expected - actual)}")
    if not good_result["ok"]:
        raise AssertionError(f"good example failed: {good_result['findings']}")
    production_matches = {
        item["match"] for item in bad_result["findings"] if item["id"] == "production_metadata"
    }
    if not {"官方 Logo", "构成的"}.issubset(production_matches):
        raise AssertionError(f"missing production matches: {sorted(production_matches)}")
    print("SELF-TEST PASSED")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--text")
    source.add_argument("--input", type=Path)
    parser.add_argument("--surface", default="unspecified")
    parser.add_argument("--component", default="body")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if args.text is None and args.input is None:
        parser.error("provide --text, --input, or --self-test")

    text = args.text if args.text is not None else args.input.read_text(encoding="utf-8")
    result = audit(text, args.surface, args.component)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["ok"]:
        print("PASS: no observable production-language leak found")
    else:
        print(f"FAIL: {len(result['findings'])} finding(s)")
        for item in result["findings"]:
            print(f"- {item['id']}: {item['match']} — {item['suggestion']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
