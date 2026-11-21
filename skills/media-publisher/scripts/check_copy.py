#!/usr/bin/env python3
"""发布文案的离线预检（微信视频号 / Bilibili / 小红书 / 抖音）。

存在的理由只有一个：这些限制全都能在本地算出来，但只有点下去才会被平台告知。
观测到的代价是每撞一次就要一个页面往返（填入 → 失焦 → 读校验提示 → 改写）。

各平台的规则**几乎没有交集**，所以一律按 `--platform` 取：

    python3 check_copy.py --platform wechat-channels --short-title "…" --json
    python3 check_copy.py --platform bilibili --title "…" --topic 架构设计 --json
    python3 check_copy.py --platform xiaohongshu --title "…" --description "…" --topic 南头古城 --json
    python3 check_copy.py --platform douyin --title "…" --description "…" --topic 傅里叶级数 --json

抖音（2026-11-21 一次实测）：标题计数器「0/30」、简介计数器「0 / 1000」，话题连同 `#` 计入简介计数器；
第 6 个话题点了候选不生成节点、只闪一下「最多可添加5个话题」，按原文取 5，超了报 error `topics_too_many`。
抖音的标题和简介在预览里拼成一段（「标题 + 空格 + 简介」），两处别写同一句。

视频号的规则来自平台自己的报错原文，不是推断：

- 「标题超过16字限制」——填入 34 字的推荐标题时返回。
- 「标题至少6个字」——2026-10-12 填入 4 字的「背包九讲」时返回；改成 6 字的
  「背包问题九讲」后提示消失。5 字没有试过，按报错原文取 6 为下限；下限处
  空格、英文字母怎么计数也没有试过，脚本沿用上限的计法（每个字符算 1）。
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
规则，2026-10-12 读到标题计数器「4 / 20」，但实测没有撞到线。话题要在正文里输入 `#` 后从联想列表选，列表里没有的名字会
变成「新建话题」，离线判断不了，所以只给 info 提示；正文里直接写的 `#xxx` 不会成为话题，
报 warn。合集上限未实测，传 `--collection` 会报 warn 级的 `collection_limit_unknown`，
去页面上读输入框 maxLength / 计数器，不阻断预检。

小红书话题最多 10 个：2026-10-29 带 12 个话题点「发布」，前端只闪出提示「最多支持添加10个话题」
（点击后约 0.1 秒出现，很快消失，事后截图里看不到），没有发出发布请求，页面也没有别的变化，看上去就像点击没生效；
删到 10 个后发布成功。11 个没试过，按提示原文取 10，超了报 error `topics_too_many`。

小红书的正文计数器还会算上话题：2026-10-12 正文两句 32 字，加 7 个话题（名称共 25 字，
带 `#` 共 32 字）后读到 `71 /1000`。`#`、换行、空格各算几个没拆开核对，所以同时传了
`--description` 和 `--topic` 时，脚本按「正文（不算换行）+ 话题名（不含 `#`）」估一个下限，超过上限
报 warn `description_with_topics_over_limit`。下限没超也可能在页面上超，接近上限时以页面为准。

小红书不许给其他平台导流（2026-11-22 用户原话「注意小红书平台不能给其他平台导流」）。标题、正文、话题、
合集名里的 URL / 域名报 error `offsite_link`；二维码、扫码、「去某平台搜」、加微信 / 关注公众号一类引导报 error
`offsite_cta`；只提到别的平台名报 warn `offsite_platform_mention`，要人逐条判断。这是关键词检查，换个说法的导流
挡不住，画面、字幕、口播也查不了，那部分按 references/xiaohongshu/platform-constraints.md「禁止站外导流」人工查。

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

# B 站实测被拒的标签名（前三个 2026-08-18，vibecoding 2026-10-06，后者换 AI编程 被接受）。
# 不是字符集问题也不是长度问题，是平台把这些名字划给了话题体系。名单必然不全，页面 toast 才是权威。
BILIBILI_TOPIC_ONLY_TAGS = ("DeepSeekHarness", "独立开发者", "插件开发", "vibecoding")

# ---------------------------------------------------------------------------
# 站外导流（小红书）
# ---------------------------------------------------------------------------

# 别的平台、站点和私域入口的名字。拉丁字母的短名两侧不能紧贴字母，免得「wxyz」「QQQ」误报。
_OFFSITE_PLATFORM = (
    r"(?:微信|公众号|视频号|朋友圈|抖音|快手|[Bb]\s?站|哔哩哔哩|[Bb]ilibili|微博|知乎|淘宝|天猫|京东|拼多多|"
    r"闲鱼|得物|油管|官网|(?<![A-Za-z])(?:YouTube|Youtube|youtube|TikTok|Tiktok|tiktok|GitHub|Github|github|"
    r"QQ|qq|VX|vx|Vx|WX|wx|V信|v信)(?![A-Za-z]))"
)
OFFSITE_PLATFORM_RE = re.compile(_OFFSITE_PLATFORM)

# 二维码、扫码，以及「去 / 到 / 上 某平台 搜 / 找 / 关注 / 看 / 下载」「在某平台搜 / 找 / 关注 / 下载」
# （「在抖音看到」是叙述，不算）、「某平台搜 X / 同名 / 号」「关注 / 加 某平台」。
OFFSITE_CTA_RE = re.compile(
    r"二维码|扫码|扫一扫|搜一搜"
    rf"|(?:去|到|上)\s*{_OFFSITE_PLATFORM}\s*(?:里|上)?\s*(?:搜|找|关注|看|下载)"
    rf"|在\s*{_OFFSITE_PLATFORM}\s*(?:里|上)?\s*(?:搜|找|关注|下载)"
    rf"|{_OFFSITE_PLATFORM}\s*(?:搜索|搜|同名|号)"
    rf"|(?:关注|加|添加|私信)\s*(?:我的?|一下|下)?\s*{_OFFSITE_PLATFORM}"
)

# URL 与裸域名。只认 ASCII 的 URL 字符，免得把紧跟在后面的中文吃进样本；前面紧贴中文（「官网lovstudio.ai」）
# 也要认出来，所以左边界只排除 ASCII 字母数字与 `.` `-`（Python 的 \w 含汉字，不能用）。
# 小红书自己的域名不算站外。
_URL_CHARS = r"[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]"
OFFSITE_URL_RE = re.compile(
    rf"https?://{_URL_CHARS}+|www\.{_URL_CHARS}+"
    r"|(?<![A-Za-z0-9.\-])(?:[A-Za-z0-9-]+\.)+"
    r"(?:com|cn|net|org|ai|io|co|me|app|dev|tv|cc|xyz|top|site|link|info|so|gg|ly)(?![A-Za-z0-9-])"
    rf"(?:/{_URL_CHARS}*)?"
)
OWN_PLATFORM_DOMAINS = ("xiaohongshu.com", "xhslink.com", "xhscdn.com")


def _own_domain(url: str) -> bool:
    host = re.sub(r"^https?://", "", url).split("/", 1)[0].lower()
    return any(host == d or host.endswith("." + d) for d in OWN_PLATFORM_DOMAINS)

PLATFORMS: dict[str, dict[str, Any]] = {
    "wechat-channels": {
        "label": "微信视频号",
        # 平台没有独立的「标题」字段，短标题就是那一个。
        "short_title_max": 16,
        # 「标题至少6个字」（2026-10-12）：4 字被拒、6 字通过，5 字未试。
        "short_title_min": 6,
        "title_max": None,
        "description_max": None,
        "collection_max": {"create": 10, "edit": None},
        "collection_immutable": True,
        "topic_label": "话题",
        "topic_max": None,
        # 平台未给硬上限；与 description-template「5–10 个互补且精准」
        # 及 2026-08-26 用户确认的样本（10 个）对齐。
        "topic_soft_max": 10,
        "topic_refused": (),
        # 描述里的 `#话题` 纯文本不会被解析成话题标签，必须走工具栏按钮生成。
        "inline_hashtag_not_topic": True,
        "inline_hashtag_message": (
            "描述文本里出现 {count} 处 `#…`：平台不会把纯文本解析成话题，"
            "必须点编辑区工具栏「#话题」按钮让平台生成标签节点。"
            "若这些就是本次话题，改用 --topic 传入并在页面上逐个生成"
        ),
        "source": "平台报错原文与创建页计数器（2026-08-17 读取；短标题下限 2026-10-12 报错原文）",
    },
    "bilibili": {
        "label": "Bilibili",
        "short_title_max": None,
        "short_title_min": None,
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
        "short_title_min": None,
        # 2026-10-12 读到标题计数器「4 / 20」，上限与公开规则一致；没有撞过线，
        # 超限时页面怎么提示不知道，所以报错不套 B 站那种「n/80」口径。
        "title_max": 20,
        "title_basis": "页面计数器「n / 20」，未撞线实测",
        # 发布页计数器「n /1000」（2026-10-01 实测读取）。
        "description_max": 1000,
        # 合集上限未实测：两个阶段都给 None，check_collection 报 warn 级的
        # collection_limit_unknown，提示去页面上读，不用猜的数字放行，也不把预检卡死。
        "collection_max": {"create": None, "edit": None},
        "collection_immutable": None,  # 未知
        "topic_label": "话题",
        # 提示原文「最多支持添加10个话题」（2026-10-29）：12 个被拦下，删到 10 个后发布成功，11 个没试过。
        "topic_max": 10,
        "topic_max_note": (
            "页面原文「最多支持添加10个话题」。超了点「发布」只闪一下这句提示、不发请求，"
            "看上去像没点上——先删到 10 个，不要连点或交接"
        ),
        "topic_soft_max": None,
        "topic_refused": (),
        "topic_notice": (
            "小红书话题要在正文输入 # 后从联想列表里选；列表里没有的名字会变成「新建话题」，"
            "离线无法判断是否已存在——填完读一次页面上的话题节点"
        ),
        # 粘贴进正文的 `#xxx` 纯文本不会变成话题节点。
        "inline_hashtag_not_topic": True,
        # 正文计数器 n /1000 把话题文本也算进去（2026-10-12：32 字正文 + 7 个话题读到 71）。
        "counter_includes_topics": True,
        "inline_hashtag_message": (
            "正文里的 {samples} 不会自动成为话题；"
            "话题请用 --topic 并在页面从 # 联想列表点选，正文去掉行内 #"
        ),
        # 2026-11-22 用户原话「注意小红书平台不能给其他平台导流」；平台规则原文没在页面上核对。
        "no_offsite_diversion": True,
        "source": "小红书创作服务平台发布页计数器（正文 2026-10-01、标题 2026-10-12 读取）与发布时的提示原文（话题上限 2026-10-29）；禁止站外导流为 2026-11-22 用户确认",
    },
    "douyin": {
        "label": "抖音",
        "short_title_max": None,
        "short_title_min": None,
        # 标题输入框后缀计数器「0/30」（2026-11-21）；输入框本身 maxLength 为 -1，没撞过线。
        "title_max": 30,
        "title_basis": "页面计数器「n/30」，未撞线实测",
        # 简介计数器「0 / 1000」（2026-11-21）。
        "description_max": 1000,
        # 账号没有合集，「请选择合集」下拉里只有「不选择合集」，创建合集的表单没打开过。
        "collection_max": {"create": None, "edit": None},
        "collection_immutable": None,
        "topic_label": "话题",
        # 第 6 个话题点了不生成节点，只闪一下「最多可添加5个话题」（2026-11-21，记录器抓到的原文）。
        "topic_max": 5,
        "topic_max_note": (
            "页面原文「最多可添加5个话题」。第 6 个点了候选也不生成节点、只闪一下提示，"
            "输入的 #名称 会留成纯文本——先减到 5 个再填"
        ),
        "topic_soft_max": None,
        "topic_refused": (),
        "topic_notice": (
            "抖音话题要点「#添加话题」后输入名称，从联想列表里点名称全等的一项；"
            "离线判断不了联想里有没有这个名字，填完读一次 [data-mention=\"#\"] 节点"
        ),
        # 2026-11-21：输入后没点上候选的「#Agent」留在简介里是纯文本，不算话题。
        "inline_hashtag_not_topic": True,
        # 简介计数器把话题连同 `#` 算进去（17 字正文 + 换行 + 5 个话题读到 50 / 1000）。
        "counter_includes_topics": True,
        "inline_hashtag_message": (
            "简介里的 {samples} 不会自动成为话题；"
            "话题请用 --topic 并在页面点「#添加话题」从联想列表点选，简介去掉行内 #"
        ),
        "source": "抖音创作者中心发布页计数器与提示原文（2026-11-21 读取）",
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
    """视频号短标题：长度区间硬门禁 + 字符集判定。"""
    limit = spec["short_title_max"]
    if limit is None:
        return _unsupported("短标题", spec)
    minimum = spec.get("short_title_min")

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

    if minimum is not None and n < minimum:
        findings.append({
            "level": "error",
            "code": "short_title_too_short",
            "message": (
                f"短标题 {n} 字，少于平台 {minimum} 字下限"
                f"（页面原文：标题至少{minimum}个字）；需补 {minimum - n} 字，"
                "优先用作品全称或补实词，不要用标点凑数"
            ),
            "actual": n,
            "limit": minimum,
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


def check_description_with_topics(
    text: str, topics: list[str], spec: dict[str, Any]
) -> list[dict]:
    """计数器含话题的平台（小红书）：按正文 + 话题名估计数下限，超上限报 warn。

    只用能确定会被计入的部分做下限：正文里换行以外的字符，和每个话题的名称（不含 `#`）。
    `#`、话题之间的空格、段落换行怎么计没有拆开核对，不加进估计，所以这是下限。
    """
    limit = spec["description_max"]
    if not spec.get("counter_includes_topics") or limit is None or not topics:
        return []
    names = [t.lstrip("#").strip() for t in topics]
    topic_chars = sum(len(n) for n in names)
    body_chars = len(re.sub(r"[\r\n]", "", text))   # 段落换行不计入下限
    floor = body_chars + topic_chars
    if floor <= limit:
        return []
    return [{
        "level": "warn",
        "code": "description_with_topics_over_limit",
        "message": (
            f"正文 {body_chars} 字（不算换行），加上 {len(names)} 个话题的名称 {topic_chars} 字后，"
            f"页面计数器至少 {floor} 字，超过 {limit} 字上限（计数器会算上话题文本，"
            "`#`、空格和换行另计，这只是下限）。先删正文或减话题，填完以页面计数器为准"
        ),
        "estimate_floor": floor,
        "limit": limit,
    }]


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
        note = spec.get("topic_max_note")
        findings.append({
            "level": "error",
            "code": "topics_too_many",
            "message": f"{label} {len(topics)} 个，超过平台 {hard} 个上限" + (f"。{note}" if note else ""),
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
                "这是 description-template 的建议上限，平台未在页面上给出硬上限"
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


def check_offsite_diversion(text: str, spec: dict[str, Any]) -> list[dict]:
    """小红书：文案里的站外链接、导流引导和别的平台名。

    同一段文字只报最重的一类：已经算进 URL 或引导的平台名，不再重复报 mention。
    """
    if not spec.get("no_offsite_diversion") or not text:
        return []

    findings: list[dict] = []
    covered: list[tuple[int, int]] = []

    urls = [m for m in OFFSITE_URL_RE.finditer(text) if not _own_domain(m.group())]
    if urls:
        covered += [m.span() for m in urls]
        samples = [m.group() for m in urls]
        findings.append({
            "level": "error",
            "code": "offsite_link",
            "message": (
                f"{spec['label']}不许给其他平台导流，文案里有链接或域名：{'、'.join(samples[:3])}"
                + (" 等" if len(samples) > 3 else "")
                + "。删掉再发，官网也算站外"
            ),
            "samples": samples[:5],
        })

    def inside(span: tuple[int, int]) -> bool:
        return any(a <= span[0] and span[1] <= b for a, b in covered)

    ctas = [m for m in OFFSITE_CTA_RE.finditer(text) if not inside(m.span())]
    if ctas:
        covered += [m.span() for m in ctas]
        samples = [m.group() for m in ctas]
        findings.append({
            "level": "error",
            "code": "offsite_cta",
            "message": (
                f"{spec['label']}不许给其他平台导流，文案里有站外引导：{'、'.join(samples[:3])}"
                + (" 等" if len(samples) > 3 else "")
                + "。二维码、扫码、「去某平台搜」、加微信 / 关注公众号一类都要删掉"
            ),
            "samples": samples[:5],
        })

    mentions = [m for m in OFFSITE_PLATFORM_RE.finditer(text) if not inside(m.span())]
    if mentions:
        names = list(dict.fromkeys(m.group() for m in mentions))
        findings.append({
            "level": "warn",
            "code": "offsite_platform_mention",
            "message": (
                f"文案提到了别的平台：{'、'.join(names)}。{spec['label']}不许导流，逐条判断："
                "属于导流就删，属于必要叙述也优先改写，留下的列进终稿确认"
            ),
            "samples": names[:5],
        })

    return findings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "发布文案离线预检（视频号 / B 站 / 小红书 / 抖音）。"
            "例：check_copy.py --platform douyin --title … --description … --topic 傅里叶级数 --json"
        ),
    )
    p.add_argument("--platform", choices=sorted(PLATFORMS), default=DEFAULT_PLATFORM,
                   help=f"目标平台，决定全部限制（默认 {DEFAULT_PLATFORM}）")
    p.add_argument("--short-title", default=None,
                   help="视频号短标题，6–16 字且禁用逗号")
    p.add_argument("--title", default=None,
                   help="稿件标题：B 站 ≤80 字，小红书 ≤20 字，抖音 ≤30 字")
    p.add_argument("--description", default=None,
                   help="描述 / 简介 / 正文全文（B 站 ≤2000 字，小红书、抖音 ≤1000 字）")
    p.add_argument("--topic", action="append", default=[], dest="topics",
                   help="一个话题（视频号 / 小红书 / 抖音）或标签（B 站），可重复传入；带不带 # 都可以")
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

    if args.description is not None and args.topics:
        findings += [
            {**f, "field": "description"}
            for f in check_description_with_topics(args.description, args.topics, spec)
        ]

    # 站外导流按字段各查一遍，报告里能看出是哪个字段带的。
    for field, value in (
        ("title", args.title),
        ("description", args.description),
        ("topics", " ".join(args.topics) if args.topics else None),
        ("collection", args.collection),
    ):
        if value is not None:
            findings += [{**f, "field": field} for f in check_offsite_diversion(value, spec)]

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
        "short_title_min": spec["short_title_min"],
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
    if spec.get("no_offsite_diversion"):
        limits["no_offsite_diversion"] = True

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
