#!/usr/bin/env python3
"""发布文案的离线预检（微信视频号 / Bilibili / 小红书）。

存在的理由只有一个：这些限制全都能在本地算出来，但只有点下去才会被平台告知。
观测到的代价是每撞一次就要一个页面往返（填入 → 失焦 → 读校验提示 → 改写）。

各平台的规则**几乎没有交集**，所以一律按 `--platform` 取：

    python3 check_copy.py --platform wechat-channels --short-title "…" --json
    python3 check_copy.py --platform bilibili --title "…" --topic 架构设计 --json
    python3 check_copy.py --platform xiaohongshu --title "…" --description "…" --topic 南头古城 --json

视频号的规则来自平台自己的报错原文，不是推断：

- 「标题超过16字限制」——填入 34 字的推荐标题时返回。
- 「标题包含特殊字符，符号仅支持书名号、引号、冒号、加号、问号、百分号、
  摄氏度，逗号可用空格代替」——填入含中文逗号的 16 字标题时返回。

只有逗号这一条被实际验证过（改成空格后提示消失）。允许集里的其余符号照抄
报错原文，未逐个试过，所以本脚本对不在允许集内的符号只报 warning 而非
error——把没验证过的推断当硬门禁，会拦下平台其实接受的标题。逗号例外，它
是唯一确认会被拒的，报 error。

视频号合集标题的 10 字上限来自「创建合集」弹窗自带的 `0/10` 计数器。它比长度更
重要的一点是**创建后不可修改**（弹窗原文：「合集创建后，标题不可修改」），所以
超长不是截断后照发，而是停下来重新起名。B 站相反：创建弹窗限 20 字，但**编辑
表单限 50 字**，所以先建短名再改成全称是合法路径，`--collection-stage edit`
就是用来核这一步的。

B 站的标签有一类拒绝无法在本地判定：部分名字被划给话题体系，toast 原文
「当前tag为话题专用，不允许自定义添加」。这里只能挡下已实测被拒的名单，新名字
仍要在页面上读 toast。

小红书的正文上限 1000 字来自发布页计数器 `n /1000`（实测）；标题 20 字是平台公开
规则，实测没有撞到线。话题要在正文里输入 `#` 后从联想列表选，列表里没有的名字会
变成「新建话题」，离线判断不了，所以只给 info 提示；正文里直接写的 `#xxx` 不会成为话题，
报 warn。合集上限未实测，传 `--collection` 会报 warn 级的 `collection_limit_unknown`，
去页面上读输入框 maxLength / 计数器，不阻断预检。

退出码 0 表示没有 error（warning 不阻断），1 表示存在 error，2 表示没给字段。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from typing import Any, Callable

# ---------------------------------------------------------------------------
# 视频号短标题的字符集规则
# ---------------------------------------------------------------------------

# 平台报错原文里列出的允许符号。键是报错中的名字，值是对应字符。
ALLOWED_SYMBOLS: dict[str, str] = {
    "书名号": "《》〈〉",
    "引号": "“”‘’「」『』\"'",
    "冒号": "：:",
    "加号": "+",
    "问号": "？?",
    "百分号": "%",
    "摄氏度": "℃",
}

ALLOWED_SYMBOL_CHARS = frozenset("".join(ALLOWED_SYMBOLS.values()))

# 空格计入长度（实测 16 字含两个空格的标题恰好通过），且不属于「特殊字符」。
ALLOWED_WHITESPACE = frozenset(" ")

# 唯一被验证过会被拒的符号，且平台给了明确的替代方案。
CONFIRMED_REJECTED = {
    "，": "半角空格",
    ",": "半角空格",
}

# ---------------------------------------------------------------------------
# 平台限制表
# ---------------------------------------------------------------------------

# B 站实测被拒的标签名（2026-08-18）。不是字符集问题也不是长度问题，
# 是平台把这些名字划给了话题体系。名单必然不全，页面 toast 才是权威。
BILIBILI_TOPIC_ONLY_TAGS = ("DeepSeekHarness", "独立开发者", "插件开发")

PLATFORMS: dict[str, dict[str, Any]] = {
    "wechat-channels": {
        "label": "微信视频号",
        # 平台没有独立的「标题」字段，短标题就是那一个。
        "short_title_max": 16,
        "title_max": None,
        "description_max": None,
        "collection_max": {"create": 10, "edit": None},
        "collection_immutable": True,
        "topic_label": "话题",
        "topic_max": None,
        "topic_soft_max": 5,  # 平台未给硬数字，经验值
        "topic_refused": (),
        # 描述里的 `#话题` 纯文本不会被解析成话题标签，必须走工具栏按钮生成。
        "inline_hashtag_not_topic": True,
        "inline_hashtag_message": (
            "描述文本里出现 {count} 处 `#…`：平台不会把纯文本解析成话题，"
            "必须点编辑区工具栏「#话题」按钮让平台生成标签节点。"
            "若这些就是本次话题，改用 --topic 传入并在页面上逐个生成"
        ),
        "source": "平台报错原文与创建页计数器（2026-08-17 读取）",
    },
    "bilibili": {
        "label": "Bilibili",
        "short_title_max": None,
        "title_max": 80,
        "description_max": 2000,
        # 创建弹窗 maxLength=20，编辑表单 maxLength=50，两者不同且都实测过。
        "collection_max": {"create": 20, "edit": 50},
        "collection_immutable": False,
        "topic_label": "标签",
        "topic_max": 10,
        "topic_soft_max": None,
        "topic_refused": BILIBILI_TOPIC_ONLY_TAGS,
        # 标签是独立字段，简介里的 # 只是普通文字，不需要提醒。
        "inline_hashtag_not_topic": False,
        "source": "投稿页计数器与 maxLength 实测（2026-08-18 读取）",
    },
    "xiaohongshu": {
        "label": "小红书",
        "short_title_max": None,
        # 平台公开规则，实测没有撞到线；页面计数器未核对，所以报错不写成「n/20」。
        "title_max": 20,
        "title_basis": "平台公开规则，未实测撞线",
        # 发布页计数器「n /1000」（2026-10-01 实测读取）。
        "description_max": 1000,
        # 合集上限未实测：两个阶段都给 None，check_collection 报 warn 级的
        # collection_limit_unknown，提示去页面上读，不用猜的数字放行，也不把预检卡死。
        "collection_max": {"create": None, "edit": None},
        "collection_immutable": None,  # 未知
        "topic_label": "话题",
        # 话题数量上限未知，页面没有给数字，也未实测；不设硬上限和经验值。
        "topic_max": None,
        "topic_soft_max": None,
        "topic_refused": (),
        "topic_notice": (
            "小红书话题要在正文输入 # 后从联想列表里选；列表里没有的名字会变成「新建话题」，"
            "离线无法判断是否已存在——填完读一次页面上的话题节点"
        ),
        # 粘贴进正文的 `#xxx` 纯文本不会变成话题节点。
        "inline_hashtag_not_topic": True,
        "inline_hashtag_message": (
            "正文里的 {samples} 不会自动成为话题；"
            "话题请用 --topic 并在页面从 # 联想列表点选，正文去掉行内 #"
        ),
        "source": "小红书创作服务平台发布页计数器（2026-10-01 读取）；标题 20 字为平台公开规则",
    },
}

DEFAULT_PLATFORM = "wechat-channels"


def _is_wordlike(ch: str) -> bool:
    """字母、数字、CJK 等「正文字符」，不属于符号。"""
    cat = unicodedata.category(ch)
    # L* 字母、N* 数字、M* 组合记号。
    return cat[0] in {"L", "N", "M"}


def _unsupported(field: str, spec: dict[str, Any]) -> list[dict]:
    return [{
        "level": "error",
        "code": "field_not_on_platform",
        "message": f"{spec['label']} 没有 {field} 这个字段，传了说明平台选错了",
    }]


# ---------------------------------------------------------------------------
# 逐字段检查
# ---------------------------------------------------------------------------

def check_short_title(text: str, spec: dict[str, Any]) -> list[dict]:
    """视频号短标题：长度硬门禁 + 字符集判定。"""
    limit = spec["short_title_max"]
    if limit is None:
        return _unsupported("短标题", spec)

    findings: list[dict] = []
    n = len(text)

    if not text.strip():
        return [{
            "level": "error",
            "code": "short_title_empty",
            "message": "短标题为空",
        }]

    if n > limit:
        findings.append({
            "level": "error",
            "code": "short_title_too_long",
            "message": (
                f"短标题 {n} 字，超过平台 {limit} 字限制"
                f"（页面原文：标题超过{limit}字限制）；需删 {n - limit} 字"
            ),
            "actual": n,
            "limit": limit,
        })

    for ch in dict.fromkeys(text):  # 去重但保持出现顺序
        if ch in CONFIRMED_REJECTED:
            findings.append({
                "level": "error",
                "code": "short_title_rejected_symbol",
                "message": (
                    f"短标题含 {ch!r}，平台已确认拒绝；"
                    f"用{CONFIRMED_REJECTED[ch]}代替停顿"
                ),
                "char": ch,
            })
            continue
        if ch in ALLOWED_WHITESPACE or ch in ALLOWED_SYMBOL_CHARS:
            continue
        if _is_wordlike(ch):
            continue
        findings.append({
            "level": "warn",
            "code": "short_title_unverified_symbol",
            "message": (
                f"短标题含 {ch!r}，不在平台报错列出的允许集内"
                "（书名号、引号、冒号、加号、问号、百分号、摄氏度）。"
                "该符号未被实测验证过，填入后请读一次页面校验提示"
            ),
            "char": ch,
        })

    return findings


def check_title(text: str, spec: dict[str, Any]) -> list[dict]:
    """B 站 / 小红书标题：只有长度上限，没有观测到字符集限制。"""
    limit = spec["title_max"]
    if limit is None:
        return _unsupported("稿件标题", spec)

    if not text.strip():
        return [{
            "level": "error",
            "code": "title_empty",
            "message": "稿件标题为空",
        }]

    n = len(text)
    if n > limit:
        basis = spec.get("title_basis") or f"页面计数器 n/{limit}"
        return [{
            "level": "error",
            "code": "title_too_long",
            "message": (
                f"稿件标题 {n} 字，超过 {limit} 字上限（{basis}）；"
                f"需删 {n - limit} 字"
            ),
            "actual": n,
            "limit": limit,
        }]

    return [{
        "level": "info",
        "code": "title_ok",
        "message": (
            f"稿件标题 {n}/{limit} 字。注意本上限未逐字撞过，"
            "接近上限时以页面计数器为准"
        ),
    }]


def check_collection(
    name: str, spec: dict[str, Any], stage: str
) -> list[dict]:
    """合集标题。上限按 `stage`（创建 / 编辑）取，两者不一定相同。"""
    if all(v is None for v in spec["collection_max"].values()):
        # 平台的合集上限整个没实测过（小红书）：这不是文案的错，改文案也修不好，
        # 所以只报 warn，让人去页面读真实上限，不能把预检卡成 fail。
        if not name.strip():
            return [{
                "level": "error",
                "code": "collection_empty",
                "message": "合集标题为空",
            }]
        return [{
            "level": "warn",
            "code": "collection_limit_unknown",
            "message": f"{spec['label']}合集标题上限未实测，去页面读输入框 maxLength / 计数器",
            "actual": len(name),
            "stage": stage,
        }]

    limit = spec["collection_max"].get(stage)
    if limit is None:
        return [{
            "level": "error",
            "code": "collection_stage_unavailable",
            "message": (
                f"{spec['label']} 没有可用的「{stage}」阶段合集上限"
                + ("（创建后标题不可修改）" if spec["collection_immutable"] else "")
            ),
        }]

    if not name.strip():
        return [{
            "level": "error",
            "code": "collection_empty",
            "message": "合集标题为空",
        }]

    n = len(name)
    if n <= limit:
        note = (
            "注意创建后**不可修改**，确认这个名字要跟着整个系列走再建"
            if spec["collection_immutable"]
            else "创建后仍可在「编辑合集」里改名，改名不影响稿件归属"
        )
        return [{
            "level": "info",
            "code": "collection_ok",
            "message": f"合集标题 {n}/{limit} 字（{stage} 阶段）。{note}",
        }]

    if spec["collection_immutable"]:
        advice = (
            f"合集创建后标题不可修改，因此不要截断后照建——"
            f"先重新起一个 ≤{limit} 字的名字，或本期先不挂合集、之后补挂"
        )
    else:
        edit_limit = spec["collection_max"].get("edit")
        if stage == "create" and edit_limit and edit_limit > limit:
            advice = (
                f"但「编辑合集」表单限 {edit_limit} 字：先用短名建，"
                f"再进编辑表单改成这个全称。不要直接降级用短名"
            )
        else:
            advice = f"需删 {n - limit} 字"

    return [{
        "level": "error",
        "code": "collection_too_long",
        "message": f"合集标题 {n} 字，超过 {stage} 阶段的 {limit} 字上限。{advice}",
        "actual": n,
        "limit": limit,
        "stage": stage,
    }]


def check_description(text: str, spec: dict[str, Any]) -> list[dict]:
    findings: list[dict] = []
    if not text.strip():
        return [{
            "level": "error",
            "code": "description_empty",
            "message": "描述为空",
        }]

    limit = spec["description_max"]
    n = len(text)
    if limit is not None and n > limit:
        findings.append({
            "level": "error",
            "code": "description_too_long",
            "message": (
                f"简介 {n} 字，超过 {limit} 字上限（页面计数器 n/{limit}）；"
                f"需删 {n - limit} 字"
            ),
            "actual": n,
            "limit": limit,
        })

    # 视频号 / 小红书：描述里的 `#话题` 纯文本不会变成话题节点，平台各有生成入口。
    if spec["inline_hashtag_not_topic"]:
        inline = re.findall(r"#[^\s#]+", text)
        if inline:
            samples = "、".join(inline[:3]) + (" 等" if len(inline) > 3 else "")
            findings.append({
                "level": "warn",
                "code": "description_inline_hashtag",
                "message": spec["inline_hashtag_message"].format(
                    count=len(inline), samples=samples
                ),
                "samples": inline[:5],
            })

    return findings


def check_topics(topics: list[str], spec: dict[str, Any]) -> list[dict]:
    label = spec["topic_label"]
    findings: list[dict] = []
    if not topics:
        return [{
            "level": "error",
            "code": "topics_empty",
            "message": f"{label}为空，publish 默认要求至少一个",
        }]

    seen: dict[str, int] = {}
    for t in topics:
        key = t.lstrip("#")
        seen[key] = seen.get(key, 0) + 1
    dupes = [k for k, v in seen.items() if v > 1]
    if dupes:
        findings.append({
            "level": "error",
            "code": "topics_duplicated",
            "message": f"{label}重复：{'、'.join(dupes)}",
        })

    refused = {r.casefold() for r in spec["topic_refused"]}
    for t in topics:
        bare = t.lstrip("#").strip()
        if bare.casefold() in refused:
            findings.append({
                "level": "error",
                "code": "topic_reserved_for_topics",
                "message": (
                    f"{label} {bare!r} 已实测被拒：「当前tag为话题专用，不允许自定义添加」。"
                    "换同义词，不要重试同一个名字"
                ),
                "tag": bare,
            })
        if " " in t.strip():
            findings.append({
                "level": "warn",
                "code": "topic_contains_space",
                "message": f"{label} {t!r} 含空格，平台可能在空格处断开",
            })

    hard = spec["topic_max"]
    if hard is not None and len(topics) > hard:
        findings.append({
            "level": "error",
            "code": "topics_too_many",
            "message": f"{label} {len(topics)} 个，超过平台 {hard} 个上限",
            "actual": len(topics),
            "limit": hard,
        })

    soft = spec["topic_soft_max"]
    if soft is not None and len(topics) > soft:
        findings.append({
            "level": "warn",
            "code": "topics_many",
            "message": (
                f"{label} {len(topics)} 个，超过建议的 {soft} 个。"
                "这是经验值，平台未在页面上给出硬上限"
            ),
        })

    if refused:
        findings.append({
            "level": "info",
            "code": "topic_refusal_list_partial",
            "message": (
                "话题专用名单只覆盖已实测被拒的名字，新名字仍可能在页面上被拒——"
                "填完标签要读一次 toast，不能只看请求返回"
            ),
        })

    notice = spec.get("topic_notice")
    if notice:
        findings.append({
            "level": "info",
            "code": "topic_pick_from_suggestions",
            "message": notice,
        })

    return findings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "发布文案离线预检（视频号 / B 站 / 小红书）。"
            "例：check_copy.py --platform xiaohongshu --title … --description … --topic 南头古城 --json"
        ),
    )
    p.add_argument("--platform", choices=sorted(PLATFORMS), default=DEFAULT_PLATFORM,
                   help=f"目标平台，决定全部限制（默认 {DEFAULT_PLATFORM}）")
    p.add_argument("--short-title", default=None,
                   help="视频号短标题，≤16 字且禁用逗号")
    p.add_argument("--title", default=None,
                   help="稿件标题：B 站 ≤80 字，小红书 ≤20 字")
    p.add_argument("--description", default=None,
                   help="描述 / 简介 / 正文全文（B 站 ≤2000 字，小红书 ≤1000 字）")
    p.add_argument("--topic", action="append", default=[], dest="topics",
                   help="一个话题（视频号 / 小红书）或标签（B 站），可重复传入；带不带 # 都可以")
    p.add_argument("--collection", default=None, help="合集标题")
    p.add_argument("--collection-stage", choices=("create", "edit"), default="create",
                   help="合集标题要过哪个表单的上限（默认 create，更严）")
    p.add_argument("--json", action="store_true", help="输出 JSON")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    spec = PLATFORMS[args.platform]

    checks: list[tuple[str, Any, Callable[[Any], list[dict]]]] = [
        ("short_title", args.short_title, lambda v: check_short_title(v, spec)),
        ("title", args.title, lambda v: check_title(v, spec)),
        ("description", args.description, lambda v: check_description(v, spec)),
        ("topics", args.topics or None, lambda v: check_topics(v, spec)),
        ("collection", args.collection,
         lambda v: check_collection(v, spec, args.collection_stage)),
    ]

    findings: list[dict] = []
    checked: list[str] = []
    for field, value, run in checks:
        if value is None:
            continue
        checked.append(field)
        findings += [{**f, "field": field} for f in run(value)]

    if not checked:
        print("未传入任何字段；至少给一个 --short-title / --title / "
              "--description / --topic / --collection",
              file=sys.stderr)
        return 2

    counts = {
        lvl: sum(1 for f in findings if f["level"] == lvl)
        for lvl in ("error", "warn", "info")
    }
    status = "fail" if counts["error"] else "pass"

    limits = {
        "short_title_max": spec["short_title_max"],
        "title_max": spec["title_max"],
        "description_max": spec["description_max"],
        "collection_max": spec["collection_max"],
        "collection_immutable": spec["collection_immutable"],
        "topic_max": spec["topic_max"],
        "topic_soft_max": spec["topic_soft_max"],
        "topic_refused": list(spec["topic_refused"]),
        "source": spec["source"],
    }
    if args.platform == "wechat-channels":
        limits["allowed_symbols"] = ALLOWED_SYMBOLS

    report = {
        "status": status,
        "read_only": True,
        "platform": args.platform,
        "platform_label": spec["label"],
        "checked": checked,
        "counts": counts,
        "findings": findings,
        "limits": limits,
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"platform: {args.platform}（{spec['label']}）")
        print(f"status: {status}  "
              f"error={counts['error']} warn={counts['warn']} info={counts['info']}")
        for f in findings:
            print(f"  [{f['level']}] {f['field']}: {f['message']}")

    return 1 if counts["error"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
