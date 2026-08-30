#!/usr/bin/env python3
"""Deterministic Chinese prose metrics for the lov-human-writing loop.

This engine measures what published AI-text detectors actually score --
predictability, burstiness, structural regularity, template density and
concreteness -- instead of asking a language model to grade its own draft.

Usage:
    python3 measure.py --input article.md
    python3 measure.py --input article.md --profile zhuque --format json
    python3 measure.py --input new.md --compare old.md
    python3 measure.py --calibrate ./my-human-articles --out baseline.json

Stdlib only. CJK safe. No network access.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

SCHEMA = "lov-human-writing/metrics/v1"

# 个人基线的样本量下限。低于 12 篇时 p90/p95 实际退化成 max()，
# 得到的基线比默认经验区间更不可靠，所以直接拒绝而不是给出假精度。
MIN_CALIBRATION_SAMPLES = 12
RECOMMENDED_CALIBRATION_SAMPLES = 30
CJK = "一-鿿"

# ── 分级词表 ────────────────────────────────────────────────────────────
# HARD: 中文 AI 写作的强指纹，出现即应改写。
# SOFT: 单次出现无害，密度过高才是问题。

HARD_PHRASES = [
    r"综上所述", r"总而言之", r"总的来说", r"归根结底", r"由此可见",
    r"值得注意的是", r"需要指出的是", r"不难发现", r"不可忽视的是",
    r"众所周知", r"毋庸置疑", r"不可否认", r"无可否认",
    r"换句话说", r"换言之", r"说白了", r"这意味着", r"意味着什么",
    r"从某种意义上(?:来说|而言|讲)", r"在某种程度上(?:来说|而言)",
    r"在当今[^。，]{0,8}(?:时代|社会|背景下)",
    r"随着[^。，]{0,10}的(?:不断|快速|飞速|持续)(?:发展|进步|演进)",
    r"在(?:这个|这样一个)[^。，]{0,8}的时代",
    r"让我们(?:一起|共同)?(?:来)?(?:看看|探讨|走进)",
    r"接下来(?:让我们|我们将)", r"下面(?:我来|让我们)",
    r"展望未来", r"放眼未来", r"未来可期",
    r"首先[^。]{0,60}其次[^。]{0,80}最后",
    r"赋能", r"底层逻辑", r"生态位", r"顶层设计", r"抓手",
    r"新质生产力", r"降维打击",
]

SOFT_PHRASES = [
    r"此外", r"另外", r"然而", r"因此", r"于是", r"从而", r"进而",
    r"事实上", r"实际上", r"具体来说", r"简而言之", r"一言以蔽之",
    r"一方面", r"另一方面", r"与此同时", r"不仅如此", r"更重要的是",
    r"值得一提的是", r"更为关键的是", r"必须承认",
    r"至关重要", r"举足轻重", r"不言而喻",
    r"深入(?:探讨|分析|剖析|理解)", r"全面(?:分析|梳理|覆盖)",
    r"系统(?:性地|地)?(?:梳理|分析)",
    r"(?:重要|深远|深刻|巨大)的(?:意义|价值|影响|作用)",
    r"(?:关键|核心|不可或缺)的(?:角色|作用|地位)",
    r"(?:显著|极大|有效)地?(?:提升|提高|改善|推动|促进)",
    r"多维度", r"全方位", r"高质量发展", r"持续演进",
]

# 过渡词：按“每句多少个”计密度，而不是简单计数。
TRANSITION_WORDS = [
    "首先", "其次", "再次", "最后", "此外", "另外", "然而", "但是", "因此",
    "所以", "于是", "从而", "进而", "总之", "综上", "同时", "与此同时",
    "不仅如此", "更重要的是", "值得一提的是", "事实上", "实际上",
    "具体来说", "简而言之", "换言之", "也就是说", "由此", "可见", "故而",
]

# 中文里“-ing 式肤浅分析”的真实形态：分句以「体现/彰显/…了 X」收尾。
TAIL_NOMINALIZATION = re.compile(
    r"[，,]\s*(?:充分)?(?:体现|彰显|凸显|突显|反映|折射|印证|诠释|展现|见证|标志|昭示)"
    r"(?:出|了|着)[^。！？；]{2,40}[。！？；]"
)

# 中文 AI 极爱的四字格套话。
IDIOM_4CHAR = [
    "日新月异", "瞬息万变", "层出不穷", "不胜枚举", "百花齐放", "蓬勃发展",
    "行之有效", "卓有成效", "如火如荼", "举世瞩目", "空前繁荣", "势不可挡",
    "相辅相成", "相得益彰", "一脉相承", "有目共睹", "不容小觑",
    "与时俱进", "开拓创新", "锐意进取", "任重道远", "方兴未艾", "崭露头角",
    "屈指可数", "包罗万象", "浩如烟海", "波澜壮阔", "熠熠生辉", "彰显魅力",
]

NEGATIVE_PARALLEL = re.compile(
    r"不(?:仅|只)(?:是)?[^。！？]{2,40}(?:而且|更是|还是|更|也)"
    r"|不是[^。！？]{2,30}而是"
    r"|与其[^。！？]{2,30}(?:不如|毋宁)"
    r"|既[^。！？]{2,30}又[^。！？]{2,30}"
)

RULE_OF_THREE = re.compile(
    rf"[{CJK}A-Za-z0-9]{{2,10}}、[{CJK}A-Za-z0-9]{{2,10}}、[{CJK}A-Za-z0-9]{{2,10}}"
)

HEDGE_WORDS = [
    "可能", "或许", "也许", "大概", "似乎", "在一定程度上", "某种程度上",
    "通常来说", "一般而言", "相对而言", "总体上",
]

STANCE_WORDS = [
    "我觉得", "我认为", "我个人", "我不信", "说实话", "坦率", "我承认",
    "我猜", "我怀疑", "在我看来", "我踩过", "我试过", "我当时",
]

CONCRETE_ANCHOR = re.compile(
    r"\d{4}\s*年|\d{1,2}\s*月\d{1,2}\s*日|\d{1,2}:\d{2}|凌晨|上午|下午|昨天|今天|前天"
    r"|\d+(?:\.\d+)?\s*(?:元|块|万|亿|美元|人|次|天|小时|分钟|公里|台|个|条|版|轮)"
    r"|\d+(?:\.\d+)?\s*%|v\d+(?:\.\d+)+"
)

EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002700-\U000027BF\U0001F000-\U0001F0FF"
    "\U00002600-\U000026FF\U0001F900-\U0001F9FF✅❌⭐✨]"
)

# 中文正规写法本就是「——」和成对引号，按总量计数会把真人判成 AI。
# 真正的机器习惯是：孤立单破折号（英文排版惯性）、多套引号体系混用。
LONE_DASH = re.compile(r"(?<![—-])(?:—|--)(?![—-])")
QUOTE_SYSTEMS = (
    re.compile(r"[「」『』]"),      # 中文直排引号
    re.compile(r"[“”‘’]"),          # 中文弯引号
    re.compile(r"(?<![A-Za-z0-9])[\"'](?![A-Za-z0-9])"),  # 裸 ASCII 引号
)
INLINE_HEADING = re.compile(
    r"^\s*(?:[-*+]\s+|\d+[.、)]\s+)?\*\*[^*\n]{1,24}?(?:[:：]\*\*|\*\*\s*[:：])"
)
BOLD_SPAN = re.compile(r"\*\*[^*\n]{1,80}\*\*")
LATIN_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9._+-]{1,}")
FENCE = re.compile(r"```.*?```", re.S)


# ── 基线（实测校准） ────────────────────────────────────────────────────
# 默认区间来自 351 篇真人中文长文的实测分位数，不是凭感觉设的。
# 语料与方法见 references/benchmark.md。
#
# 定界规则（对两类指标方向相反）：
#   · 变异性/具体性指标（越高越像人）→ 下界取 p10，warn 取 p5；
#   · 套话/规整度指标（越高越像机器）→ 上界取 p90，warn 取 p95；
#   · 真人中位数为 0 的 AI 指纹项（四字格套话、尾部名词化）→ 不取 p90
#     （p90 也是 0，会导致零容忍误判），而是取略高于 p95 的近零上界。
#
# 实测推翻了初版手工阈值，且错在两个方向：
#   过严（误判真人）：opener_repeat_ratio、colon_per_1k、bold_per_1k、
#     heading_per_1k、first_person_per_1k、rule_of_three_per_1k、solo_para_ratio
#   过松（漏判 AI）：idiom4_per_1k、hedge_per_1k、de_ratio、sent_len_cv
#
# 权威用法：用 --calibrate 基于自己的历史真人稿件生成个人基线。

def _band(target, warn=None):
    return {"target": target, "warn": warn if warn is not None else target}


BASE_BANDS: Dict[str, dict] = {
    # 节奏 / burstiness —— 双侧区间：太整齐像机器，太失控则是转写稿
    "sent_len_mean": _band([21, 46], [19, 52]),
    "sent_len_cv": _band([0.54, None], [0.51, None]),
    "short_sent_ratio": _band([0.12, 0.39], [0.09, 0.47]),
    "long_sent_ratio": _band([0.05, 0.42], [0.03, 0.50]),
    "max_uniform_run": _band([None, 7], [None, 8]),
    "para_len_cv": _band([0.58, None], [0.49, None]),
    "solo_para_ratio": _band([0.24, 0.82], [0.12, 0.90]),
    # 模板 / 重复
    "opener_repeat_ratio": _band([None, 0.49], [None, 0.57]),
    "transition_density": _band([None, 0.22], [None, 0.30]),
    "hard_phrase_per_1k": _band([None, 0.50], [None, 0.75]),
    "soft_phrase_per_1k": _band([None, 2.1], [None, 2.9]),
    # 下面两项真人 p90 就是 0，取 p90 会变成零容忍；改用近零上界
    "tail_nominal_per_1k": _band([None, 0.15], [None, 0.40]),
    "idiom4_per_1k": _band([None, 0.10], [None, 0.30]),
    "neg_parallel_per_1k": _band([None, 1.2], [None, 1.9]),
    "rule_of_three_per_1k": _band([None, 4.2], [None, 5.2]),
    # 结构规整度
    "inline_heading_ratio": _band([None, 0.21], [None, 0.34]),
    "bullet_ratio": _band([None, 0.46], [None, 0.66]),
    "bold_per_1k": _band([None, 16.7], [None, 20.4]),
    "heading_per_1k": _band([None, 8.0], [None, 9.5]),
    "list_item_len_cv": _band([0.27, None], [0.20, None]),
    # 具体性 / 立场 —— 正向指标，缺失是 AI 稿的典型特征
    "digit_per_1k": _band([2.8, None], [1.9, None]),
    # latin_per_1k 不设区间：英文 token 密度取决于选题（技术文必然高、
    # 随笔必然低），不是人机信号。实测它只贡献误判，故降级为信息项。
    # 第一人称高度依赖文体，真人 p10 已低到 0.11；基线只做兜底，收紧交给 profile
    "first_person_per_1k": _band([0.10, None], [0.0, None]),
    "concrete_anchor_count": _band([1, None], [0, None]),
    "hedge_per_1k": _band([None, 2.6], [None, 3.3]),
    # 机械指纹 —— 只保留在中文里真正成立的项
    "de_ratio": _band([None, 0.038], [None, 0.043]),
    "lone_dash_per_1k": _band([None, 2.1], [None, 3.7]),
    "colon_per_1k": _band([None, 16.6], [None, 19.6]),
    "quote_style_mixed": _band([None, 1], [None, 2]),
    "emoji_per_1k": _band([None, 1.0], [None, 2.7]),
}

# profile 覆盖统一从同一份实测分布取值，只是换分位数：
# 要更严就把机器向指标从 p90 收到 p75、把人向指标从 p10 提到 p25。
PROFILES: Dict[str, dict] = {
    "wechat": {
        "label": "微信公众号长文（适配长段落、第一人称与移动端阅读节奏）",
        "bands": {
            # 公众号长文的人味主要靠第一人称叙事，提到 p25
            "first_person_per_1k": _band([1.0, None], [0.10, None]),
        },
    },
    "zhuque": {
        "label": "高强度表层审计（收紧句段波动、结构工整与套话密度）",
        "bands": {
            "sent_len_cv": _band([0.59, None], [0.54, None]),
            "max_uniform_run": _band([None, 5], [None, 7]),
            "para_len_cv": _band([0.71, None], [0.58, None]),
            "soft_phrase_per_1k": _band([None, 1.0], [None, 2.1]),
            "transition_density": _band([None, 0.13], [None, 0.22]),
            "hard_phrase_per_1k": _band([None, 0.0], [None, 0.25]),
            "list_item_len_cv": _band([0.44, None], [0.27, None]),
        },
    },
    "neutral": {
        "label": "通用非虚构写作（不假设口语风格）",
        "bands": {
            "solo_para_ratio": _band([0.05, 0.90], [0.0, 0.96]),
            "first_person_per_1k": _band([0.0, None], [0.0, None]),
        },
    },
    "thesis": {
        "label": "学术 / 正式文体（保留书面语，仍要求节奏与具体性）",
        "bands": {
            "solo_para_ratio": _band([0.0, 0.38], [0.0, 0.50]),
            "first_person_per_1k": _band([0.0, None], [0.0, None]),
            "short_sent_ratio": _band([0.03, 0.31], [0.0, 0.39]),
            "sent_len_mean": _band([26, 52], [21, 66]),
            "hedge_per_1k": _band([None, 5.5], [None, 8.0]),
            "bold_per_1k": _band([None, 5.1], [None, 9.9]),
            "emoji_per_1k": _band([None, 0.0], [None, 0.0]),
            "quote_style_mixed": _band([None, 0], [None, 1]),
        },
    },
}

FAMILIES: List[Tuple[str, str, Sequence[str]]] = [
    ("rhythm", "节奏 / 爆发性", (
        "sent_len_mean", "sent_len_cv", "short_sent_ratio", "long_sent_ratio",
        "max_uniform_run", "para_len_cv", "solo_para_ratio")),
    ("template", "模板 / 重复", (
        "opener_repeat_ratio", "transition_density", "hard_phrase_per_1k",
        "soft_phrase_per_1k", "tail_nominal_per_1k", "idiom4_per_1k",
        "neg_parallel_per_1k", "rule_of_three_per_1k")),
    ("structure", "结构规整度", (
        "inline_heading_ratio", "bullet_ratio", "bold_per_1k",
        "heading_per_1k", "list_item_len_cv")),
    ("concreteness", "具体性 / 立场", (
        "digit_per_1k", "latin_per_1k", "first_person_per_1k",
        "concrete_anchor_count", "hedge_per_1k")),
    ("fingerprint", "机械指纹", (
        "de_ratio", "lone_dash_per_1k", "colon_per_1k", "quote_style_mixed",
        "emoji_per_1k")),
]

LABELS = {
    "sent_len_mean": "平均句长（字）",
    "sent_len_cv": "句长变异系数 CV（越高越像人）",
    "short_sent_ratio": "短句占比（<15 字）",
    "long_sent_ratio": "长句占比（>45 字）",
    "max_uniform_run": "最长等长句链（±20% 内连续句数）",
    "para_len_cv": "段落长度变异系数",
    "solo_para_ratio": "一句成段占比",
    "opener_repeat_ratio": "句首二字重复率",
    "transition_density": "过渡词密度（个/句）",
    "hard_phrase_per_1k": "硬禁套话（次/千字）",
    "soft_phrase_per_1k": "慎用套话（次/千字）",
    "tail_nominal_per_1k": "分句尾「体现/彰显了…」（次/千字）",
    "idiom4_per_1k": "四字格套话（次/千字）",
    "neg_parallel_per_1k": "否定式排比（次/千字）",
    "rule_of_three_per_1k": "三项并列（次/千字）",
    "inline_heading_ratio": "「**粗体词：**解释」行占比",
    "bullet_ratio": "列表行占比",
    "bold_per_1k": "加粗片段（次/千字）",
    "heading_per_1k": "标题（个/千字）",
    "list_item_len_cv": "列表项长度变异系数",
    "digit_per_1k": "数字串（个/千字）",
    "latin_per_1k": "英文/产品名 token（个/千字）",
    "first_person_per_1k": "第一人称（次/千字）",
    "concrete_anchor_count": "时间/金额/版本等硬锚点（个）",
    "hedge_per_1k": "模糊限定词（次/千字）",
    "de_ratio": "「的」字占比",
    "lone_dash_per_1k": "孤立单破折号（次/千字，中文应用「——」）",
    "colon_per_1k": "冒号（个/千字）",
    "quote_style_mixed": "混用的引号体系数（超 1 套即机器痕迹）",
    "emoji_per_1k": "emoji（个/千字）",
}


# ── 文本切分 ────────────────────────────────────────────────────────────

def strip_front_matter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text


def split_blocks(text: str) -> Tuple[str, List[str]]:
    """Return (prose_text_without_code, raw_lines)."""
    lines = text.split("\n")
    prose = FENCE.sub(" ", text)
    prose = re.sub(r"`[^`\n]+`", " ", prose)
    prose = re.sub(r"^\s{0,3}#{1,6}\s+", "", prose, flags=re.M)
    prose = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", prose)
    prose = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", prose)
    prose = re.sub(r"\*{1,3}|__|~~|^\s{0,3}>\s?", "", prose, flags=re.M)
    return prose, lines


SENT_END = re.compile(r"(?<=[。！？!?…])|(?<=\n)")


def split_sentences(prose: str) -> List[str]:
    parts = re.split(r"[。！？!?…]+|\n+", prose)
    out = []
    for p in parts:
        s = p.strip().strip("*>-# 　")
        if len(re.sub(r"\s", "", s)) >= 3:
            out.append(s)
    return out


def split_paragraphs(text: str) -> List[str]:
    body = FENCE.sub(" ", text)
    parts = re.split(r"\n\s*\n", body)
    out = []
    for p in parts:
        s = p.strip()
        if not s or s.startswith("#"):
            continue
        if len(re.sub(r"\s", "", s)) >= 2:
            out.append(s)
    return out


def cjk_len(s: str) -> int:
    return len(re.sub(r"\s", "", s))


def cv(values: Sequence[float]) -> float:
    vals = [v for v in values if v > 0]
    if len(vals) < 2:
        return 0.0
    mean = statistics.fmean(vals)
    if mean == 0:
        return 0.0
    return statistics.pstdev(vals) / mean


# ── 指标计算 ────────────────────────────────────────────────────────────

def compute(text: str) -> Tuple[Dict[str, float], Dict[str, List[dict]], Dict[str, float]]:
    text = strip_front_matter(text)
    prose, lines = split_blocks(text)
    sentences = split_sentences(prose)
    paragraphs = split_paragraphs(text)
    chars = cjk_len(prose)
    per_1k = (lambda n: round(n * 1000 / chars, 2)) if chars else (lambda n: 0.0)

    m: Dict[str, float] = {}
    loc: Dict[str, List[dict]] = {}
    stats = {
        "char_count": chars,
        "sentence_count": len(sentences),
        "paragraph_count": len(paragraphs),
        "line_count": len(lines),
    }
    if not sentences:
        return m, loc, stats

    def add_loc(key: str, index: int, snippet: str) -> None:
        loc.setdefault(key, [])
        if len(loc[key]) < 6:
            snippet = snippet.strip().replace("\n", " ")
            loc[key].append({
                "sentence": index,
                "snippet": snippet[:60] + ("…" if len(snippet) > 60 else ""),
            })

    lens = [cjk_len(s) for s in sentences]
    m["sent_len_mean"] = round(statistics.fmean(lens), 1)
    m["sent_len_cv"] = round(cv(lens), 3)
    m["short_sent_ratio"] = round(sum(1 for x in lens if x < 15) / len(lens), 3)
    m["long_sent_ratio"] = round(sum(1 for x in lens if x > 45) / len(lens), 3)

    run = best = 1
    best_at = 0
    for i in range(1, len(lens)):
        prev, cur = lens[i - 1], lens[i]
        if prev and abs(cur - prev) <= 0.2 * prev:
            run += 1
            if run > best:
                best, best_at = run, i
        else:
            run = 1
    m["max_uniform_run"] = best
    if best > 4:
        lo = max(0, best_at - best + 1)
        add_loc("max_uniform_run", lo, sentences[lo])

    plens = [cjk_len(p) for p in paragraphs] or [0]
    m["para_len_cv"] = round(cv(plens), 3)
    solo = sum(1 for p in paragraphs if len(split_sentences(p)) <= 1)
    m["solo_para_ratio"] = round(solo / max(len(paragraphs), 1), 3)

    openers = [re.sub(r"[^" + CJK + r"A-Za-z]", "", s)[:2] for s in sentences]
    openers = [o for o in openers if len(o) == 2]
    dup = len(openers) - len(set(openers))
    m["opener_repeat_ratio"] = round(dup / max(len(openers), 1), 3)

    trans_total = 0
    for i, s in enumerate(sentences):
        hit = [w for w in TRANSITION_WORDS if w in s]
        trans_total += len(hit)
        if hit:
            add_loc("transition_density", i, f"[{'/'.join(hit[:3])}] {s}")
    m["transition_density"] = round(trans_total / len(sentences), 3)

    def scan(patterns: Sequence[str], key: str) -> int:
        total = 0
        for pat in patterns:
            rx = re.compile(pat)
            for i, s in enumerate(sentences):
                for mo in rx.finditer(s):
                    total += 1
                    add_loc(key, i, f"[{mo.group(0)[:14]}] {s}")
        return total

    m["hard_phrase_per_1k"] = per_1k(scan(HARD_PHRASES, "hard_phrase_per_1k"))
    m["soft_phrase_per_1k"] = per_1k(scan(SOFT_PHRASES, "soft_phrase_per_1k"))
    m["idiom4_per_1k"] = per_1k(scan([re.escape(w) for w in IDIOM_4CHAR], "idiom4_per_1k"))
    m["hedge_per_1k"] = per_1k(sum(prose.count(w) for w in HEDGE_WORDS))

    tails = TAIL_NOMINALIZATION.findall(prose)
    m["tail_nominal_per_1k"] = per_1k(len(tails))
    for t in tails[:6]:
        add_loc("tail_nominal_per_1k", -1, t)

    negs = NEGATIVE_PARALLEL.findall(prose)
    m["neg_parallel_per_1k"] = per_1k(len(negs))
    for i, s in enumerate(sentences):
        if NEGATIVE_PARALLEL.search(s):
            add_loc("neg_parallel_per_1k", i, s)

    threes = RULE_OF_THREE.findall(prose)
    m["rule_of_three_per_1k"] = per_1k(len(threes))
    for t in threes[:6]:
        add_loc("rule_of_three_per_1k", -1, t)

    non_empty = [l for l in lines if l.strip()]
    n_lines = max(len(non_empty), 1)
    inline = [l for l in non_empty if INLINE_HEADING.match(l)]
    m["inline_heading_ratio"] = round(len(inline) / n_lines, 3)
    for l in inline[:6]:
        add_loc("inline_heading_ratio", -1, l)

    bullets = [l for l in non_empty if re.match(r"^\s*(?:[-*+]\s+|\d+[.、)]\s+)", l)]
    m["bullet_ratio"] = round(len(bullets) / n_lines, 3)
    blens = [cjk_len(re.sub(r"^\s*(?:[-*+]\s+|\d+[.、)]\s+)", "", l)) for l in bullets]
    m["list_item_len_cv"] = round(cv(blens), 3) if len(blens) >= 3 else 1.0

    m["bold_per_1k"] = per_1k(len(BOLD_SPAN.findall(text)))
    m["heading_per_1k"] = per_1k(len(re.findall(r"^\s{0,3}#{1,6}\s+", text, flags=re.M)))

    m["digit_per_1k"] = per_1k(len(re.findall(r"\d+(?:[.:]\d+)*", prose)))
    m["latin_per_1k"] = per_1k(len(LATIN_TOKEN.findall(prose)))
    m["first_person_per_1k"] = per_1k(len(re.findall(r"我(?:们|的|自己)?", prose)))
    m["concrete_anchor_count"] = len(CONCRETE_ANCHOR.findall(prose))

    m["de_ratio"] = round(prose.count("的") / max(chars, 1), 4)
    m["colon_per_1k"] = per_1k(prose.count("：") + prose.count(":"))
    m["emoji_per_1k"] = per_1k(len(EMOJI.findall(text)))

    lone = LONE_DASH.findall(prose)
    m["lone_dash_per_1k"] = per_1k(len(lone))
    # 超出的引号体系数：用 1 套是正常的，2 套以上才是机器痕迹
    systems_used = sum(1 for pat in QUOTE_SYSTEMS if pat.search(prose))
    m["quote_style_mixed"] = max(0, systems_used - 1)

    stats["stance_hits"] = sum(prose.count(w) for w in STANCE_WORDS)
    return m, loc, stats


# ── 判定 ────────────────────────────────────────────────────────────────

def resolve_bands(profile: str, baseline: Optional[dict]) -> Dict[str, dict]:
    bands = {k: dict(v) for k, v in BASE_BANDS.items()}
    bands.update({k: dict(v) for k, v in PROFILES.get(profile, {}).get("bands", {}).items()})
    if baseline:
        for k, v in (baseline.get("bands") or {}).items():
            if k in bands:
                bands[k] = v
    return bands


def _inside(value: float, band: Optional[Sequence]) -> bool:
    if not band:
        return True
    lo, hi = band[0], band[1]
    if lo is not None and value < lo:
        return False
    if hi is not None and value > hi:
        return False
    return True


def judge(metrics: Dict[str, float], bands: Dict[str, dict]) -> Dict[str, dict]:
    verdict = {}
    for key, value in metrics.items():
        band = bands.get(key)
        if not band:
            verdict[key] = {"value": value, "status": "info", "target": None}
            continue
        if _inside(value, band["target"]):
            status = "pass"
        elif _inside(value, band["warn"]):
            status = "warn"
        else:
            status = "fail"
        verdict[key] = {"value": value, "status": status,
                        "target": band["target"], "warn": band["warn"]}
    return verdict


def pressure(rows) -> int:
    """累计压力分：fail 记 2 分，warn 记 1 分。"""
    items = rows.values() if isinstance(rows, dict) else rows
    return sum(2 if v["status"] == "fail" else 1 if v["status"] == "warn" else 0
               for v in items)


# 整篇判定的标尺：同一批 351 篇真人长文在**各自 profile 下**实测的压力分位数。
# 必须按 profile 分别记录——收紧 profile 会让整条分布平移（zhuque p75 是 9
# 而 neutral 是 6），共用一把尺子会把档位偏移误报成文本失败。
#
# 单项越界是 p10/p90 定界的设计内噪声：真人稿 fail 项数中位数就是 1。
# 所以 any-fail 聚合会把 ~66% 的真人稿判死，必须看累计压力。
PROFILE_PRESSURE = {
    "wechat": (7, 9),
    "zhuque": (9, 11),
    "neutral": (6, 9),
    "thesis": (8, 11),
}
DEFAULT_PRESSURE = (7, 9)


def family_rollup(verdict: Dict[str, dict]) -> List[dict]:
    out = []
    for fid, label, keys in FAMILIES:
        rows = [(k, verdict[k]) for k in keys if k in verdict]
        fails = [k for k, v in rows if v["status"] == "fail"]
        warns = [k for k, v in rows if v["status"] == "warn"]
        # 家族只有 5–7 项，同样不做 any-fail：单项越界记为 warn 级提示，
        # 压力分到 4（两项 fail，或一项 fail 加两项 warn）才算这一族失守。
        p = pressure([v for _, v in rows])
        status = "fail" if p >= 4 else ("warn" if p >= 2 else "pass")
        out.append({"id": fid, "label": label, "status": status,
                    "pressure": p, "fail": fails, "warn": warns,
                    "metrics": [{"key": k, **v} for k, v in rows]})
    return out


def resolve_pressure_ref(profile: str, baseline: Optional[dict]) -> Tuple[int, int]:
    """标尺与区间必须同源：用了个人基线，就用基线自带的压力分位数。"""
    if baseline:
        ref = baseline.get("pressure_reference") or {}
        p75, p90 = ref.get("p75"), ref.get("p90")
        if p75 is not None and p90 is not None:
            return int(p75), int(p90)
    return PROFILE_PRESSURE.get(profile, DEFAULT_PRESSURE)


def overall(verdict: Dict[str, dict], profile: str = "wechat",
            baseline: Optional[dict] = None) -> str:
    """整篇判定：与同源真人语料的压力分布比较，而非逐项一票否决。

    pass = 压力不高于真人 p75；warn = 到真人 p90；fail = 超出真人 p90。
    所以 fail 的含义是「越界密度已超过 90% 的真人长文」，
    不是「检测到 AI」——本引擎不做身份判定，只做分布定位。
    """
    p75, p90 = resolve_pressure_ref(profile, baseline)
    p = pressure(verdict)
    if p <= p75:
        return "pass"
    if p <= p90:
        return "warn"
    return "fail"


# ── 报告 ────────────────────────────────────────────────────────────────

MARK = {"pass": "[PASS]", "warn": "[WARN]", "fail": "[FAIL]", "info": "[INFO]"}


def fmt_band(band) -> str:
    if not band:
        return "-"
    lo, hi = band
    if lo is not None and hi is not None:
        return f"{lo} ~ {hi}"
    if lo is not None:
        return f">= {lo}"
    if hi is not None:
        return f"<= {hi}"
    return "-"


def report_text(payload: dict, show_loc: bool) -> str:
    out: List[str] = []
    s = payload["stats"]
    out.append("=" * 68)
    out.append(f"lov-human-writing 度量报告   profile={payload['profile']}")
    out.append(f"基线来源: {payload['baseline_provenance']}")
    out.append(f"字数 {s['char_count']}  句 {s['sentence_count']}  段 {s['paragraph_count']}")
    out.append("=" * 68)
    for fam in payload["families"]:
        out.append(f"\n{MARK[fam['status']]} {fam['label']}")
        for row in fam["metrics"]:
            out.append(
                f"  {MARK[row['status']]} {LABELS.get(row['key'], row['key']):<32}"
                f" {row['value']:<8} 目标 {fmt_band(row['target'])}"
            )
    if show_loc and payload["locations"]:
        out.append("\n" + "-" * 68)
        out.append("命中定位（改写靶点）")
        for key, items in payload["locations"].items():
            if key not in payload["failing_keys"]:
                continue
            out.append(f"\n  {LABELS.get(key, key)}")
            for it in items:
                where = f"句{it['sentence']}" if it["sentence"] >= 0 else "全文"
                out.append(f"    - {where}: {it['snippet']}")
    out.append("\n" + "=" * 68)
    ref = payload["pressure_reference"]
    out.append(f"总判定: {MARK[payload['overall']]}   "
               f"压力分 {payload['pressure']}"
               f"（真人基准 p75={ref['human_p75']} / p90={ref['human_p90']}）")
    out.append(f"  未通过 {len(payload['failing_keys'])} 项 / 警告 "
               f"{len(payload['warning_keys'])} 项 · fail 记 2 分、warn 记 1 分")
    out.append(f"  基准语料: {ref['corpus']}。单项越界属定界噪声，"
               f"真人稿中位数亦踩中 1 项，故判定看累计压力而非逐项否决。")
    out.append("  本引擎只做分布定位，不做「是否 AI 生成」的身份判定。")
    if payload["failing_keys"]:
        out.append("需要定向改写的指标: " + ", ".join(
            LABELS.get(k, k) for k in payload["failing_keys"]))
    out.append("=" * 68)
    return "\n".join(out)


def build_payload(text: str, profile: str, baseline: Optional[dict]) -> dict:
    metrics, locations, stats = compute(text)
    if not metrics:
        return {"schema": SCHEMA, "error": "文本过短或无法解析出句子", "stats": stats}
    bands = resolve_bands(profile, baseline)
    verdict = judge(metrics, bands)
    families = family_rollup(verdict)
    failing = [k for k, v in verdict.items() if v["status"] == "fail"]
    warning = [k for k, v in verdict.items() if v["status"] == "warn"]
    total = pressure(verdict)
    ref_p75, ref_p90 = resolve_pressure_ref(profile, baseline)
    using_baseline = bool(
        baseline and (baseline.get("pressure_reference") or {}).get("p75") is not None)
    return {
        "schema": SCHEMA,
        "profile": profile,
        "profile_label": PROFILES.get(profile, {}).get("label", profile),
        "baseline_provenance": (baseline or {}).get("provenance", "empirical-default"),
        "stats": stats,
        "metrics": metrics,
        "verdict": verdict,
        "families": families,
        "locations": locations,
        "failing_keys": failing,
        "warning_keys": warning,
        "pressure": total,
        "pressure_reference": {
            "human_p75": ref_p75,
            "human_p90": ref_p90,
            "corpus": (f"个人基线 {baseline.get('sample_count', '?')} 篇"
                       if using_baseline else "351 篇真人中文长文（同 profile 实测）"),
        },
        "overall": overall(verdict, profile, baseline),
    }


def compare(new: dict, old: dict) -> str:
    out = ["=" * 68, "版本对比（旧 -> 新）", "=" * 68]
    keys = [k for _, _, ks in FAMILIES for k in ks]
    for k in keys:
        a = old.get("metrics", {}).get(k)
        b = new.get("metrics", {}).get(k)
        if a is None or b is None:
            continue
        if abs(b - a) < 1e-9:
            continue
        sa = old["verdict"][k]["status"]
        sb = new["verdict"][k]["status"]
        flag = "" if sa == sb else f"  {sa} -> {sb}"
        out.append(f"  {LABELS.get(k, k):<32} {a} -> {b}{flag}")
    out.append("-" * 68)
    out.append(f"  总判定 {old.get('overall')} -> {new.get('overall')}")
    out.append(f"  未通过项 {len(old.get('failing_keys', []))} -> {len(new.get('failing_keys', []))}")
    out.append("=" * 68)
    return "\n".join(out)


# ── 个人基线校准 ────────────────────────────────────────────────────────

def calibrate(paths: List[Path], profile: str) -> dict:
    samples: Dict[str, List[float]] = {}
    used = []
    collected: List[Dict[str, float]] = []
    for p in paths:
        try:
            metrics, _, stats = compute(p.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        if not metrics or stats["char_count"] < 400:
            continue
        used.append(p.name)
        collected.append(metrics)
        for k, v in metrics.items():
            samples.setdefault(k, []).append(v)
    if len(used) < MIN_CALIBRATION_SAMPLES:
        raise SystemExit(
            f"ERROR: 只找到 {len(used)} 篇可用稿件，至少需要 "
            f"{MIN_CALIBRATION_SAMPLES} 篇 400 字以上的真人稿件。"
            "样本太少时分位数由个别极端稿件主导，基线会比默认区间更不可靠。"
        )

    def quant(vals: List[float], q: float) -> float:
        vals = sorted(vals)
        pos = q * (len(vals) - 1)
        lo = math.floor(pos)
        hi = math.ceil(pos)
        if lo == hi:
            return vals[lo]
        return vals[lo] + (vals[hi] - vals[lo]) * (pos - lo)

    base = resolve_bands(profile, None)
    bands = {}
    for k, vals in samples.items():
        band = base.get(k)
        if not band:
            continue
        # 必须与 BASE_BANDS 同一套约定：target=p10/p90、warn=p5/p95。
        # 用 p25/p75 做 target 会让用户自己的稿件有约 25% 的单项越界率，
        # 压力分均值升到 10 上下，越过 PROFILE_PRESSURE 的 fail 门——
        # 即「拿自己的文风校准，反被判成 AI」。分位数换了，标尺却没换。
        p05, p10, p90, p95 = (quant(vals, q) for q in (0.05, 0.10, 0.90, 0.95))
        lo_t, hi_t = band["target"]

        hi_target, hi_warn = None, None
        if hi_t is not None:
            hi_target, hi_warn = round(p90, 4), round(p95, 4)
            # 退化情形：该指标在样本里几乎恒为 0（四字格套话、尾部名词化），
            # p90 也是 0，照搬会变成零容忍——首次出现就判 fail。
            # 退回默认的近零上界，它已经处理过这个问题。
            if hi_target == 0:
                hi_target, hi_warn = hi_t, band["warn"][1]

        target = [round(p10, 4) if lo_t is not None else None, hi_target]
        warn = [round(p05, 4) if lo_t is not None else None, hi_warn]
        bands[k] = {"target": target, "warn": warn}

    note = None
    if len(used) < RECOMMENDED_CALIBRATION_SAMPLES:
        note = (f"样本仅 {len(used)} 篇，低于建议的 "
                f"{RECOMMENDED_CALIBRATION_SAMPLES} 篇；尾部分位数噪声较大。")

    # 基线必须自带判定标尺。PROFILE_PRESSURE 是按 BASE_BANDS 标定的，
    # 换成个人基线后压力分布会平移，沿用原标尺等于用别人的尺子量自己
    # ——与 profile 各自校准标尺是同一个道理。
    merged = {k: dict(v) for k, v in base.items()}
    merged.update({k: dict(v) for k, v in bands.items()})
    pressures = [pressure(judge(m, merged)) for m in collected]

    return {
        "schema": "lov-human-writing/baseline/v1",
        "provenance": f"calibrated from {len(used)} human-written samples",
        "quantile_convention": "target=p10/p90, warn=p05/p95 (matches BASE_BANDS)",
        "profile": profile,
        "sample_count": len(used),
        "note": note,
        "pressure_reference": {
            "p75": round(quant(pressures, 0.75)) if pressures else None,
            "p90": round(quant(pressures, 0.90)) if pressures else None,
        },
        "samples": used,
        "bands": bands,
    }


# ── CLI ─────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Deterministic Chinese prose metrics")
    ap.add_argument("--input", "-i", help="待度量的 .md / .txt 文件")
    ap.add_argument("--text", "-t", help="直接传入文本")
    ap.add_argument("--compare", "-c", help="对比的旧版本文件")
    ap.add_argument("--profile", "-p", default="wechat",
                    choices=sorted(PROFILES), help="阈值 profile")
    ap.add_argument("--baseline", "-b", help="个人基线 JSON（覆盖默认经验区间）")
    ap.add_argument("--format", "-f", default="text", choices=["text", "json"])
    ap.add_argument("--no-locate", action="store_true", help="不输出命中定位")
    ap.add_argument("--calibrate", help="用一个目录下的真人稿件生成个人基线")
    ap.add_argument("--out", help="--calibrate 的输出路径")
    return ap.parse_args()


def load_baseline(path: Optional[str]) -> Optional[dict]:
    if not path:
        return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != "lov-human-writing/baseline/v1":
        raise SystemExit(f"ERROR: 不是合法的基线文件: {path}")
    return data


def main() -> int:
    args = parse_args()

    if args.calibrate:
        root = Path(args.calibrate).expanduser()
        files = sorted([p for p in root.rglob("*") if p.suffix in {".md", ".txt"}])
        result = calibrate(files, args.profile)
        text = json.dumps(result, ensure_ascii=False, indent=2)
        if args.out:
            Path(args.out).expanduser().write_text(text + "\n", encoding="utf-8")
            print(f"baseline={args.out}  samples={len(result['samples'])}")
        else:
            print(text)
        return 0

    if args.text:
        body = args.text
    elif args.input:
        p = Path(args.input).expanduser()
        if not p.exists():
            print(f"ERROR: file not found: {p}", file=sys.stderr)
            return 2
        body = p.read_text(encoding="utf-8")
    else:
        body = sys.stdin.read()
    if not body.strip():
        print("ERROR: 需要 --input / --text 或 stdin 输入", file=sys.stderr)
        return 2

    baseline = load_baseline(args.baseline)
    payload = build_payload(body, args.profile, baseline)
    if payload.get("error"):
        print(f"ERROR: {payload['error']}", file=sys.stderr)
        return 2

    if args.compare:
        old_text = Path(args.compare).expanduser().read_text(encoding="utf-8")
        old = build_payload(old_text, args.profile, baseline)
        payload["compare"] = {"path": args.compare, "overall": old.get("overall"),
                              "metrics": old.get("metrics")}
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(report_text(payload, not args.no_locate))
            print()
            print(compare(payload, old))
        return 0 if payload["overall"] != "fail" else 1

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(report_text(payload, not args.no_locate))
    return 0 if payload["overall"] != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
