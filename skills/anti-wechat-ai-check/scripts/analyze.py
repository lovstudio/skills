#!/usr/bin/env python3
"""
Analyze text for AI-generated content indicators.

Checks for patterns commonly flagged by WeChat's 3.27 non-human automated
content creation detection: template phrases, transition word density,
sentence structure uniformity, paragraph pattern repetition, etc.

Usage:
    python analyze.py --input article.md
    python analyze.py --text "直接传入文本内容"
    python analyze.py --input article.md --format json
"""

import argparse, json, re, sys
from collections import Counter
from pathlib import Path

# ── AI 高频模板短语 ──────────────────────────────────────────────────────

AI_TEMPLATE_PHRASES = [
    # 开头套话
    r"在当今(?:社会|时代|数字化|信息化|快速发展)",
    r"随着(?:科技|技术|社会|经济|时代)的(?:不断|快速|飞速|持续)?(?:发展|进步|演变)",
    r"(?:众所周知|不可否认|毋庸置疑|值得注意的是|需要指出的是)",
    r"在(?:这个|这样一个)(?:瞬息万变|日新月异|充满挑战)",
    r"(?:近年来|当下|如今|当前),?\s*(?:越来越多|愈来愈多)",
    # 过渡/连接
    r"(?:首先|其次|再次|最后|此外|另外|与此同时|不仅如此|更重要的是|值得一提的是)",
    r"(?:总而言之|综上所述|总的来说|归根结底|由此可见|不难发现)",
    r"(?:一方面|另一方面).*(?:一方面|另一方面)",
    r"从(?:本质上|根本上|某种意义上)(?:来说|而言|来看)",
    # 总结套话
    r"(?:展望未来|放眼未来|面对未来|在未来的日子里)",
    r"(?:让我们|我们(?:应该|需要|必须))(?:共同|一起|携手)",
    r"(?:相信|期待)(?:在不久的将来|未来)",
    r"这(?:不仅|既)是.*(?:更是|也是).*的(?:体现|表现|缩影)",
    # 形容词堆砌
    r"(?:深入|全面|系统|深刻)(?:地)?(?:分析|探讨|研究|思考|了解|理解)",
    r"(?:具有|拥有)(?:重要|深远|深刻|积极|巨大)(?:的)?(?:意义|价值|影响|作用)",
    r"(?:有效|高效|切实|积极)(?:地)?(?:推动|促进|推进|提升|提高|加强|改善)",
    # 填充短语
    r"(?:不得不说|不可忽视的是|毫无疑问)",
    r"(?:扮演着|发挥着)(?:重要|关键|不可或缺)(?:的)?(?:角色|作用)",
    r"在.*(?:方面|层面|维度|角度)(?:上)?(?:,|，)",
    r"(?:为此|因此|故而|鉴于此|有鉴于此)",
]

# ── 段落结构模式 ──────────────────────────────────────────────────────

PARAGRAPH_PATTERNS = [
    ("总分总", r"(?:总的来说|综上|总而言之|由此可见)"),
    ("并列三段", r"(?:第一|首先).*(?:第二|其次).*(?:第三|再次|最后)"),
    ("递进", r"(?:不仅.*而且|不但.*还|不仅如此)"),
]


def load_text(args):
    if args.text:
        return args.text
    if args.input:
        p = Path(args.input)
        if not p.exists():
            print(f"ERROR: file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        return p.read_text(encoding="utf-8")
    print("ERROR: provide --input or --text", file=sys.stderr)
    sys.exit(1)


def analyze(text: str) -> dict:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    # 段落：以空行分隔的文本块
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    # 句子：按句号、问号、感叹号分割
    sentences = re.split(r"[。！？!?]", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 2]

    results = {
        "stats": {},
        "template_phrases": [],
        "structure_issues": [],
        "sentence_issues": [],
        "risk_score": 0,
        "risk_level": "",
    }

    # ── 1. 基础统计 ──
    char_count = len(re.sub(r"\s", "", text))
    results["stats"] = {
        "char_count": char_count,
        "paragraph_count": len(paragraphs),
        "sentence_count": len(sentences),
    }

    score = 0

    # ── 2. 模板短语检测 ──
    for pattern in AI_TEMPLATE_PHRASES:
        matches = re.findall(pattern, text)
        if matches:
            for m in matches:
                results["template_phrases"].append({
                    "match": m if isinstance(m, str) else m[0],
                    "pattern": pattern[:40],
                })
                score += 3

    # ── 3. 过渡词密度 ──
    transition_words = re.findall(
        r"(?:首先|其次|再次|此外|另外|最后|因此|总之|然而|不过|"
        r"与此同时|不仅如此|更重要的是|值得一提的是|事实上|实际上|"
        r"换言之|也就是说|具体来说|简而言之|从而|进而|继而)",
        text,
    )
    density = len(transition_words) / max(len(sentences), 1)
    if density > 0.3:
        results["structure_issues"].append({
            "type": "transition_word_density",
            "detail": f"过渡词密度 {density:.1%}（{len(transition_words)}/{len(sentences)} 句），AI 文章通常 >30%",
            "severity": "high",
        })
        score += 10
    elif density > 0.15:
        results["structure_issues"].append({
            "type": "transition_word_density",
            "detail": f"过渡词密度 {density:.1%}，略偏高",
            "severity": "medium",
        })
        score += 5

    # ── 4. 句子长度均匀度 ──
    if len(sentences) >= 5:
        lengths = [len(s) for s in sentences]
        avg = sum(lengths) / len(lengths)
        if avg > 0:
            cv = (sum((l - avg) ** 2 for l in lengths) / len(lengths)) ** 0.5 / avg
            if cv < 0.25:
                results["sentence_issues"].append({
                    "type": "uniform_sentence_length",
                    "detail": f"句子长度变异系数 {cv:.2f}（<0.25 表示过于整齐，真人写作通常 >0.35）",
                    "severity": "high",
                })
                score += 10
            elif cv < 0.35:
                results["sentence_issues"].append({
                    "type": "uniform_sentence_length",
                    "detail": f"句子长度变异系数 {cv:.2f}，偏整齐",
                    "severity": "medium",
                })
                score += 5

    # ── 5. 段落长度均匀度 ──
    if len(paragraphs) >= 4:
        p_lens = [len(p) for p in paragraphs]
        p_avg = sum(p_lens) / len(p_lens)
        if p_avg > 0:
            p_cv = (sum((l - p_avg) ** 2 for l in p_lens) / len(p_lens)) ** 0.5 / p_avg
            if p_cv < 0.2:
                results["structure_issues"].append({
                    "type": "uniform_paragraph_length",
                    "detail": f"段落长度变异系数 {p_cv:.2f}（过于均匀，像模板生成）",
                    "severity": "high",
                })
                score += 8

    # ── 6. 段首重复模式 ──
    if len(paragraphs) >= 3:
        starters = []
        for p in paragraphs:
            # 取前 4 个字作为段首模式
            clean = re.sub(r"^[#\-\*\d\.、]+\s*", "", p)
            if len(clean) >= 4:
                starters.append(clean[:4])
        starter_counts = Counter(starters)
        repeated = {k: v for k, v in starter_counts.items() if v >= 3}
        if repeated:
            results["structure_issues"].append({
                "type": "repeated_paragraph_starters",
                "detail": f"段首重复: {', '.join(f'「{k}」×{v}' for k, v in repeated.items())}",
                "severity": "medium",
            })
            score += 5

    # ── 7. 句式雷同检测（句子开头 pattern） ──
    if len(sentences) >= 6:
        sent_starts = []
        for s in sentences:
            clean = re.sub(r"^[\s,，、]+", "", s)
            if len(clean) >= 3:
                sent_starts.append(clean[:3])
        start_counts = Counter(sent_starts)
        repeated_starts = {k: v for k, v in start_counts.items() if v >= 3}
        if repeated_starts:
            results["sentence_issues"].append({
                "type": "repeated_sentence_starts",
                "detail": f"句首重复: {', '.join(f'「{k}」×{v}' for k, v in repeated_starts.items())}",
                "severity": "medium",
            })
            score += 5

    # ── 8. "的" 字密度（AI 中文常见过度使用 "的"） ──
    de_count = text.count("的")
    if char_count > 50:
        de_ratio = de_count / char_count
        if de_ratio > 0.06:
            results["sentence_issues"].append({
                "type": "excessive_de",
                "detail": f"「的」字占比 {de_ratio:.1%}（共 {de_count} 个），AI 文章常 >6%",
                "severity": "medium",
            })
            score += 5

    # ── 9. 列举模式（"第一...第二...第三" 或数字编号过多） ──
    enum_matches = re.findall(r"(?:第[一二三四五六七八九十]|[1-9]\.|[①②③④⑤])", text)
    if len(enum_matches) > 6:
        results["structure_issues"].append({
            "type": "excessive_enumeration",
            "detail": f"列举标记 {len(enum_matches)} 处，过度条理化是 AI 特征",
            "severity": "low",
        })
        score += 3

    # ── 风险等级 ──
    results["risk_score"] = min(score, 100)
    if score >= 50:
        results["risk_level"] = "HIGH"
    elif score >= 25:
        results["risk_level"] = "MEDIUM"
    else:
        results["risk_level"] = "LOW"

    return results


def format_report(r: dict) -> str:
    out = []
    out.append(f"═══ AI 痕迹分析报告 ═══\n")
    out.append(f"字数: {r['stats']['char_count']}  段落: {r['stats']['paragraph_count']}  句子: {r['stats']['sentence_count']}")
    out.append(f"风险评分: {r['risk_score']}/100  等级: {r['risk_level']}\n")

    if r["template_phrases"]:
        out.append(f"── 模板短语 ({len(r['template_phrases'])} 处) ──")
        for item in r["template_phrases"]:
            out.append(f"  ⚠ 「{item['match']}」")
        out.append("")

    for section, label in [("structure_issues", "结构问题"), ("sentence_issues", "句式问题")]:
        items = r[section]
        if items:
            out.append(f"── {label} ({len(items)} 项) ──")
            for item in items:
                sev = {"high": "🔴", "medium": "🟡", "low": "🟢"}[item["severity"]]
                out.append(f"  {sev} {item['detail']}")
            out.append("")

    if r["risk_score"] < 10:
        out.append("✅ 文本 AI 特征不明显，风险较低。")

    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="Analyze text for AI-generation indicators")
    ap.add_argument("--input", "-i", help="Input file path (.md, .txt)")
    ap.add_argument("--text", "-t", help="Inline text to analyze")
    ap.add_argument("--format", "-f", choices=["text", "json"], default="text", help="Output format")
    args = ap.parse_args()

    text = load_text(args)
    results = analyze(text)

    if args.format == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(format_report(results))


if __name__ == "__main__":
    main()
