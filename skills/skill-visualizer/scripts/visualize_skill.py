#!/usr/bin/env python3
"""Turn one local Agent Skill into Mermaid diagrams and a JSON logic model."""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover - exercised by CLI preflight
    yaml = None


SCHEMA = "lovstudio/skill-logic/v1"
MERMAID_VERSION = "11.12.2"
MERMAID_BUNDLE = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "vendor"
    / f"mermaid-{MERMAID_VERSION}.min.js"
)
RESOURCE_PREFIXES = ("references/", "scripts/", "assets/", "skills/")
ROOT_RESOURCES = {
    "SKILL.md",
    "skill.yaml",
    "kit.yaml",
    "README.md",
    "CHANGELOG.md",
    "skill-card.yaml",
    "skill-card.md",
    "pricing-card.yaml",
    "cases/cases.json",
}
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
LIST_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)(.+?)\s*$")
ORDERED_RE = re.compile(r"^\s*\d+[.)]\s+(.+?)\s*$")
STEP_RE = re.compile(
    r"^(?:step|阶段|步骤)\s*([0-9]+(?:\.[0-9]+)*)?\s*[:：.\-]?\s*(.*)$",
    re.IGNORECASE,
)
CONDITION_RE = re.compile(
    r"^(if|when|unless|otherwise|else|如果|若|当|仅当|否则|如未|如需|需要时)\s*(.*)$",
    re.IGNORECASE,
)
INLINE_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_./-])"
    r"((?:references|scripts|assets|skills)/[A-Za-z0-9_./-]*[A-Za-z0-9_]"
    r"|(?:SKILL\.md|skill\.yaml|kit\.yaml|README\.md|CHANGELOG\.md|skill-card\.ya?ml|skill-card\.md|pricing-card\.yaml|cases/cases\.json))"
)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
CJK_RE = re.compile(r"[\u3400-\u9fff]")

ZH_DISPLAY_TRANSLATIONS = {
    "从品牌内核出发初始化或重构可运行的 Landing Page，统一定位、叙事、文案、UI、媒体、实现与验收。Use when the user asks to create, optimize, rebrand, or fix a homepage，尤其适用于“产品价值不清”“首页没有品牌感”或“视觉与产品不匹配”。":
        "从品牌内核出发初始化或重构可运行的落地页，统一定位、叙事、文案、界面、媒体、实现与验收；适用于创建、优化、品牌重塑或修复首页，尤其是产品价值不清、首页缺少品牌感或视觉与产品不匹配的情况。",
    "Resolve the real surface": "确认真实页面范围",
    "Verify kit.yaml, selected modules, and referenced documents.": "核验 kit.yaml、已选模块和引用文档。",
    "Inspect the exact repository, route, URL, screenshots, files, and brand assets provided by the user before broad exploration.": "在扩大探索范围前，先检查用户指定的代码库、路由、网址、截图、文件和品牌素材。",
    "Read project instructions and current git state. Preserve unrelated work.": "读取项目指令和当前 Git 状态，保留无关改动。",
    "Identify whether the target is a corporate brand homepage, product Landing Page, campaign, portfolio, creator platform, or authenticated product entry.": "判断目标属于企业品牌首页、产品落地页、营销活动页、作品集、创作者平台还是需登录的产品入口。",
    "Ask one focused question through the host's user-input capability (for example AskUserQuestion where available) only when an unresolved choice would materially change the public result; otherwise proceed from repository truth.": "只有未解决的选择会实质改变公开结果时，才通过宿主能力提出一个聚焦问题；否则依据代码库事实继续。",
    "Select the pipeline": "选择执行管线",
    "| Situation | Pipeline |": "根据当前场景选择对应管线。",
    "New page or product launch → initialize": "新页面或产品发布 → initialize",
    "Existing page should become substantially better → optimize": "现有页面需要显著改善 → optimize",
    "Identity, positioning, copy, and UI all need a new direction → rebrand": "品牌识别、定位、文案和界面都需要新方向 → rebrand",
    "Brand is stable; narrative and copy need a new edition → refresh-copy": "品牌稳定，只需更新叙事与文案 → refresh-copy",
    "Brand is stable; visual media need renewal → refresh-assets": "品牌稳定，只需更新视觉媒体 → refresh-assets",
    "Explicit read-only assessment → audit": "明确要求只读评估 → audit",
    "If the user asks why the page is weak, select optimize: explain the root cause, then fix it. Select audit only when edits are explicitly excluded.": "如果用户询问页面为什么表现不佳，选择 optimize：先说明根因，再完成修复；只有明确排除修改时才选择 audit。",
    "If the user asks why the page is weak": "如果用户询问页面为什么表现不佳",
    "select optimize: explain the root cause, then fix it. Select audit only when edits are explicitly excluded.": "选择 optimize：先说明根因，再完成修复；只有在明确不允许修改时才选择 audit。",
    "Establish the source hierarchy": "建立信息来源层级",
    "Create an internal truth ledger before writing public copy:": "撰写公开文案前，先建立内部事实台账。",
    "approved brand guide, founder/product truth, and existing design system;": "第一层：已批准的品牌指南、创始人或产品事实，以及现有设计系统。",
    "actual product behavior, repository content, live routes, and real assets;": "第二层：真实产品行为、代码库内容、线上路由和真实素材。",
    "verified customer evidence, metrics, cases, and current public statements;": "第三层：已核验的客户证据、指标、案例和当前公开表述。",
    "inferred opportunity, clearly marked internal;": "第四层：推断出的机会，但必须明确标记为内部判断。",
    "evidence gaps that must not become production claims.": "第五层：证据缺口，不得转化为正式对外声明。",
    "Separate every useful input into internal context, publishable claim, verified proof, or open evidence. Never paste the raw brief into the page.": "把每项输入分别归为内部上下文、可公开声明、已核验证据或待补证据；不得把原始需求说明直接贴进页面。",
    "Build the brand foundation": "建立品牌基础",
    "Run the brand module before downstream design. Produce a compact Brand Spine:": "在后续设计前运行品牌模块，形成精炼的品牌主轴（Brand Spine）。",
    "category and audience tension;": "产品类别与受众张力；",
    "belief, promise, mechanism, and meaningful difference;": "品牌信念、承诺、实现机制和有意义的差异；",
    "personality expressed as observable behavior;": "通过可观察行为表达的品牌人格；",
    "one brand thesis the page should leave in memory;": "页面应留在访客记忆中的一个品牌主张；",
    "verbal rules, visual signature, content principles, interaction character;": "语言规则、视觉签名、内容原则和交互性格；",
    "proof anchors, boundaries, and the action that completes the promise.": "证据锚点、表达边界，以及完成承诺的行动。",
    "Classify the offer's product value, mechanism, proof, and distribution/access modes before composing the page. A local architecture may be a meaningful mechanism; a macOS download button is still a delivery control.": "编排页面前，先区分产品价值、实现机制、证据与分发或访问方式。本地架构可能是有意义的机制，但 macOS 下载按钮仍只是交付控件。",
    "For an existing brand, distinguish what is equity to preserve, inconsistency to repair, and generic residue to retire. Read $KIT_DIR/references/brand-system.md for the full decision model.": "对现有品牌，区分需要保留的品牌资产、需要修复的不一致，以及应淘汰的通用残留；完整决策模型见 $KIT_DIR/references/brand-system.md。",
    "Compose the public story": "组织对外叙事",
    "Use the strategy module to turn the Brand Spine into a narrative rather than a": "使用策略模块把品牌主轴转化为叙事，而不是功能罗列。",
    "Use the strategy module to turn the Brand Spine into a narrative rather than a feature inventory. Define:": "使用策略模块把品牌主轴转化为叙事，而不是功能清单，并定义：",
    "the visitor's initial state and desired movement;": "访客的初始状态与期望发生的变化；",
    "a headline spine that tells the story when only headings are scanned;": "只浏览标题也能理解故事的标题主线；",
    "the smallest section sequence needed to reveal belief, product, proof, and action;": "呈现信念、产品、证据与行动所需的最小区块序列；",
    "one primary conversion with a real next state;": "一个具有真实后续状态的主要转化动作；",
    "proof paired to every meaningful claim;": "每项重要声明都配有相应证据；",
    "copy that sounds like this brand and does not expose planning context.": "符合该品牌语气且不泄露规划上下文的文案。",
    "Keep installation, platform, package, pricing, and access-mode choices in an availability or action stage unless one of them changes the actual product promise. Run a distribution-inversion check: after removing platform labels, the hero and headline spine must still explain why the product matters.": "除非安装、平台、软件包、价格或访问方式改变了产品承诺，否则把它们留在可用性或行动阶段。执行分发反转检查：移除平台标签后，首屏和标题主线仍应说明产品为何重要。",
    "The first viewport may lead with a brand belief, an outcome, or an action, but it must still make category, relevance, and next step discoverable without guesswork.": "首屏可以从品牌信念、结果或行动切入，但仍必须让访客无需猜测即可识别产品类别、与自身的关系和下一步。",
    "Create one visual world": "建立统一视觉体系",
    "Use the art-direction module to translate the same Brand Spine into UI and media:": "使用艺术指导模块，把同一品牌主轴落实到界面与媒体。",
    "typographic roles, palette, surfaces, spacing, composition, icon and control grammar;": "字体角色、配色、表面、间距、构图、图标与控件语法；",
    "one ownable visual motif repeated with restraint;": "一个可归属品牌且克制重复的视觉母题；",
    "stage hierarchy that gives major ideas different visual weight;": "让主要观点具有不同视觉权重的舞台层级；",
    "real product imagery and product-specific media treatment;": "真实产品图像和产品专属的媒体处理；",
    "motion that expresses character and has a reduced-motion equivalent.": "能够表达品牌性格且提供弱动效替代的动效。",
    "Before selecting a style, write a compact style-fit rationale covering product category and mechanism, audience and readiness, use environment and emotional state, trust/risk/accessibility needs, existing equity, and authentic assets. Then choose one visual world and reject at least two plausible but less suitable directions. Translate any requested adjectives into product-specific materials, density, typography, composition, imagery, and interaction behavior. Audit Logo assets by visible ink bounds and optical alignment rather than trusting the SVG viewBox or transparent canvas to be visually centered.": "选择风格前，先写出精炼的适配理由，覆盖产品类别与机制、受众与准备度、使用环境与情绪状态、信任风险与无障碍需求、现有品牌资产和真实素材。随后选择一个视觉世界，并排除至少两个看似可行但不够适合的方向。把用户形容词转化为产品专属的材质、密度、字体、构图、图像和交互行为；Logo 对齐以可见墨迹边界和光学校准为准，而不是盲信 SVG viewBox 或透明画布。",
    "Do not solve a brand problem with a generic card grid, default gradient, stock illustration pack, or another company's recognizable visual language.": "不得用通用卡片网格、默认渐变、图库插画包或其他公司的标志性视觉语言解决品牌问题。",
    "Implement the brand as a product": "把品牌落实为产品体验",
    "Use the builder module to make the approved narrative and visual system real:": "使用构建模块实现已确认的叙事与视觉系统。",
    "map brand decisions into reusable tokens and components;": "把品牌决策映射为可复用的设计变量和组件；",
    "preserve semantic HTML, accessibility, localization, and design-system integrity;": "保持语义化 HTML、无障碍、本地化和设计系统完整性；",
    "make primary and repeated actions share one mental model and destination;": "让主要动作和重复动作共享同一心智模型与目的地；",
    "keep prompt inputs IME-safe and connect them to a real result;": "保证提示词输入兼容输入法，并连接到真实结果；",
    "integrate authentic assets with correct crop, loading, alt, and responsive behavior;": "以正确的裁切、加载、替代文本和响应式行为集成真实素材；",
    "align metadata, sharing, footer, analytics, and legal surfaces with the same identity.": "让元数据、分享、页脚、分析和法律页面保持同一品牌身份。",
    "Validate memory, meaning, and mechanics": "验证记忆、含义与运行机制",
    "Use the review module and $KIT_DIR/references/implementation-and-acceptance.md.": "使用审阅模块和 $KIT_DIR/references/implementation-and-acceptance.md 完成验收。",
    "Use the review module and $KIT_DIR/references/implementation-and-acceptance.md. Verify three layers:": "使用审阅模块和 $KIT_DIR/references/implementation-and-acceptance.md 验证三个层面：",
    "Memory: after a short exposure, can a visitor recall the brand thesis, one signature, and one thing the brand enables?": "记忆：短暂浏览后，访客能否回忆品牌主张、一个视觉签名和品牌让其实现的一件事？",
    "Meaning: can they identify category, relevance, proof, and next action?": "含义：访客能否识别产品类别、与自身的关系、证据和下一步行动？",
    "Mechanics: do routes, forms, keyboard, IME, responsive states, performance, metadata, analytics, and error states work?": "运行机制：路由、表单、键盘、输入法、响应式状态、性能、元数据、分析和错误状态是否正常？",
    "Run repository-native quality gates and inspect 320 px, tablet, and desktop. Include at least one common 1280-1440 px desktop width so hero wrapping and Logo placement are observed at realistic sizes. Fix causal problems, then re-run the complete visitor path. When a public page is deployed, read back the production route rather than treating a local build as online verification.": "运行代码库原生质量门，并检查 320px、平板和桌面宽度；至少覆盖一个常见的 1280–1440px 桌面宽度，以观察真实尺寸下的首屏换行和 Logo 位置。修复因果问题后重新运行完整访客路径；公开页面部署后必须回读生产路由，不能把本地构建当作线上验证。",
    "Report the outcome": "报告结果",
    "Lead in the user's language with what changed. Include:": "使用用户语言先说明改动结果，并包含必要证据。",
    "page/route and primary visitor path;": "页面或路由，以及主要访客路径；",
    "Brand Spine and the signature choices expressed in copy, content, UI, and media;": "品牌主轴，以及在文案、内容、界面和媒体中体现的标志性选择；",
    "authentic versus generated assets and remaining proof gaps;": "真实素材与生成素材的区分，以及剩余证据缺口；",
    "commands, viewport/path checks, and observed results;": "执行命令、视口或路径检查和观察结果；",
    "production-only follow-up, without presenting it as completed.": "仅能在生产环境完成的后续事项，不得表述为已经完成。",
    "The user asks to build a branded landing page, rebrand a homepage, or improve its identity, story, UI, and conversion.": "用户要求创建品牌化落地页、重塑首页品牌，或改善品牌识别、叙事、界面与转化。",
    "Infer the product shape": "判断产品形态",
    "Use the request, memory, repository, and supplied examples before asking": "提问前先使用当前请求、记忆、代码库和已有示例判断。",
    "Infer implementation and composition": "判断实现与组合方式",
    "Choose automatically and briefly state the result:": "自动选择，并简要说明结果。",
    "Analyze the nearby Skill group before creating a new one": "创建前分析相邻 Skill 组",
    "Before scaffolding, inspect the local Skill source root and installed Skill": "生成骨架前，检查本地 Skill 源目录和已安装 Skill。",
    "Declare the user Profile contract — always": "始终声明用户 Profile 契约",
    "Every new Skill receives a skill.yaml declaration for user-profile/v1, even": "每个新 Skill 都要在 skill.yaml 中声明 user-profile/v1。",
    "When the user directly states a value intended for future sessions": "当用户直接说明要供后续会话使用的值时",
    "run the generated scripts/profile_store.py record ... --confirm command and report the canonical saved path. Inferred values stay in the current request context.": "运行生成的 scripts/profile_store.py record ... --confirm 命令，并报告规范保存路径；推断值只保留在当前请求上下文。",
    "Plan contents": "规划内容",
    "Deterministic operations → scripts/ as standalone argparse CLIs.": "确定性操作放入 scripts/，实现为独立的 argparse 命令行工具。",
    "Initialize locally": "在本地初始化",
    "Single Skill:": "单一 Skill。",
    "Implement": "实现",
    "Write the source as instructions for an agent, not as notes about this chat:": "把源文件写成面向 Agent 的指令，而不是当前对话的笔记。",
    "Validate and install": "验证并安装",
    "The user asks to create, scaffold, validate, or locally install an Agent Skill.": "用户要求创建、生成骨架、验证或在本地安装 Agent Skill。",
}


def display_text(value: Any, zh: bool) -> str:
    """Localize presentation text without changing the extracted source model."""
    text = compact(value)
    if not zh:
        return text
    translated = ZH_DISPLAY_TRANSLATIONS.get(text)
    if translated:
        return translated
    diagnostic_prefix = "Packaged files not referenced by SKILL.md or linked docs: "
    if text.startswith(diagnostic_prefix):
        return "以下打包文件未被 SKILL.md 或已链接文档引用：" + text[len(diagnostic_prefix):]
    return text


def display_resource_kind(value: Any, zh: bool) -> str:
    text = compact(value)
    if not zh:
        return text
    return {
        "reference": "参考文档",
        "script": "脚本",
        "asset": "资源",
        "module": "Skill 模块",
        "skill-module": "Skill 模块",
        "runtime-manifest": "运行时清单",
        "kit-manifest": "Kit 清单",
        "manifest": "清单",
        "case": "案例",
        "source": "源文件",
        "document": "文档",
    }.get(text, text)


def load_mermaid_bundle() -> str:
    """Load the vendored browser renderer embedded into standalone reviews."""
    if not MERMAID_BUNDLE.is_file():
        relative = MERMAID_BUNDLE.relative_to(Path(__file__).resolve().parents[1])
        raise RuntimeError(f"missing vendored Mermaid runtime: {relative}")
    return MERMAID_BUNDLE.read_text(encoding="utf-8").replace("</script", "<\\/script")


@dataclass
class SourceSpan:
    file: str
    start: int
    end: int


@dataclass
class TextItem:
    text: str
    source: SourceSpan


@dataclass
class Condition:
    text: str
    action: str
    source: SourceSpan


@dataclass
class StepDetail:
    kind: str
    text: str
    source: SourceSpan


@dataclass
class Step:
    id: str
    number: str
    title: str
    summary: str
    source: SourceSpan
    conditions: List[Condition] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    details: List[StepDetail] = field(default_factory=list)
    module_ids: List[str] = field(default_factory=list)
    pipeline_ids: List[str] = field(default_factory=list)
    assurance: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Resource:
    path: str
    kind: str
    exists: bool
    linked: bool
    sources: List[SourceSpan] = field(default_factory=list)


@dataclass
class ResourceEdge:
    source: str
    target: str
    line: int


@dataclass
class Diagnostic:
    level: str
    code: str
    message: str


@dataclass
class Heading:
    level: int
    title: str
    line: int


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def compact(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def strip_markdown(value: str) -> str:
    value = re.sub(r"`([^`]*)`", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"[*~]+", "", value)
    return compact(value)


def normalize_heading(value: str) -> str:
    value = strip_markdown(value).casefold()
    value = re.sub(r"\([^)]*\)", "", value)
    return compact(value)


def resolve_skill(target: Path) -> Tuple[Path, Path]:
    target = target.expanduser()
    if target.is_dir():
        skill_root = target.resolve()
        skill_file = skill_root / "SKILL.md"
    elif target.is_file():
        skill_file = target.resolve()
        if skill_file.name != "SKILL.md":
            raise ValueError("file input must be named SKILL.md")
        skill_root = skill_file.parent
    else:
        raise ValueError(f"target does not exist: {target}")
    if not skill_file.is_file():
        raise ValueError(f"SKILL.md not found under: {skill_root}")
    return skill_root, skill_file


def parse_frontmatter(text: str) -> Tuple[Dict[str, Any], int]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, 0
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            if yaml is None:
                raise RuntimeError("PyYAML is required: python3 -m pip install PyYAML")
            value = yaml.safe_load("\n".join(lines[1:index])) or {}
            if not isinstance(value, dict):
                raise ValueError("SKILL.md frontmatter must be a YAML mapping")
            return value, index + 1
    raise ValueError("SKILL.md frontmatter is not closed with ---")


def parse_headings(lines: Sequence[str]) -> List[Heading]:
    headings: List[Heading] = []
    for index, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line)
        if match:
            headings.append(Heading(len(match.group(1)), compact(match.group(2)), index))
    return headings


def section_bounds(
    headings: Sequence[Heading], predicate: Any, level: int = 2
) -> Optional[Tuple[int, int, Heading]]:
    for index, heading in enumerate(headings):
        if heading.level == level and predicate(normalize_heading(heading.title)):
            end = 10**9
            for later in headings[index + 1 :]:
                if later.level <= level:
                    end = later.line - 1
                    break
            return heading.line + 1, end, heading
    return None


def list_items(lines: Sequence[str], start: int, end: int, source: str) -> List[TextItem]:
    result: List[TextItem] = []
    end = min(end, len(lines))
    line_number = start
    while line_number <= end:
        match = LIST_RE.match(lines[line_number - 1])
        if match:
            parts = [match.group(1).strip()]
            source_end = line_number
            next_line = line_number + 1
            while next_line <= end:
                following = lines[next_line - 1]
                stripped = following.strip()
                if (
                    not stripped
                    or stripped.startswith(("#", "```", "|"))
                    or LIST_RE.match(following)
                ):
                    break
                parts.append(stripped)
                source_end = next_line
                next_line += 1
            result.append(
                TextItem(
                    strip_markdown(" ".join(parts)),
                    SourceSpan(source, line_number, source_end),
                )
            )
            line_number = max(line_number + 1, next_line)
            continue
        line_number += 1
    return result


def parse_trigger_group(
    lines: Sequence[str], headings: Sequence[Heading], source: str, activation: bool
) -> List[TextItem]:
    trigger_bounds = section_bounds(
        headings,
        lambda title: title == "triggers" or title in {"触发", "触发条件", "触发边界"},
    )
    if not trigger_bounds:
        return []
    start, end, _ = trigger_bounds
    candidates = [
        heading
        for heading in headings
        if start <= heading.line <= end and heading.level >= 3
    ]
    expected = (
        ("activate", "when to use", "使用时机", "触发时", "适用")
        if activation
        else ("do not activate", "do not use", "not activate", "不触发", "不适用")
    )
    for index, heading in enumerate(candidates):
        normalized = normalize_heading(heading.title)
        matches = any(token in normalized for token in expected)
        if activation and ("do not" in normalized or "not activate" in normalized):
            matches = False
        if not matches:
            continue
        group_end = end
        for later in candidates[index + 1 :]:
            if later.level <= heading.level:
                group_end = later.line - 1
                break
        return list_items(lines, heading.line + 1, group_end, source)
    return []


def split_condition(value: str) -> Optional[Tuple[str, str]]:
    cleaned = strip_markdown(value)
    match = CONDITION_RE.match(cleaned)
    if not match:
        return None
    prefix = match.group(1)
    rest = match.group(2).strip()
    parts = re.split(r"\s*[,，;；:]\s*", rest, maxsplit=1)
    condition = compact(f"{prefix} {parts[0]}")
    action = compact(parts[1]) if len(parts) > 1 else ""
    return condition, action


def summarize_step(lines: Sequence[str], start: int, end: int) -> str:
    for line_number in range(start, min(end, len(lines)) + 1):
        raw = lines[line_number - 1].strip()
        if not raw or raw.startswith("#") or raw.startswith("```"):
            continue
        match = LIST_RE.match(raw)
        value = match.group(1) if match else raw
        value = strip_markdown(value)
        if value:
            return value
    return ""


def classify_step_detail(value: str, shape: str = "paragraph") -> str:
    """Classify authored detail without inventing semantics beyond its wording."""
    normalized = strip_markdown(value).casefold()
    if shape == "table":
        return "decision"
    if re.search(
        r"\b(verify|validate|check|test|inspect|audit|re-read|confirm)\b|"
        r"(核验|验证|检查|审阅|验收|确认)",
        normalized,
    ):
        return "verification"
    if re.search(
        r"\b(do not|must not|never|avoid|only when|preserve)\b|"
        r"(不得|不要|禁止|仅当|保留)",
        normalized,
    ):
        return "guardrail"
    if shape == "ordered":
        return "criterion"
    if re.match(
        r"^(create|produce|build|define|compose|implement|report|establish|write|lead|map)\b|"
        r"^(建立|形成|产出|生成|定义|组织|实现|报告|撰写|映射)",
        normalized,
    ):
        return "output"
    return "instruction"


def parse_step_details(
    lines: Sequence[str], start: int, end: int, source: str
) -> List[StepDetail]:
    """Preserve the actionable body of a step as line-bound review evidence."""
    result: List[StepDetail] = []
    line_number = start
    final_line = min(end, len(lines))
    in_code_fence = False
    while line_number <= final_line:
        raw = lines[line_number - 1]
        stripped = raw.strip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            line_number += 1
            continue
        if not stripped or stripped.startswith("#"):
            line_number += 1
            continue
        if in_code_fence:
            result.append(
                StepDetail("command", stripped, SourceSpan(source, line_number, line_number))
            )
            line_number += 1
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            if re.fullmatch(r"\|?[\s:|\-]+\|?", stripped):
                line_number += 1
                continue
            cells = [strip_markdown(cell) for cell in stripped.strip("|").split("|")]
            if line_number < final_line and re.fullmatch(
                r"\|?[\s:|\-]+\|?", lines[line_number].strip()
            ):
                line_number += 1
                continue
            text = " → ".join(cell for cell in cells if cell)
            if text:
                result.append(
                    StepDetail("decision", text, SourceSpan(source, line_number, line_number))
                )
            line_number += 1
            continue
        ordered_match = ORDERED_RE.match(raw)
        list_match = LIST_RE.match(raw)
        if ordered_match or list_match:
            match = ordered_match or list_match
            assert match is not None
            parts = [match.group(1).strip()]
            source_end = line_number
            next_line = line_number + 1
            while next_line <= final_line:
                following = lines[next_line - 1]
                following_stripped = following.strip()
                if (
                    not following_stripped
                    or following_stripped.startswith(("#", "```", "|"))
                    or LIST_RE.match(following)
                ):
                    break
                parts.append(following_stripped)
                source_end = next_line
                next_line += 1
            text = strip_markdown(" ".join(parts))
            if text:
                shape = "ordered" if ordered_match else "list"
                result.append(
                    StepDetail(
                        classify_step_detail(text, shape),
                        text,
                        SourceSpan(source, line_number, source_end),
                    )
                )
            line_number = max(line_number + 1, next_line)
            continue
        parts = [stripped]
        source_end = line_number
        next_line = line_number + 1
        while next_line <= final_line:
            following = lines[next_line - 1]
            following_stripped = following.strip()
            if (
                not following_stripped
                or following_stripped.startswith(("#", "```", "|"))
                or LIST_RE.match(following)
            ):
                break
            parts.append(following_stripped)
            source_end = next_line
            next_line += 1
        text = strip_markdown(" ".join(parts))
        if text:
            result.append(
                StepDetail(
                    classify_step_detail(text),
                    text,
                    SourceSpan(source, line_number, source_end),
                )
            )
        line_number = max(line_number + 1, next_line)
    return result


def safe_id(prefix: str, index: int) -> str:
    return f"{prefix}_{index:03d}"


def extract_paths(line: str) -> Set[str]:
    found: Set[str] = set()
    normalized_line = re.sub(r"\$[A-Za-z_][A-Za-z0-9_]*/", "", line)
    for match in INLINE_PATH_RE.finditer(normalized_line):
        found.add(match.group(1).rstrip(".,:;)]}'\""))
    for match in MARKDOWN_LINK_RE.finditer(line):
        candidate = match.group(1).split("#", 1)[0].strip()
        suffix = Path(candidate).suffix.lower()
        if (
            candidate.startswith((RESOURCE_PREFIXES + ("./", "../")))
            or candidate in ROOT_RESOURCES
            or suffix in {".md", ".yaml", ".yml", ".json", ".py", ".sh"}
        ) and not candidate.startswith(("http://", "https://", "data:")):
            found.add(candidate)
    return found


def normalize_resource_path(path: str, declaring_file: str, skill_root: Path) -> Optional[str]:
    path = path.split("#", 1)[0].strip().replace("\\", "/")
    if not path or path.startswith(("http://", "https://", "/", "data:")):
        return None
    declaring_parent = Path(declaring_file).parent
    if path in ROOT_RESOURCES:
        candidate = (skill_root / path).resolve()
    elif path.startswith(("./", "../")) or "/" not in path:
        candidate = (skill_root / declaring_parent / path).resolve()
    else:
        candidate = (skill_root / path).resolve()
    try:
        return candidate.relative_to(skill_root).as_posix()
    except ValueError:
        return None


def extract_conditions(
    lines: Sequence[str], start: int, end: int, source: str
) -> List[Condition]:
    result: List[Condition] = []
    in_code_fence = False
    line_number = start
    final_line = min(end, len(lines))
    while line_number <= final_line:
        raw = lines[line_number - 1]
        if raw.strip().startswith("```"):
            in_code_fence = not in_code_fence
            line_number += 1
            continue
        if in_code_fence or raw.lstrip().startswith("#"):
            line_number += 1
            continue
        match = LIST_RE.match(raw)
        candidate = match.group(1) if match else raw.strip()
        if not match and re.match(r"^(if|when|unless|otherwise|else)\b", candidate):
            line_number += 1
            continue
        source_end = line_number
        continuation: List[str] = [candidate]
        next_line = line_number + 1
        while next_line <= final_line:
            next_raw = lines[next_line - 1]
            next_stripped = next_raw.strip()
            if (
                not next_stripped
                or next_stripped.startswith(("#", "```"))
                or LIST_RE.match(next_raw)
            ):
                break
            continuation.append(next_stripped)
            source_end = next_line
            next_line += 1
        candidate = " ".join(continuation)
        parsed = split_condition(candidate)
        if parsed:
            result.append(
                Condition(parsed[0], parsed[1], SourceSpan(source, line_number, source_end))
            )
        line_number = max(line_number + 1, next_line)
    return result


def parse_steps(
    lines: Sequence[str], headings: Sequence[Heading], source: str, skill_root: Path
) -> List[Step]:
    workflow = section_bounds(
        headings,
        lambda title: "workflow" in title or title in {"流程", "运行流程", "执行流程"},
    )
    if not workflow:
        return []
    start, end, workflow_heading = workflow
    end = min(end, len(lines))
    step_headings: List[Heading] = []
    for heading in headings:
        if start <= heading.line <= end and heading.level > workflow_heading.level:
            if STEP_RE.match(normalize_heading(heading.title)):
                step_headings.append(heading)
    steps: List[Step] = []
    if step_headings:
        for index, heading in enumerate(step_headings):
            match = STEP_RE.match(strip_markdown(heading.title))
            assert match is not None
            number = compact(match.group(1)) or str(index + 1)
            title = compact(match.group(2)) or strip_markdown(heading.title)
            body_start = heading.line + 1
            body_end = end
            if index + 1 < len(step_headings):
                body_end = step_headings[index + 1].line - 1
            resources: Set[str] = set()
            for line_number in range(body_start, body_end + 1):
                for raw_path in extract_paths(lines[line_number - 1]):
                    normalized = normalize_resource_path(raw_path, source, skill_root)
                    if normalized:
                        resources.add(normalized)
            steps.append(
                Step(
                    id=safe_id("step", index + 1),
                    number=number,
                    title=title,
                    summary=summarize_step(lines, body_start, body_end),
                    source=SourceSpan(source, heading.line, body_end),
                    conditions=extract_conditions(lines, body_start, body_end, source),
                    resources=sorted(resources),
                    details=parse_step_details(lines, body_start, body_end, source),
                )
            )
        return steps

    ordered: List[Tuple[int, str]] = []
    for line_number in range(start, end + 1):
        match = ORDERED_RE.match(lines[line_number - 1])
        if match:
            ordered.append((line_number, strip_markdown(match.group(1))))
    for index, (line_number, title) in enumerate(ordered):
        next_line = ordered[index + 1][0] - 1 if index + 1 < len(ordered) else line_number
        resources: Set[str] = set()
        for raw_path in extract_paths(lines[line_number - 1]):
            normalized = normalize_resource_path(raw_path, source, skill_root)
            if normalized:
                resources.add(normalized)
        steps.append(
            Step(
                id=safe_id("step", index + 1),
                number=str(index + 1),
                title=title,
                summary="",
                source=SourceSpan(source, line_number, next_line),
                conditions=extract_conditions(lines, line_number, next_line, source),
                resources=sorted(resources),
                details=parse_step_details(lines, line_number, next_line, source),
            )
        )
    return steps


def resource_kind(path: str) -> str:
    if path == "skill.yaml":
        return "runtime-manifest"
    if path == "kit.yaml":
        return "kit-manifest"
    if path.startswith("references/"):
        return "reference"
    if path.startswith("scripts/"):
        return "script"
    if path.startswith("assets/"):
        return "asset"
    if path.startswith("skills/"):
        return "module"
    if path.startswith("cases/"):
        return "case"
    return "source"


def discover_resources(
    skill_root: Path, root_file: Path, max_depth: int
) -> Tuple[List[Resource], List[ResourceEdge]]:
    resource_map: Dict[str, Resource] = {}
    edges: List[ResourceEdge] = []
    visited: Set[str] = set()
    root_relative = root_file.relative_to(skill_root).as_posix()
    queue: List[Tuple[str, int]] = [(root_relative, 0)]
    while queue:
        declaring_file, depth = queue.pop(0)
        if declaring_file in visited:
            continue
        visited.add(declaring_file)
        declaring_path = skill_root / declaring_file
        if not declaring_path.is_file() or declaring_path.suffix.lower() != ".md":
            continue
        for line_number, line in enumerate(read_text(declaring_path).splitlines(), start=1):
            for raw_path in extract_paths(line):
                path = normalize_resource_path(raw_path, declaring_file, skill_root)
                if not path or path == declaring_file:
                    continue
                target_exists = (skill_root / path).exists()
                active = is_active_resource_mention(line, path, target_exists)
                if not active:
                    continue
                span = SourceSpan(declaring_file, line_number, line_number)
                if path == root_relative:
                    if not any(
                        edge.source == declaring_file
                        and edge.target == path
                        and edge.line == line_number
                        for edge in edges
                    ):
                        edges.append(ResourceEdge(declaring_file, path, line_number))
                    continue
                resource = resource_map.setdefault(
                    path,
                    Resource(path, resource_kind(path), target_exists, True, []),
                )
                if not any(asdict(existing) == asdict(span) for existing in resource.sources):
                    resource.sources.append(span)
                if not any(
                    edge.source == declaring_file and edge.target == path and edge.line == line_number
                    for edge in edges
                ):
                    edges.append(ResourceEdge(declaring_file, path, line_number))
                if (
                    resource.exists
                    and path.endswith(".md")
                    and path.startswith(("references/", "skills/"))
                    and depth < max_depth
                    and path not in visited
                ):
                    queue.append((path, depth + 1))

    for prefix in ("references", "scripts", "assets", "skills"):
        base = skill_root / prefix
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.name in {".DS_Store"} or "__pycache__" in path.parts:
                continue
            relative = path.relative_to(skill_root).as_posix()
            resource_map.setdefault(
                relative,
                Resource(relative, resource_kind(relative), True, False, []),
            )
    for root_resource in sorted(ROOT_RESOURCES - {"SKILL.md"}):
        path = skill_root / root_resource
        if path.exists():
            resource_map.setdefault(
                root_resource,
                Resource(root_resource, resource_kind(root_resource), True, False, []),
            )
    return sorted(resource_map.values(), key=lambda item: item.path), sorted(
        edges, key=lambda item: (item.source, item.line, item.target)
    )


def is_active_resource_mention(line: str, path: str, exists: bool) -> bool:
    """Separate runtime inputs from filenames shown as generated products."""
    lowered = line.casefold()
    if path.startswith(RESOURCE_PREFIXES) and exists:
        return True
    if MARKDOWN_LINK_RE.search(line):
        return True
    strong_markers = (
        "read ",
        "see ",
        "run ",
        "execute ",
        "invoke ",
        "load ",
        "verify ",
        "requires ",
        "required ",
        "resolve ",
        "through ",
        "python3 ",
        "读取",
        "参见",
        "运行",
        "执行",
        "调用",
        "加载",
        "校验",
        "必须存在",
    )
    return any(marker in lowered for marker in strong_markers)


def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.is_file() or yaml is None:
        return {}
    value = yaml.safe_load(read_text(path)) or {}
    return value if isinstance(value, dict) else {}


def parse_dependencies(frontmatter: Dict[str, Any]) -> List[str]:
    metadata = frontmatter.get("metadata")
    values: Any = metadata.get("dependencies", []) if isinstance(metadata, dict) else []
    if isinstance(values, str):
        values = [values]
    return [compact(item) for item in values if compact(item)] if isinstance(values, list) else []


def parse_named_list_section(
    lines: Sequence[str], headings: Sequence[Heading], source: str, names: Set[str]
) -> List[TextItem]:
    bounds = section_bounds(headings, lambda title: title in names)
    if not bounds:
        return []
    start, end, _ = bounds
    return list_items(lines, start, end, source)


def parse_kit(skill_root: Path) -> Dict[str, Any]:
    data = load_yaml(skill_root / "kit.yaml")
    if not data:
        return {}
    raw_modules = data.get("modules", [])
    raw_pipelines = data.get("pipelines", [])
    if isinstance(raw_pipelines, dict):
        pipelines = [
            {"id": compact(name), "steps": sequence if isinstance(sequence, list) else []}
            for name, sequence in raw_pipelines.items()
        ]
    elif isinstance(raw_pipelines, list):
        pipelines = raw_pipelines
    else:
        pipelines = []
    modules: List[Dict[str, Any]] = []
    for raw_module in raw_modules if isinstance(raw_modules, list) else []:
        if not isinstance(raw_module, dict):
            continue
        module = dict(raw_module)
        module_path = compact(module.get("path"))
        module_file = skill_root / module_path / "SKILL.md" if module_path else None
        module["source"] = (
            module_file.relative_to(skill_root).as_posix() if module_file else ""
        )
        module["exists"] = bool(module_file and module_file.is_file())
        module["description"] = ""
        module["workflow_steps"] = []
        module["quality_gates"] = []
        if module_file and module_file.is_file():
            module_text = read_text(module_file)
            module_lines = module_text.splitlines()
            module_frontmatter, _ = parse_frontmatter(module_text)
            module_headings = parse_headings(module_lines)
            module_source = module_file.relative_to(skill_root).as_posix()
            module["description"] = compact(module_frontmatter.get("description"))
            module["workflow_steps"] = [
                asdict(step)
                for step in parse_steps(
                    module_lines,
                    module_headings,
                    module_source,
                    skill_root,
                )
            ]
            module["quality_gates"] = [
                asdict(item)
                for item in parse_named_list_section(
                    module_lines,
                    module_headings,
                    module_source,
                    {"quality gate", "quality gates", "质量门", "质量门禁", "验收标准"},
                )
            ]
        modules.append(module)
    return {"modules": modules, "pipelines": pipelines}


def associate_steps_with_kit(steps: List[Step], kit: Dict[str, Any]) -> None:
    modules = [item for item in kit.get("modules", []) if isinstance(item, dict)]
    pipelines = [item for item in kit.get("pipelines", []) if isinstance(item, dict)]
    module_by_id = {compact(item.get("id")): item for item in modules}
    for step in steps:
        authored = " ".join([step.title, step.summary] + [item.text for item in step.details])
        normalized = authored.casefold()
        for module_id, module in module_by_id.items():
            if not module_id:
                continue
            suffix = module_id.split("-")[-1]
            skill_id = compact(module.get("skill")).casefold()
            module_path = compact(module.get("path")).casefold()
            explicit_aliases = {
                module_id.casefold(),
                skill_id,
                module_path,
                f"{suffix} module",
                f"{suffix} 模块",
            }
            if any(alias and alias in normalized for alias in explicit_aliases):
                step.module_ids.append(module_id)
                continue
            if any(
                resource == module_path or resource.startswith(module_path + "/")
                for resource in step.resources
                if module_path
            ):
                step.module_ids.append(module_id)
        for pipeline in pipelines:
            pipeline_id = compact(pipeline.get("id") or pipeline.get("name"))
            if pipeline_id and re.search(
                rf"(?<![a-z0-9-]){re.escape(pipeline_id.casefold())}(?![a-z0-9-])",
                normalized,
            ):
                step.pipeline_ids.append(pipeline_id)
        linked_modules = [module_by_id[item] for item in step.module_ids if item in module_by_id]
        linked_gates = sum(len(item.get("quality_gates", [])) for item in linked_modules)
        deterministic_resources = [
            item
            for item in step.resources
            if item.startswith("scripts/") and "validate" not in Path(item).name.casefold()
        ]
        verification_items = [item for item in step.details if item.kind == "verification"]
        output_items = [item for item in step.details if item.kind == "output"]
        step.assurance = {
            "source_bound": True,
            "authored_detail_count": len(step.details),
            "support_level": (
                "module_pipeline_or_resource"
                if sum(bool(item) for item in (step.module_ids, step.pipeline_ids, step.resources)) > 1
                else "module"
                if step.module_ids
                else "pipeline"
                if step.pipeline_ids
                else "resource"
                if step.resources
                else "declaration_only"
            ),
            "execution_mode": "deterministic_script" if deterministic_resources else "agent_instruction",
            "deterministic_resources": deterministic_resources,
            "declared_output_count": len(output_items),
            "declared_verification_count": len(verification_items) + linked_gates,
            "effect_evidence": "not_observed",
        }


def build_trust_model(
    steps: Sequence[Step], kit: Dict[str, Any], resources: Sequence[Resource]
) -> Dict[str, Any]:
    runtime_scripts = [
        item.path
        for item in resources
        if item.exists
        and item.path.startswith("scripts/")
        and "validate" not in Path(item.path).name.casefold()
        and "test" not in Path(item.path).name.casefold()
    ]
    validation_assets = [
        item.path
        for item in resources
        if item.exists
        and (
            "validate" in Path(item.path).name.casefold()
            or "test" in Path(item.path).name.casefold()
        )
    ]
    observed_artifacts = [
        item.path
        for item in resources
        if item.exists and item.path.startswith(("cases/", "evidence/", "artifacts/"))
    ]
    modules = [item for item in kit.get("modules", []) if isinstance(item, dict)]
    quality_gates = sum(len(item.get("quality_gates", [])) for item in modules)
    supported_steps = sum(
        1 for step in steps if step.module_ids or step.pipeline_ids or step.resources
    )
    steps_with_checks = sum(
        1 for step in steps if step.assurance.get("declared_verification_count", 0) > 0
    )
    effect_evidence = "observed_unbound" if observed_artifacts else "not_observed"
    return {
        "scope": "internal_runtime",
        "routing_scope": "external_activation_boundary",
        "traceability": {
            "source_bound_steps": len(steps),
            "total_steps": len(steps),
        },
        "support": {
            "steps_with_modules_or_resources": supported_steps,
            "module_workflows": sum(bool(item.get("workflow_steps")) for item in modules),
            "module_quality_gates": quality_gates,
        },
        "implementation": {
            "mode": "deterministic" if runtime_scripts else "agent_guided",
            "runtime_scripts": runtime_scripts,
        },
        "verification": {
            "steps_with_declared_checks": steps_with_checks,
            "validation_assets": validation_assets,
            "observed_artifacts": observed_artifacts,
            "effect_evidence": effect_evidence,
        },
        "verdict": "observed_unbound" if observed_artifacts else "declared_not_observed",
    }


def build_model(skill_root: Path, skill_file: Path, max_depth: int) -> Dict[str, Any]:
    text = read_text(skill_file)
    lines = text.splitlines()
    frontmatter, _ = parse_frontmatter(text)
    headings = parse_headings(lines)
    source = skill_file.relative_to(skill_root).as_posix()
    activate = parse_trigger_group(lines, headings, source, True)
    exclude = parse_trigger_group(lines, headings, source, False)
    steps = parse_steps(lines, headings, source, skill_root)
    resources, resource_edges = discover_resources(skill_root, skill_file, max_depth)
    diagnostics: List[Diagnostic] = []
    kit = parse_kit(skill_root)
    associate_steps_with_kit(steps, kit)
    trust = build_trust_model(steps, kit, resources)
    if not frontmatter.get("name"):
        diagnostics.append(Diagnostic("error", "missing_name", "Frontmatter name is missing."))
    if not activate:
        diagnostics.append(
            Diagnostic("error", "missing_activation", "No activation examples were extracted.")
        )
    if not exclude:
        diagnostics.append(
            Diagnostic("warning", "missing_non_trigger", "No non-trigger boundary was extracted.")
        )
    if not steps:
        diagnostics.append(
            Diagnostic("error", "missing_workflow", "No ordered workflow steps were extracted.")
        )
    missing = [resource.path for resource in resources if resource.linked and not resource.exists]
    for path in missing:
        diagnostics.append(
            Diagnostic("error", "missing_resource", f"Declared local resource does not exist: {path}")
        )
    unlinked = [
        resource.path
        for resource in resources
        if not resource.linked
        and resource.path not in {
            "CHANGELOG.md",
            "README.md",
            "skill-card.md",
            "skill-card.yaml",
            "pricing-card.yaml",
            "cases/cases.json",
            "scripts/validate_skill.py",
        }
    ]
    if unlinked:
        diagnostics.append(
            Diagnostic(
                "info",
                "unlinked_packaged_files",
                f"Packaged files not referenced by SKILL.md or linked docs: {', '.join(unlinked)}",
            )
        )
    manifest = load_yaml(skill_root / "skill.yaml")
    profile = manifest.get("context", {}).get("profile", {}) if isinstance(manifest.get("context"), dict) else {}
    runtime_context = {
        "runtime": compact(manifest.get("runtime")),
        "profile_schema": compact(profile.get("schema")) if isinstance(profile, dict) else "",
        "reads": profile.get("read", []) if isinstance(profile, dict) else [],
    }
    return {
        "schema": SCHEMA,
        "skill": {
            "name": compact(frontmatter.get("name")) or skill_root.name,
            "version": compact((frontmatter.get("metadata") or {}).get("version"))
            if isinstance(frontmatter.get("metadata"), dict)
            else "",
            "description": compact(frontmatter.get("description")),
            "source": source,
        },
        "routing": {
            "activate": [asdict(item) for item in activate],
            "do_not_activate": [asdict(item) for item in exclude],
        },
        "runtime_context": runtime_context,
        "workflow": {"steps": [asdict(step) for step in steps]},
        "trust": trust,
        "dependencies": parse_dependencies(frontmatter),
        "kit": kit,
        "resources": [asdict(resource) for resource in resources],
        "resource_edges": [asdict(edge) for edge in resource_edges],
        "diagnostics": [asdict(item) for item in diagnostics],
        "coverage": {
            "activation_examples": len(activate),
            "non_trigger_examples": len(exclude),
            "workflow_steps": len(steps),
            "conditional_rules": sum(len(step.conditions) for step in steps),
            "linked_resources": sum(1 for item in resources if item.linked),
            "missing_resources": len(missing),
            "reference_depth": max_depth,
            "kit_modules": len(kit.get("modules", [])),
            "kit_pipelines": len(kit.get("pipelines", [])),
            "steps_with_support": trust["support"]["steps_with_modules_or_resources"],
            "steps_with_checks": trust["verification"]["steps_with_declared_checks"],
            "observed_artifacts": len(trust["verification"]["observed_artifacts"]),
        },
    }


def mermaid_text(value: Any, limit: int = 72) -> str:
    value = compact(value)
    if len(value) > limit:
        value = value[: limit - 1].rstrip() + "…"
    return (
        value.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("[", "(")
        .replace("]", ")")
        .replace("{", "(")
        .replace("}", ")")
    )


def source_label(source: Dict[str, Any]) -> str:
    start = source.get("start")
    end = source.get("end")
    suffix = str(start) if start == end else f"{start}-{end}"
    return f"{source.get('file')}:{suffix}"


def render_runtime_mermaid(model: Dict[str, Any], direction: str, zh: bool) -> str:
    yes = "是" if zh else "yes"
    no = "否" if zh else "no"
    deliver = "交付并报告证据" if zh else "Deliver output and report evidence"
    resume = "继续" if zh else "Continue"
    internal_start = "Skill 内部执行开始" if zh else "Skill internal execution starts"
    lines = [f"flowchart {direction}", f'  internal(["{internal_start}"])']
    steps = model["workflow"]["steps"]
    previous = "internal"
    for step_index, step in enumerate(steps, start=1):
        node = step["id"]
        label = f"{step['number']}. {display_text(step['title'], zh)}"
        lines.append(f'  {node}["{mermaid_text(label)}"]')
        lines.append(f"  {previous} --> {node}")
        previous = node
        for condition_index, condition in enumerate(step.get("conditions", []), start=1):
            decision = f"decision_{step_index:03d}_{condition_index:02d}"
            action = f"action_{step_index:03d}_{condition_index:02d}"
            join = f"join_{step_index:03d}_{condition_index:02d}"
            lines.append(f'  {decision}{{"{mermaid_text(display_text(condition["text"], zh))}"}}')
            lines.append(f'  {join}(["{mermaid_text(resume)}"])')
            lines.append(f"  {previous} --> {decision}")
            if condition.get("action"):
                lines.append(f'  {action}["{mermaid_text(display_text(condition["action"], zh))}"]')
                lines.append(f'  {decision} -- "{yes}" --> {action}')
                lines.append(f"  {action} --> {join}")
            else:
                lines.append(f'  {decision} -- "{yes}" --> {join}')
            lines.append(f'  {decision} -- "{no}" --> {join}')
            previous = join
    lines.append(f'  deliver(["{mermaid_text(deliver)}"])')
    lines.append(f"  {previous} --> deliver")
    lines.extend(
        [
            "  classDef entry fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e;",
            "  classDef decision fill:#fef3c7,stroke:#d97706,color:#78350f;",
            "  classDef process fill:#ecfdf5,stroke:#059669,color:#064e3b;",
            "  classDef terminal fill:#f3e8ff,stroke:#9333ea,color:#581c87;",
            "  classDef inspectable fill:#ecfdf5,stroke:#176b57,color:#064e3b,stroke-width:2px;",
            "  class internal entry;",
            "  class deliver terminal;",
        ]
    )
    if steps:
        lines.append("  class " + ",".join(step["id"] for step in steps) + " inspectable;")
    decision_ids = [
        f"decision_{step_index:03d}_{condition_index:02d}"
        for step_index, step in enumerate(steps, start=1)
        for condition_index, _ in enumerate(step.get("conditions", []), start=1)
    ]
    if decision_ids:
        lines.append("  class " + ",".join(decision_ids) + " decision;")
    return "\n".join(lines)


def render_resource_mermaid(model: Dict[str, Any], zh: bool) -> str:
    root_label = "主控制器 SKILL.md" if zh else "Controller SKILL.md"
    lines = ["flowchart LR", f'  controller["{root_label}"]']
    node_ids: Dict[str, str] = {"SKILL.md": "controller"}
    for index, resource in enumerate(model["resources"], start=1):
        node_id = safe_id("resource", index)
        node_ids[resource["path"]] = node_id
        status = "" if resource["exists"] else (" · 缺失" if zh else " · missing")
        label = f"{resource['path']}\n{display_resource_kind(resource['kind'], zh)}{status}"
        lines.append(f'  {node_id}["{mermaid_text(label, 96)}"]')
    declared_edges: Set[Tuple[str, str]] = set()
    for edge in model["resource_edges"]:
        source = node_ids.get(edge["source"], "controller")
        target = node_ids.get(edge["target"])
        if target and (source, target) not in declared_edges:
            lines.append(f"  {source} -.-> {target}")
            declared_edges.add((source, target))
    for dependency_index, dependency in enumerate(model.get("dependencies", []), start=1):
        node_id = safe_id("dependency", dependency_index)
        lines.append(f'  {node_id}[["{mermaid_text(dependency)}"]]')
        lines.append(f"  controller --> {node_id}")
    lines.extend(
        [
            "  classDef source fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e;",
            "  classDef linked fill:#ecfdf5,stroke:#059669,color:#064e3b;",
            "  classDef unlinked fill:#f8fafc,stroke:#94a3b8,color:#334155,stroke-dasharray: 4 3;",
            "  classDef missing fill:#fee2e2,stroke:#dc2626,color:#7f1d1d;",
            "  class controller source;",
        ]
    )
    linked_ids = [
        node_ids[item["path"]]
        for item in model["resources"]
        if item["linked"] and item["exists"]
    ]
    unlinked_ids = [
        node_ids[item["path"]]
        for item in model["resources"]
        if not item["linked"] and item["exists"]
    ]
    missing_ids = [
        node_ids[item["path"]] for item in model["resources"] if not item["exists"]
    ]
    if linked_ids:
        lines.append("  class " + ",".join(linked_ids) + " linked;")
    if unlinked_ids:
        lines.append("  class " + ",".join(unlinked_ids) + " unlinked;")
    if missing_ids:
        lines.append("  class " + ",".join(missing_ids) + " missing;")
    return "\n".join(lines)


def render_kit_mermaid(model: Dict[str, Any], zh: bool) -> str:
    kit = model.get("kit") or {}
    modules = kit.get("modules") or []
    pipelines = kit.get("pipelines") or []
    if not modules and not pipelines:
        return ""
    title = "Skill Kit 组合" if zh else "Skill Kit composition"
    lines = ["flowchart LR", f'  kit["{title}"]']
    module_ids: Dict[str, str] = {}
    for index, module in enumerate(modules, start=1):
        if isinstance(module, dict):
            name = compact(module.get("id") or module.get("name") or module.get("path"))
        else:
            name = compact(module)
        node_id = safe_id("module", index)
        module_ids[name] = node_id
        lines.append(f'  {node_id}["{mermaid_text(name or node_id)}"]')
    for pipeline_index, pipeline in enumerate(pipelines, start=1):
        if not isinstance(pipeline, dict):
            continue
        pipeline_name = compact(pipeline.get("id") or pipeline.get("name") or f"pipeline-{pipeline_index}")
        steps = pipeline.get("steps") or pipeline.get("modules") or []
        previous = "kit"
        for raw_step in steps if isinstance(steps, list) else []:
            name = compact(raw_step.get("module") or raw_step.get("id")) if isinstance(raw_step, dict) else compact(raw_step)
            target = module_ids.get(name)
            if target:
                lines.append(f'  {previous} -- "{mermaid_text(pipeline_name)}" --> {target}')
                previous = target
    return "\n".join(lines)


def choose_language(model: Dict[str, Any], requested: str) -> bool:
    if requested == "zh":
        return True
    if requested == "en":
        return False
    sample = model["skill"].get("description", "") + " " + " ".join(
        item["text"] for item in model["routing"]["activate"]
    )
    return bool(CJK_RE.search(sample))


def markdown_table(rows: Iterable[Sequence[str]]) -> str:
    materialized = list(rows)
    if not materialized:
        return ""
    width = len(materialized[0])
    escaped = [
        [compact(cell).replace("|", "\\|").replace("\n", "<br>") for cell in row]
        for row in materialized
    ]
    return "\n".join(
        ["| " + " | ".join(escaped[0]) + " |", "| " + " | ".join(["---"] * width) + " |"]
        + ["| " + " | ".join(row) + " |" for row in escaped[1:]]
    )


def render_report(model: Dict[str, Any], direction: str, language: str) -> str:
    zh = choose_language(model, language)
    coverage = model["coverage"]
    title = "Skill 信任审阅" if zh else "Skill Trust Review"
    summary_title = "信任覆盖" if zh else "Trust Coverage"
    runtime_title = "内部运行流程" if zh else "Internal Runtime Flow"
    resource_title = "资源与依赖关系" if zh else "Resources and Dependencies"
    evidence_title = "可追溯逻辑" if zh else "Traceable Logic"
    diagnostic_title = "诊断" if zh else "Diagnostics"
    lines = [
        f"# {model['skill']['name']} · {title}",
        "",
        (
            f"> 来源：`{model['skill']['source']}` · 版本：`{model['skill']['version'] or 'unknown'}` · "
            f"模型：`{model['schema']}`"
            if zh
            else f"> Source: `{model['skill']['source']}` · Version: `{model['skill']['version'] or 'unknown'}` · Model: `{model['schema']}`"
        ),
        "",
        f"## {summary_title}",
        "",
        (
            f"- 激活示例：{coverage['activation_examples']}；非触发示例：{coverage['non_trigger_examples']}。\n"
            f"- 运行步骤：{coverage['workflow_steps']}；显式条件规则：{coverage['conditional_rules']}。\n"
            f"- 已链接资源：{coverage['linked_resources']}；缺失资源：{coverage['missing_resources']}；引用展开深度：{coverage['reference_depth']}。\n"
            f"- Kit 模块：{coverage['kit_modules']}；命名管线：{coverage['kit_pipelines']}。\n"
            f"- 有能力依据的步骤：{coverage.get('steps_with_support', 0)}；有验收规则的步骤：{coverage.get('steps_with_checks', 0)}；真实案例产物：{coverage.get('observed_artifacts', 0)}。"
            if zh
            else f"- Activation examples: {coverage['activation_examples']}; non-trigger examples: {coverage['non_trigger_examples']}.\n"
            f"- Runtime steps: {coverage['workflow_steps']}; explicit conditional rules: {coverage['conditional_rules']}.\n"
            f"- Linked resources: {coverage['linked_resources']}; missing resources: {coverage['missing_resources']}; reference depth: {coverage['reference_depth']}.\n"
            f"- Kit modules: {coverage['kit_modules']}; named pipelines: {coverage['kit_pipelines']}.\n"
            f"- Steps with support: {coverage.get('steps_with_support', 0)}; steps with checks: {coverage.get('steps_with_checks', 0)}; observed artifacts: {coverage.get('observed_artifacts', 0)}."
        ),
        "",
        f"## {runtime_title}",
        "",
        "```mermaid",
        render_runtime_mermaid(model, direction, zh),
        "```",
        "",
        f"## {resource_title}",
        "",
        "```mermaid",
        render_resource_mermaid(model, zh),
        "```",
    ]
    kit_mermaid = render_kit_mermaid(model, zh)
    if kit_mermaid:
        lines.extend(
            [
                "",
                "## " + ("Kit 管线" if zh else "Kit Pipelines"),
                "",
                "```mermaid",
                kit_mermaid,
                "```",
            ]
        )
    step_rows: List[Sequence[str]] = [
        ("步骤", "摘要", "来源") if zh else ("Step", "Summary", "Source")
    ]
    for step in model["workflow"]["steps"]:
        step_rows.append(
            (
                f"{step['number']}. {display_text(step['title'], zh)}",
                display_text(step.get("summary") or "—", zh),
                source_label(step["source"]),
            )
        )
    lines.extend(["", f"## {evidence_title}", "", markdown_table(step_rows)])
    condition_rows: List[Sequence[str]] = [
        ("条件", "动作", "来源") if zh else ("Condition", "Action", "Source")
    ]
    for step in model["workflow"]["steps"]:
        for condition in step.get("conditions", []):
            condition_rows.append(
                (
                    display_text(condition["text"], zh),
                    display_text(condition.get("action") or ("继续" if zh else "continue"), zh),
                    source_label(condition["source"]),
                )
            )
    if len(condition_rows) > 1:
        lines.extend(
            ["", "### " + ("条件分支" if zh else "Conditional Branches"), "", markdown_table(condition_rows)]
        )
    lines.extend(["", "### " + ("外部适用边界" if zh else "External Activation Boundary"), ""])
    lines.append(
        "> 这部分属于宿主路由，不进入上方 Skill 内部运行图。"
        if zh
        else "> This belongs to host routing and is excluded from the internal runtime graph above."
    )
    for item in model["routing"]["activate"]:
        lines.append(f"- ✅ {display_text(item['text'], zh)} (`{source_label(item['source'])}`)")
    for item in model["routing"]["do_not_activate"]:
        lines.append(f"- ⛔ {display_text(item['text'], zh)} (`{source_label(item['source'])}`)")
    lines.extend(["", f"## {diagnostic_title}", ""])
    if model["diagnostics"]:
        for item in model["diagnostics"]:
            lines.append(f"- `{item['level']}` · `{item['code']}` · {display_text(item['message'], zh)}")
    else:
        lines.append("- " + ("未发现结构性问题。" if zh else "No structural diagnostics."))
    lines.extend(
        [
            "",
            (
                "> 说明：报告区分源码声明、能力依据、验收规则和真实效果。静态完整度不能替代运行案例与结果回读。"
                if zh
                else "> Note: the report separates source declarations, capability support, acceptance rules, and real effect. Static completeness does not replace runtime cases and result readback."
            ),
            "",
        ]
    )
    return "\n".join(lines)


HTML_CSS = r"""
:root {
  color-scheme: light;
  --paper: #f4efe5;
  --paper-deep: #e9dfcf;
  --surface: rgba(255, 253, 248, 0.88);
  --surface-solid: #fffdf8;
  --ink: #14231e;
  --muted: #66716a;
  --line: rgba(20, 35, 30, 0.16);
  --line-strong: rgba(20, 35, 30, 0.34);
  --accent: #d64e31;
  --accent-soft: #f4d8cb;
  --teal: #0b6f67;
  --teal-soft: #cce5de;
  --gold: #a66b12;
  --gold-soft: #f1dfb8;
  --danger: #a83232;
  --danger-soft: #f4d2ce;
  --diagram-canvas: #fbfaf7;
  --diagram-grid: rgba(20, 35, 30, 0.07);
  --studio-chrome: #17231f;
  --studio-ink: #fff8eb;
  --shadow: 0 18px 60px rgba(43, 35, 25, 0.11);
  --display: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif;
  --body: "Avenir Next", "Gill Sans", "Trebuchet MS", sans-serif;
  --mono: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background:
    linear-gradient(90deg, transparent 23px, var(--line) 24px, transparent 25px),
    linear-gradient(var(--paper), var(--paper));
  background-size: 100% 100%, 100% 100%;
  color: var(--ink);
  font-family: var(--body);
  line-height: 1.62;
}
a { color: inherit; }
button, input { font: inherit; }
button {
  border: 1px solid var(--line-strong);
  border-radius: 999px;
  background: var(--surface-solid);
  color: var(--ink);
  min-height: 40px;
  padding: 0 15px;
  cursor: pointer;
  transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
}
button:hover { transform: translateY(-1px); border-color: var(--accent); }
button:focus-visible, a:focus-visible, summary:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--accent) 42%, transparent);
  outline-offset: 3px;
}
code, pre { font-family: var(--mono); }
code { font-size: 0.88em; }

.hero {
  position: relative;
  overflow: hidden;
  background: #14231e;
  color: #fff8eb;
  border-bottom: 6px solid var(--accent);
}
.hero::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(115deg, transparent 62%, rgba(255,255,255,.06) 62.2%, transparent 63%),
    repeating-linear-gradient(90deg, transparent 0 79px, rgba(255,255,255,.045) 80px);
  pointer-events: none;
}
.hero-inner {
  position: relative;
  width: min(1320px, calc(100% - 40px));
  margin: 0 auto;
  padding: 42px 0 38px;
}
.kicker {
  margin: 0 0 20px;
  color: #f2aa76;
  font-family: var(--mono);
  font-size: 12px;
  letter-spacing: .17em;
  text-transform: uppercase;
}
h1, h2, h3 { font-family: var(--display); }
h1 {
  max-width: 940px;
  margin: 0;
  font-size: clamp(40px, 5.8vw, 72px);
  line-height: .95;
  font-weight: 600;
  letter-spacing: -.045em;
}
.hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 22px;
  align-items: center;
  margin-top: 30px;
  color: rgba(255,248,235,.72);
  font-family: var(--mono);
  font-size: 12px;
}
.status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid rgba(255,255,255,.24);
  border-radius: 999px;
  padding: 7px 11px;
  color: #fff8eb;
}
.status::before { content: ""; width: 8px; height: 8px; border-radius: 50%; background: #72d6a5; }
.status.warning::before { background: #f3c66b; }
.status.error::before { background: #ff7668; }

.review-nav {
  position: sticky;
  top: 0;
  z-index: 20;
  border-bottom: 1px solid var(--line);
  background: color-mix(in srgb, var(--paper) 90%, transparent);
  backdrop-filter: blur(18px);
}
.nav-inner {
  width: min(1320px, calc(100% - 40px));
  margin: 0 auto;
  min-height: 58px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.nav-links { display: flex; gap: 4px; overflow-x: auto; flex: 1; scrollbar-width: none; }
.nav-links::-webkit-scrollbar { display: none; }
.nav-links a {
  white-space: nowrap;
  text-decoration: none;
  padding: 9px 12px;
  border-radius: 999px;
  color: var(--muted);
  font-size: 13px;
}
.nav-links a:hover { color: var(--ink); background: var(--surface); }
.nav-actions { display: flex; gap: 7px; }

main { width: min(1320px, calc(100% - 40px)); margin: 0 auto; padding: 24px 0 96px; }
section { scroll-margin-top: 82px; }
.section-head {
  display: grid;
  grid-template-columns: 70px minmax(0, 1fr);
  gap: 18px;
  align-items: start;
  margin: 76px 0 28px;
}
.section-head > div { min-width: 0; }
.section-index {
  padding-top: 8px;
  border-top: 3px solid var(--accent);
  color: var(--accent);
  font-family: var(--mono);
  font-size: 12px;
}
.section-head h2 { margin: 0; font-size: clamp(31px, 4vw, 50px); line-height: 1; letter-spacing: -.025em; }
.section-head p { margin: 10px 0 0; max-width: 700px; color: var(--muted); overflow-wrap: anywhere; }

.diagram-section .section-head { margin-top: 34px; }
.diagram-studio {
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: var(--studio-chrome);
  color: var(--studio-ink);
  box-shadow: 0 28px 80px rgba(17, 24, 20, 0.22);
}
.diagram-studio-bar {
  min-height: 58px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 9px 12px;
  border-bottom: 1px solid rgba(255,255,255,.12);
}
.diagram-brand {
  display: flex;
  align-items: center;
  gap: 9px;
  min-width: max-content;
  color: rgba(255,248,235,.72);
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: .08em;
  text-transform: uppercase;
}
.diagram-brand::before {
  content: "";
  width: 9px;
  height: 9px;
  border-radius: 2px;
  background: #ff7656;
  box-shadow: 12px 0 0 #f3c66b, 24px 0 0 #6ac9be;
  margin-right: 24px;
}
.diagram-tabs {
  display: flex;
  gap: 4px;
  min-width: 0;
  overflow-x: auto;
  flex: 1;
  scrollbar-width: none;
}
.diagram-tabs::-webkit-scrollbar { display: none; }
.diagram-tab,
.diagram-tool {
  min-height: 36px;
  border-color: rgba(255,255,255,.16);
  border-radius: 7px;
  background: transparent;
  color: rgba(255,248,235,.7);
  font-family: var(--mono);
  font-size: 11px;
  white-space: nowrap;
}
.diagram-tab:hover,
.diagram-tool:hover { border-color: rgba(255,255,255,.42); background: rgba(255,255,255,.08); color: #fff8eb; }
.diagram-tab[aria-selected="true"] { background: #fff8eb; border-color: #fff8eb; color: #14231e; }
.diagram-tools { display: flex; gap: 5px; }
.diagram-tool.square { width: 36px; padding: 0; font-size: 17px; }
.diagram-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  min-height: 680px;
}
.diagram-canvas {
  position: relative;
  overflow: auto;
  min-width: 0;
  min-height: 680px;
  padding: 34px;
  background-color: var(--diagram-canvas);
  background-image: radial-gradient(var(--diagram-grid) 1px, transparent 1px);
  background-size: 18px 18px;
  color: var(--ink);
}
.diagram-preview {
  width: 100%;
  min-height: 600px;
  display: grid;
  place-items: center;
  transform-origin: top center;
  transition: width 160ms ease;
}
.diagram-preview svg { display: block; width: 100%; height: auto; min-width: 520px; }
.diagram-loading,
.diagram-error {
  align-self: center;
  justify-self: center;
  max-width: 560px;
  padding: 22px 24px;
  border: 1px solid var(--line-strong);
  background: var(--surface-solid);
  color: var(--ink);
  font-family: var(--mono);
  font-size: 12px;
}
.diagram-error { border-color: var(--danger); color: var(--danger); }
.diagram-source-panel {
  min-width: 0;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  border-left: 1px solid rgba(255,255,255,.12);
  background: #101815;
}
.diagram-source-panel[hidden], .step-inspector-panel[hidden] { display: none !important; }
.diagram-source-head,
.diagram-source-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 14px;
  color: rgba(255,248,235,.64);
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: .08em;
  text-transform: uppercase;
}
.diagram-source-head { border-bottom: 1px solid rgba(255,255,255,.1); }
.diagram-source-foot { border-top: 1px solid rgba(255,255,255,.1); }
.diagram-source {
  max-height: none;
  overflow: auto;
  padding: 18px;
  border: 0;
  background: transparent;
  color: #d9e4dd;
  font-size: 11px;
  line-height: 1.65;
  white-space: pre;
}
.diagram-render-status { color: #79cbb9; }
.diagram-render-status.error { color: #ff8b82; }
.diagram-zoom-value { min-width: 46px; text-align: center; font-family: var(--mono); font-size: 10px; color: rgba(255,248,235,.62); }

.stats {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 1px;
  background: var(--line);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
}
.stat { min-height: 134px; padding: 24px 20px; background: var(--surface-solid); }
.stat strong { display: block; font-family: var(--display); font-size: 42px; line-height: 1; font-weight: 600; }
.stat span { display: block; margin-top: 15px; color: var(--muted); font-size: 12px; letter-spacing: .04em; }

.meta-strip {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-top: 14px;
}
.meta-card, .panel {
  border: 1px solid var(--line);
  background: var(--surface);
  box-shadow: 0 8px 26px rgba(43,35,25,.06);
}
.meta-card { padding: 18px 20px; }
.meta-card dt { color: var(--muted); font-size: 12px; }
.meta-card dd { margin: 4px 0 0; font-family: var(--mono); font-size: 13px; overflow-wrap: anywhere; }

.flow-list { list-style: none; margin: 0; padding: 0 0 0 54px; counter-reset: flow; }
.flow-step {
  position: relative;
  margin: 0 0 18px;
  padding: 24px 26px 22px;
  border: 1px solid var(--line);
  background: var(--surface);
  box-shadow: 0 10px 34px rgba(43,35,25,.06);
  animation: rise 420ms ease both;
  animation-delay: calc(var(--i) * 45ms);
}
.flow-step::before {
  content: attr(data-step);
  position: absolute;
  left: -54px;
  top: 22px;
  width: 36px;
  height: 36px;
  border: 2px solid var(--teal);
  background: var(--paper);
  color: var(--teal);
  display: grid;
  place-items: center;
  border-radius: 50%;
  font-family: var(--mono);
  font-size: 11px;
  font-weight: 700;
}
.flow-step:not(:last-child)::after {
  content: "";
  position: absolute;
  left: -36px;
  top: 58px;
  bottom: -20px;
  width: 1px;
  background: var(--line-strong);
}
.flow-step h3 { margin: 0; font-size: 25px; font-weight: 600; }
.flow-step p { margin: 9px 0 0; color: var(--muted); }
.source-ref { display: inline-flex; margin-top: 14px; color: var(--teal); font-family: var(--mono); font-size: 11px; }
.condition {
  margin-top: 17px;
  padding: 15px 17px;
  border-left: 4px solid var(--gold);
  background: var(--gold-soft);
}
.condition strong { display: block; color: var(--gold); font-size: 12px; letter-spacing: .06em; text-transform: uppercase; }
.condition p { color: var(--ink); }

.pipeline-list { display: grid; gap: 12px; }
.pipeline {
  display: grid;
  grid-template-columns: minmax(130px, .34fr) minmax(0, 1fr);
  gap: 18px;
  align-items: center;
  padding: 19px 22px;
  border: 1px solid var(--line);
  background: var(--surface);
}
.pipeline h3 { margin: 0; font-family: var(--mono); font-size: 13px; color: var(--accent); }
.sequence { display: flex; align-items: center; gap: 9px; overflow-x: auto; padding: 3px 0; }
.module-pill { white-space: nowrap; border: 1px solid var(--line-strong); background: var(--surface-solid); padding: 7px 11px; font-family: var(--mono); font-size: 11px; }
.arrow { color: var(--accent); font-family: var(--mono); }

.routing-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.route-panel { padding: 24px; }
.route-panel h3 { margin: 0 0 15px; font-size: 24px; }
.route-panel ul { margin: 0; padding: 0; list-style: none; display: grid; gap: 11px; }
.route-panel li { padding: 12px 0 12px 28px; border-top: 1px solid var(--line); position: relative; }
.route-panel li::before { position: absolute; left: 0; top: 13px; font-family: var(--mono); color: var(--teal); content: "IN"; font-size: 10px; }
.route-panel.out li::before { content: "OUT"; color: var(--danger); }
.route-panel code { display: block; margin-top: 6px; color: var(--muted); }

.table-wrap { overflow-x: auto; border: 1px solid var(--line); background: var(--surface); }
table { width: 100%; border-collapse: collapse; min-width: 720px; }
th, td { padding: 14px 16px; text-align: left; border-bottom: 1px solid var(--line); vertical-align: top; }
th { color: var(--muted); font-size: 11px; letter-spacing: .08em; text-transform: uppercase; }
td { font-size: 14px; }
.resource-path { font-family: var(--mono); font-size: 12px; overflow-wrap: anywhere; }
.tag { display: inline-flex; border: 1px solid var(--line-strong); border-radius: 999px; padding: 4px 8px; font-size: 10px; text-transform: uppercase; letter-spacing: .05em; }
.tag.linked { color: var(--teal); background: var(--teal-soft); }
.tag.unlinked { color: var(--muted); }
.tag.missing, .level-error { color: var(--danger); background: var(--danger-soft); }
.level-warning { color: var(--gold); background: var(--gold-soft); }
.level-info { color: var(--teal); background: var(--teal-soft); }

.diagnostics { display: grid; gap: 10px; }
.diagnostic { display: grid; grid-template-columns: auto auto 1fr; gap: 10px; align-items: start; padding: 16px 18px; border: 1px solid var(--line); background: var(--surface); }
.diagnostic .level { padding: 4px 8px; font-family: var(--mono); font-size: 10px; text-transform: uppercase; }
.diagnostic code { color: var(--muted); }

details { border: 1px solid var(--line); background: var(--surface); margin-top: 12px; }
summary { cursor: pointer; padding: 17px 19px; font-weight: 600; }
.details-body { padding: 0 19px 19px; }
.code-tools { display: flex; gap: 8px; margin-bottom: 10px; }
pre { margin: 0; max-height: 520px; overflow: auto; padding: 18px; background: #14231e; color: #f8eedb; font-size: 12px; line-height: 1.55; tab-size: 2; }
.edge-list { columns: 2; column-gap: 34px; margin: 0; padding-left: 20px; }
.edge-list li { break-inside: avoid; margin-bottom: 7px; font-family: var(--mono); font-size: 11px; }
.honesty-note { margin-top: 30px; padding: 20px 22px; border: 1px solid var(--line); border-left: 5px solid var(--accent); background: var(--accent-soft); }
footer { width: min(1180px, calc(100% - 40px)); margin: 0 auto; padding: 0 0 54px; color: var(--muted); font-family: var(--mono); font-size: 11px; }

/* Purpose-first restrained layout. Mermaid stays primary; evidence is progressive. */
:root {
  --paper: #f6f7f5;
  --paper-deep: #eceeeb;
  --surface: #ffffff;
  --surface-solid: #ffffff;
  --ink: #17211d;
  --muted: #68716d;
  --line: #dfe3e0;
  --line-strong: #bcc4bf;
  --accent: #176b57;
  --accent-soft: #e8f2ee;
  --teal: #176b57;
  --teal-soft: #e8f2ee;
  --gold: #8a6417;
  --gold-soft: #f7f0dc;
  --danger: #a23b36;
  --danger-soft: #f8e9e7;
  --diagram-canvas: #fbfcfb;
  --diagram-grid: rgba(23, 33, 29, 0.055);
  --studio-chrome: #ffffff;
  --studio-ink: #17211d;
  --shadow: none;
}
body { background: var(--paper); line-height: 1.58; }
button {
  min-height: 36px;
  border-radius: 7px;
  padding: 0 12px;
  box-shadow: none;
  transition: border-color 140ms ease, background 140ms ease, color 140ms ease;
}
button:hover { transform: none; background: var(--paper); }
.hero { background: #ffffff; color: var(--ink); border-bottom: 1px solid var(--line); }
.hero::before { display: none; }
.hero-inner { padding: 28px 0 24px; }
.kicker { margin-bottom: 12px; color: var(--muted); font-size: 10px; letter-spacing: .12em; }
h1 { max-width: none; font-size: clamp(32px, 4vw, 48px); line-height: 1.06; letter-spacing: -.025em; }
.hero-meta { margin-top: 16px; color: var(--muted); gap: 8px 18px; font-size: 11px; }
.status { color: var(--ink); border-color: var(--line-strong); padding: 5px 9px; }
.review-nav { background: rgba(246,247,245,.96); backdrop-filter: blur(10px); }
.nav-inner { min-height: 50px; }
.nav-links a { padding: 7px 10px; font-size: 12px; }
.nav-actions button { background: transparent; }
main { padding-top: 16px; }
.section-head,
.diagram-section .section-head {
  display: block;
  margin: 48px 0 18px;
}
.diagram-section .section-head { margin-top: 18px; }
.section-index { display: none; }
.section-head h2 { font-size: clamp(25px, 3vw, 34px); line-height: 1.15; letter-spacing: -.015em; }
.section-head p { margin-top: 7px; max-width: 760px; font-size: 14px; }
.diagram-studio {
  border-color: var(--line);
  border-radius: 9px;
  background: #ffffff;
  color: var(--ink);
  box-shadow: none;
}
.diagram-studio-bar {
  min-height: 52px;
  padding: 8px 10px;
  border-color: var(--line);
  background: #f7f8f7;
}
.diagram-brand { color: var(--muted); font-size: 10px; }
.diagram-brand::before { display: none; }
.diagram-tab,
.diagram-tool {
  min-height: 34px;
  border-color: transparent;
  background: transparent;
  color: var(--muted);
}
.diagram-tab:hover,
.diagram-tool:hover { border-color: var(--line); background: #ffffff; color: var(--ink); }
.diagram-tab[aria-selected="true"] { background: #ffffff; border-color: var(--line-strong); color: var(--ink); }
.diagram-tools { padding-left: 8px; border-left: 1px solid var(--line); }
.diagram-workspace { grid-template-columns: minmax(0, 1fr); min-height: 720px; }
.diagram-studio.source-open .diagram-workspace { grid-template-columns: minmax(0, 1fr) 360px; }
.diagram-canvas { min-height: 720px; padding: 28px; }
.diagram-preview { min-height: 660px; }
.diagram-source-panel { border-color: var(--line); }
.stats { border-radius: 8px; overflow: hidden; box-shadow: none; }
.stat { min-height: 92px; padding: 17px 18px; }
.stat strong { font-size: 30px; }
.stat span { margin-top: 9px; }
.meta-card, .panel, .flow-step, .pipeline, .diagnostic { box-shadow: none; }
.meta-card { padding: 14px 16px; }
.flow-step { animation: none; }
.evidence-disclosure { margin-top: 0; border-radius: 8px; overflow: hidden; }
.evidence-disclosure > summary { list-style: none; display: flex; align-items: center; justify-content: space-between; font-size: 14px; }
.evidence-disclosure > summary::-webkit-details-marker { display: none; }
.evidence-disclosure > summary::after { content: "展开"; color: var(--muted); font-family: var(--mono); font-size: 10px; font-weight: 400; }
.evidence-disclosure[open] > summary::after { content: "收起"; }
.evidence-disclosure .details-body { padding: 10px 18px 20px; }
.evidence-disclosure .flow-list { margin-top: 10px; }
.honesty-note { background: #ffffff; border-left-width: 1px; }
footer { width: min(1320px, calc(100% - 40px)); }

.trust-verdict {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(260px, .55fr);
  gap: 18px;
  margin: 0 0 18px;
  padding: 22px 24px;
  border: 1px solid var(--line);
  border-left: 4px solid var(--gold);
  border-radius: 8px;
  background: #ffffff;
}
.trust-verdict h2 { margin: 4px 0 8px; font-size: clamp(23px, 2.8vw, 32px); }
.trust-verdict p { margin: 0; color: var(--muted); }
.trust-verdict .eyebrow { color: var(--gold); font-family: var(--mono); font-size: 10px; letter-spacing: .1em; text-transform: uppercase; }
.trust-boundary { align-self: center; padding-left: 18px; border-left: 1px solid var(--line); }
.trust-boundary strong { display: block; margin-bottom: 6px; font-size: 13px; }
.trust-boundary span { display: block; color: var(--muted); font-size: 12px; }
.stats { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.step-selector-strip {
  display: flex;
  gap: 6px;
  margin: 0 0 10px;
  overflow-x: auto;
  scrollbar-width: thin;
}
.step-selector {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: max-content;
  border-color: var(--line);
  background: #ffffff;
  color: var(--muted);
  font-size: 12px;
}
.step-selector span { font-family: var(--mono); color: var(--accent); }
.step-selector[aria-pressed="true"] { border-color: var(--accent); background: var(--accent-soft); color: var(--ink); }
.trust-workspace { display: grid; grid-template-columns: minmax(0, 1.55fr) minmax(360px, .72fr); gap: 12px; align-items: start; }
.trust-workspace.non-runtime { grid-template-columns: minmax(0, 1fr); }
.trust-workspace.non-runtime .step-inspector { display: none; }
.trust-workspace .diagram-workspace { min-height: 640px; }
.trust-workspace .diagram-canvas { min-height: 640px; }
.trust-workspace .diagram-preview { min-height: 580px; }
.step-inspector {
  position: sticky;
  top: 62px;
  max-height: calc(100vh - 78px);
  overflow: auto;
  border: 1px solid var(--line);
  border-radius: 9px;
  background: #ffffff;
}
.step-inspector-panel > header { padding: 22px 22px 18px; border-bottom: 1px solid var(--line); }
.step-inspector-panel > header p { margin: 0 0 6px; color: var(--muted); font-family: var(--mono); font-size: 10px; text-transform: uppercase; letter-spacing: .08em; }
.step-inspector-panel > header h3 { margin: 0; font-size: 25px; line-height: 1.16; }
.step-inspector-panel > header .source-ref { margin-top: 10px; }
.step-inspector-panel > section { padding: 20px 22px; border-top: 1px solid var(--line); }
.step-inspector-panel h4 { margin: 0 0 12px; font-size: 14px; }
.step-inspector-panel h5 { margin: 16px 0 8px; color: var(--muted); font-size: 11px; letter-spacing: .04em; }
.assurance-row { display: flex; flex-wrap: wrap; gap: 6px; padding: 12px 22px; background: #f7f8f7; }
.assurance-row span { padding: 4px 7px; border: 1px solid var(--line-strong); border-radius: 999px; color: var(--accent); font-size: 10px; }
.assurance-row span.gap { color: var(--gold); border-color: #d8c187; background: var(--gold-soft); }
.assurance-row span.observed { color: var(--teal); background: var(--teal-soft); }
.step-detail-list, .module-step-list, .module-gate-list, .verification-list, .resource-chip-list, .pipeline-support-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }
.step-detail-item { position: relative; padding: 11px 12px; border: 1px solid var(--line); border-radius: 6px; }
.step-detail-item p { margin: 5px 0 6px; color: var(--ink); font-size: 13px; }
.step-detail-item code, .module-step-list code, .module-gate-list code, .verification-list code { display: block; color: var(--muted); font-size: 10px; }
.detail-kind { color: var(--accent); font-family: var(--mono); font-size: 9px; letter-spacing: .06em; }
.module-evidence { margin: 0 0 8px; border-radius: 6px; }
.module-evidence summary { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 12px; }
.module-evidence summary span { color: var(--muted); font-size: 10px; }
.module-body { padding: 0 12px 14px; }
.module-body > p { color: var(--muted); font-size: 12px; }
.module-step-list li, .module-gate-list li, .verification-list li { padding: 9px 0; border-top: 1px solid var(--line); }
.module-step-list strong { display: block; font-size: 12px; }
.module-step-list span { display: block; margin: 3px 0 5px; color: var(--muted); font-size: 11px; }
.module-gate-list li, .verification-list li { font-size: 12px; }
.resource-chip-list li code { display: block; padding: 7px 8px; background: var(--paper); overflow-wrap: anywhere; }
.pipeline-support-list li { padding: 9px 10px; border: 1px solid var(--line); border-radius: 6px; }
.pipeline-support-list code { display: block; margin-bottom: 4px; color: var(--accent); }
.pipeline-support-list span { display: block; color: var(--muted); font-size: 11px; overflow-wrap: anywhere; }
.evidence-gap, .effect-copy { margin: 0; padding: 11px 12px; border-left: 3px solid var(--gold); background: var(--gold-soft); color: #604814; font-size: 12px; }
.verification-list { margin-top: 10px; }
.empty-evidence { color: var(--muted); font-size: 12px; }
.diagram-preview g.node.inspectable-step { cursor: pointer; }
.diagram-preview g.node.inspectable-step:hover > rect,
.diagram-preview g.node.inspectable-step:hover > polygon,
.diagram-preview g.node.inspectable-step:focus > rect,
.diagram-preview g.node.inspectable-step:focus > polygon,
.diagram-preview g.node.inspectable-step.selected-step > rect,
.diagram-preview g.node.inspectable-step.selected-step > polygon { stroke: #0d5b48 !important; stroke-width: 4px !important; filter: drop-shadow(0 3px 5px rgba(23,107,87,.18)); }
.external-boundary-note { margin: 0 0 12px; color: var(--muted); font-size: 13px; }

@keyframes rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@media (prefers-reduced-motion: reduce) { * { scroll-behavior: auto !important; animation: none !important; transition: none !important; } }
@media (max-width: 960px) {
  .trust-workspace { grid-template-columns: 1fr; }
  .step-inspector { position: static; max-height: none; }
  .diagram-studio.source-open .diagram-workspace { grid-template-columns: 1fr; }
  .diagram-source-panel { border-left: 0; border-top: 1px solid rgba(255,255,255,.12); max-height: 360px; }
  .diagram-tools [data-export-svg] { display: none; }
  .stats { grid-template-columns: repeat(3, 1fr); }
  .meta-strip { grid-template-columns: 1fr; }
  .pipeline { grid-template-columns: 1fr; gap: 8px; }
}
@media (max-width: 700px) {
  .trust-verdict { grid-template-columns: 1fr; padding: 18px; }
  .trust-boundary { padding: 14px 0 0; border-left: 0; border-top: 1px solid var(--line); }
  .hero-inner, .nav-inner, main, footer { width: min(100% - 24px, 1180px); }
  .hero-inner { padding: 22px 0 20px; }
  h1 { font-size: clamp(30px, 10vw, 42px); }
  .nav-actions { display: none; }
  .diagram-studio-bar { align-items: stretch; flex-direction: column; }
  .diagram-brand { padding: 4px 2px; }
  .diagram-tabs { width: 100%; }
  .diagram-tools { width: 100%; }
  .diagram-tool { flex: 1; }
  .diagram-tool.square { width: auto; }
  .diagram-canvas { min-height: 520px; padding: 18px 12px; }
  .diagram-preview { min-height: 480px; align-items: start; }
  .diagram-preview svg { min-width: 0; }
  .diagram-source-panel { max-height: 300px; }
  .stats { grid-template-columns: repeat(2, 1fr); }
  .stat { min-height: 108px; padding: 19px 16px; }
  .stat strong { font-size: 34px; }
  .section-head { grid-template-columns: 46px minmax(0, 1fr); margin-top: 58px; }
  .routing-grid { grid-template-columns: 1fr; }
  .flow-list { padding-left: 42px; }
  .flow-step { padding: 20px 18px; }
  .flow-step::before { left: -42px; width: 30px; height: 30px; }
  .flow-step:not(:last-child)::after { left: -27px; top: 52px; }
  .diagnostic { grid-template-columns: auto 1fr; }
  .diagnostic p { grid-column: 1 / -1; margin: 0; }
  .edge-list { columns: 1; }
}
@media print {
  .review-nav, .code-tools { display: none !important; }
  body { background: white; color: #111; }
  .hero { background: white; color: #111; border-top: 8px solid #d64e31; }
  .hero::before { display: none; }
  .hero-meta, .kicker { color: #555; }
  main { width: 100%; padding-top: 16px; }
  .diagram-studio-bar, .diagram-source-panel { display: none !important; }
  .diagram-studio, .diagram-canvas { border: 0; box-shadow: none; background: white; }
  .diagram-workspace, .diagram-canvas { min-height: 0; display: block; }
  .diagram-preview { min-height: 0; }
  .flow-step, .panel, .meta-card, .pipeline, .stat { box-shadow: none; break-inside: avoid; }
  details { break-inside: avoid; }
}
"""


HTML_JS = r"""
(() => {
  const root = document.documentElement;
  const printButton = document.querySelector('[data-print]');
  const downloadButton = document.querySelector('[data-download-json]');
  const modelNode = document.getElementById('logic-model');
  const studio = document.querySelector('[data-diagram-studio]');
  const preview = document.querySelector('[data-diagram-preview]');
  const sourceView = document.querySelector('[data-diagram-source]');
  const sourceName = document.querySelector('[data-diagram-source-name]');
  const sourcePanel = document.querySelector('[data-diagram-source-panel]');
  const sourceToggle = document.querySelector('[data-toggle-source]');
  const renderStatus = document.querySelector('[data-diagram-render-status]');
  const zoomValue = document.querySelector('[data-diagram-zoom-value]');
  const trustWorkspace = document.querySelector('[data-trust-workspace]');
  const stepInspector = document.querySelector('[data-step-inspector]');
  const stepSelectors = Array.from(document.querySelectorAll('[data-select-step]'));
  const stepPanels = Array.from(document.querySelectorAll('[data-step-panel]'));
  const tabs = Array.from(document.querySelectorAll('[data-diagram-key]'));
  const cache = new Map();
  let activeKey = tabs[0]?.dataset.diagramKey || 'runtime';
  let selectedStepId = stepSelectors[0]?.dataset.selectStep || '';
  let zoom = 1;

  const definitions = tabs.map((tab) => {
    const sourceNode = document.querySelector(tab.dataset.sourceTarget);
    return {
      key: tab.dataset.diagramKey,
      label: tab.textContent.trim(),
      source: sourceNode?.textContent || '',
      tab,
    };
  });

  const copyText = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (_) {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.setAttribute('readonly', '');
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      textarea.remove();
    }
  };

  const pulseCopied = (button) => {
    const original = button.textContent;
    button.textContent = button.dataset.copiedLabel || 'Copied';
    window.setTimeout(() => { button.textContent = original; }, 1400);
  };

  const updateZoom = () => {
    preview.style.width = `${Math.round(zoom * 100)}%`;
    zoomValue.textContent = `${Math.round(zoom * 100)}%`;
  };

  const selectStep = (stepId, reveal = false) => {
    if (!stepId) return;
    selectedStepId = stepId;
    stepSelectors.forEach((button) => {
      button.setAttribute('aria-pressed', String(button.dataset.selectStep === stepId));
    });
    stepPanels.forEach((panel) => {
      panel.hidden = panel.dataset.stepPanel !== stepId;
    });
    preview.querySelectorAll('g.node.inspectable-step').forEach((node) => {
      node.classList.toggle('selected-step', node.dataset.stepId === stepId);
    });
    if (reveal && window.innerWidth <= 960) {
      stepInspector?.scrollIntoView({behavior: 'smooth', block: 'start'});
    }
  };

  const bindRuntimeSteps = () => {
    if (activeKey !== 'runtime') return;
    preview.querySelectorAll('g.node').forEach((node) => {
      const match = node.id.match(/step_\d+/);
      if (!match) return;
      const stepId = match[0];
      node.dataset.stepId = stepId;
      node.classList.add('inspectable-step');
      node.setAttribute('role', 'button');
      node.setAttribute('tabindex', '0');
      node.setAttribute('aria-label', `${node.textContent.trim()} · ${studio.dataset.inspectLabel}`);
      node.addEventListener('click', () => selectStep(stepId, true));
      node.addEventListener('keydown', (event) => {
        if (!['Enter', ' '].includes(event.key)) return;
        event.preventDefault();
        selectStep(stepId, true);
      });
    });
    selectStep(selectedStepId);
  };

  const showDiagram = (key) => {
    const definition = definitions.find((item) => item.key === key);
    if (!definition) return;
    activeKey = key;
    zoom = 1;
    updateZoom();
    tabs.forEach((tab) => {
      const selected = tab.dataset.diagramKey === key;
      tab.setAttribute('aria-selected', String(selected));
      tab.tabIndex = selected ? 0 : -1;
    });
    sourceName.textContent = `${definition.label} · Mermaid`;
    sourceView.textContent = definition.source;
    const result = cache.get(key);
    if (!result) {
      preview.innerHTML = `<div class="diagram-loading">${studio.dataset.loadingLabel}</div>`;
      return;
    }
    if (result.error) {
      preview.innerHTML = `<div class="diagram-error">${result.error}</div>`;
      return;
    }
    preview.innerHTML = result.svg;
    const svg = preview.querySelector('svg');
    if (svg) {
      svg.removeAttribute('height');
      svg.setAttribute('role', 'img');
      svg.setAttribute('aria-label', definition.label);
    }
    trustWorkspace?.classList.toggle('non-runtime', key !== 'runtime');
    bindRuntimeSteps();
  };

  const renderDiagrams = async () => {
    if (!studio || typeof mermaid === 'undefined') {
      root.dataset.mermaidReady = 'error';
      renderStatus.textContent = studio?.dataset.rendererMissing || 'Mermaid renderer unavailable';
      renderStatus.classList.add('error');
      preview.innerHTML = `<div class="diagram-error">${renderStatus.textContent}</div>`;
      return;
    }
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: 'strict',
      suppressErrorRendering: true,
      theme: 'base',
      look: 'classic',
      flowchart: {
        curve: 'basis',
        htmlLabels: false,
        nodeSpacing: 34,
        rankSpacing: 52,
        padding: 18,
        useMaxWidth: true,
      },
      themeVariables: {
        fontFamily: 'Avenir Next, Gill Sans, Trebuchet MS, sans-serif',
        fontSize: '15px',
        primaryColor: '#ecfdf5',
        primaryTextColor: '#14231e',
        primaryBorderColor: '#0b6f67',
        secondaryColor: '#fef3c7',
        secondaryTextColor: '#4f3507',
        secondaryBorderColor: '#a66b12',
        tertiaryColor: '#f4d8cb',
        tertiaryTextColor: '#542015',
        tertiaryBorderColor: '#d64e31',
        lineColor: '#557068',
        edgeLabelBackground: '#fffdf8',
        clusterBkg: '#f4efe5',
        clusterBorder: '#b8aa95',
      },
    });
    renderStatus.textContent = studio.dataset.renderingLabel;
    let rendered = 0;
    for (let index = 0; index < definitions.length; index += 1) {
      const definition = definitions[index];
      try {
        const result = await mermaid.render(`skill-mermaid-${definition.key}-${index}`, definition.source);
        cache.set(definition.key, {svg: result.svg});
        rendered += 1;
      } catch (error) {
        cache.set(definition.key, {error: String(error?.message || error)});
      }
    }
    studio.dataset.renderedCount = String(rendered);
    root.dataset.mermaidReady = rendered === definitions.length ? 'true' : 'partial';
    renderStatus.textContent = rendered === definitions.length
      ? studio.dataset.readyLabel
      : `${rendered}/${definitions.length} ${studio.dataset.partialLabel}`;
    renderStatus.classList.toggle('error', rendered !== definitions.length);
    showDiagram(activeKey);
  };

  tabs.forEach((tab) => {
    tab.addEventListener('click', () => showDiagram(tab.dataset.diagramKey));
    tab.addEventListener('keydown', (event) => {
      if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
      event.preventDefault();
      const index = tabs.indexOf(tab);
      const delta = event.key === 'ArrowRight' ? 1 : -1;
      const next = tabs[(index + delta + tabs.length) % tabs.length];
      next.focus();
      showDiagram(next.dataset.diagramKey);
    });
  });
  stepSelectors.forEach((button) => {
    button.addEventListener('click', () => selectStep(button.dataset.selectStep, true));
  });

  document.querySelector('[data-zoom-in]')?.addEventListener('click', () => {
    zoom = Math.min(2, zoom + 0.15);
    updateZoom();
  });
  document.querySelector('[data-zoom-out]')?.addEventListener('click', () => {
    zoom = Math.max(0.45, zoom - 0.15);
    updateZoom();
  });
  document.querySelector('[data-fit-diagram]')?.addEventListener('click', () => {
    zoom = 1;
    updateZoom();
    document.querySelector('.diagram-canvas')?.scrollTo({top: 0, left: 0, behavior: 'smooth'});
  });
  sourceToggle?.addEventListener('click', () => {
    const open = sourceToggle.getAttribute('aria-pressed') !== 'true';
    sourceToggle.setAttribute('aria-pressed', String(open));
    sourceToggle.textContent = open ? sourceToggle.dataset.hideLabel : sourceToggle.dataset.showLabel;
    sourcePanel.hidden = !open;
    studio.classList.toggle('source-open', open);
  });
  document.querySelector('[data-copy-diagram-source]')?.addEventListener('click', async (event) => {
    await copyText(sourceView.textContent);
    pulseCopied(event.currentTarget);
  });
  document.querySelector('[data-export-svg]')?.addEventListener('click', () => {
    const svg = preview.querySelector('svg');
    if (!svg) return;
    const clone = svg.cloneNode(true);
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    const blob = new Blob([`<?xml version="1.0" encoding="UTF-8"?>\n${clone.outerHTML}`], {type: 'image/svg+xml;charset=utf-8'});
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${studio.dataset.filenamePrefix}-${activeKey}.svg`;
    link.click();
    URL.revokeObjectURL(link.href);
  });

  printButton?.addEventListener('click', () => window.print());
  downloadButton?.addEventListener('click', () => {
    const blob = new Blob([modelNode.textContent], {type: 'application/json;charset=utf-8'});
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = downloadButton.dataset.filename;
    link.click();
    URL.revokeObjectURL(link.href);
  });
  document.querySelectorAll('[data-copy-target]').forEach((button) => {
    button.addEventListener('click', async () => {
      const target = document.querySelector(button.dataset.copyTarget);
      if (!target) return;
      await copyText(target.textContent);
      pulseCopied(button);
    });
  });

  updateZoom();
  showDiagram(activeKey);
  renderDiagrams();
})();
"""


def html_text(value: Any) -> str:
    return html_lib.escape(compact(value), quote=True)


def html_source(source: Dict[str, Any]) -> str:
    return html_text(source_label(source))


def _render_html_interactive_legacy(model: Dict[str, Any], direction: str, language: str) -> str:
    """Render a self-contained review interface with no external assets."""
    zh = choose_language(model, language)
    skill = model["skill"]
    coverage = model["coverage"]
    trust = model.get("trust", {})
    diagnostics = model["diagnostics"]
    errors = sum(1 for item in diagnostics if item["level"] == "error")
    warnings = sum(1 for item in diagnostics if item["level"] == "warning")
    status_class = "error" if errors else "warning" if warnings or diagnostics else ""
    status_label = (
        f"{errors} 个错误" if zh and errors else
        f"{warnings} 个警告" if zh and warnings else
        "仅信息诊断" if zh and diagnostics else
        "结构检查通过" if zh else
        f"{errors} errors" if errors else
        f"{warnings} warnings" if warnings else
        "Informational diagnostics only" if diagnostics else
        "Structural checks passed"
    )
    labels = {
        "diagrams": "内部运行" if zh else "Internal Runtime",
        "overview": "信任概览" if zh else "Trust Overview",
        "flow": "步骤证据" if zh else "Step Evidence",
        "kit": "Kit 管线" if zh else "Kit Pipelines",
        "routing": "外部适用边界" if zh else "External Activation Boundary",
        "resources": "资源" if zh else "Resources",
        "diagnostics": "风险与缺口" if zh else "Risks and Gaps",
        "artifacts": "源码与模型" if zh else "Sources and Model",
        "print": "打印" if zh else "Print",
        "download": "下载 JSON" if zh else "Download JSON",
        "copy": "复制" if zh else "Copy",
        "copied": "已复制" if zh else "Copied",
    }
    runtime_mermaid = render_runtime_mermaid(model, direction, zh)
    resource_mermaid = render_resource_mermaid(model, zh)
    kit_mermaid = render_kit_mermaid(model, zh)
    model_json = json.dumps(model, ensure_ascii=False, indent=2, sort_keys=True)
    embedded_json = model_json.replace("</", "<\\/")
    mermaid_bundle = load_mermaid_bundle()

    diagram_specs = [
        ("runtime", "内部运行" if zh else "Internal Runtime", "#runtime-mermaid"),
        ("resources", "资源关系" if zh else "Resources", "#resource-mermaid"),
    ]
    if kit_mermaid:
        diagram_specs.append(("kit", "Kit 管线" if zh else "Kit Pipelines", "#kit-mermaid"))
    diagram_ready_label = (
        f"已渲染 {len(diagram_specs)} 张图"
        if zh
        else f"{len(diagram_specs)} diagrams rendered"
    )
    flow_evidence_label = (
        f"查看 {coverage['workflow_steps']} 个步骤的源码证据"
        if zh
        else f"View source evidence for {coverage['workflow_steps']} steps"
    )
    kit_detail_label = (
        f"查看 {coverage['kit_pipelines']} 条管线的文字明细"
        if zh
        else f"View text details for {coverage['kit_pipelines']} pipelines"
    )
    resource_detail_label = (
        f"查看 {len(model['resources'])} 个资源的明细"
        if zh
        else f"View details for {len(model['resources'])} resources"
    )
    diagram_tabs_html = "".join(
        f'<button type="button" class="diagram-tab" role="tab" '
        f'id="diagram-tab-{key}" aria-controls="diagram-preview" '
        f'aria-selected="{str(index == 0).lower()}" tabindex="{0 if index == 0 else -1}" '
        f'data-diagram-key="{key}" data-source-target="{source_target}">{html_text(label)}</button>'
        for index, (key, label, source_target) in enumerate(diagram_specs)
    )

    stat_values = [
        (coverage["workflow_steps"], "内部步骤" if zh else "Internal steps"),
        (coverage.get("steps_with_support", 0), "有能力依据" if zh else "Steps with support"),
        (coverage.get("steps_with_checks", 0), "有验收规则" if zh else "Steps with checks"),
        (coverage.get("observed_artifacts", 0), "真实运行案例" if zh else "Observed cases"),
    ]
    stats_html = "".join(
        f'<div class="stat"><strong>{value}</strong><span>{html_text(label)}</span></div>'
        for value, label in stat_values
    )
    nav_items = ["overview", "diagrams", "diagnostics", "routing", "artifacts"]
    nav_html = "".join(
        f'<a href="#{item}">{html_text(labels[item])}</a>' for item in nav_items
    )

    module_by_id = {
        compact(item.get("id")): item
        for item in model.get("kit", {}).get("modules", [])
        if isinstance(item, dict)
    }
    pipeline_by_id = {
        compact(item.get("id") or item.get("name")): item
        for item in model.get("kit", {}).get("pipelines", [])
        if isinstance(item, dict)
    }
    detail_kind_labels = {
        "output": "声明产物" if zh else "Declared output",
        "criterion": "判断依据" if zh else "Criterion",
        "decision": "决策映射" if zh else "Decision map",
        "verification": "验证动作" if zh else "Verification",
        "guardrail": "边界约束" if zh else "Guardrail",
        "command": "执行命令" if zh else "Command",
        "instruction": "执行动作" if zh else "Instruction",
    }
    step_selectors: List[str] = []
    step_inspectors: List[str] = []
    step_items: List[str] = []
    for index, step in enumerate(model["workflow"]["steps"], start=1):
        conditions = "".join(
            '<div class="condition">'
            f'<strong>{html_text("条件" if zh else "Condition")}</strong>'
            f'<p>{html_text(display_text(condition["text"], zh))}</p>'
            + (
                f'<p><b>{html_text("动作" if zh else "Action")}:</b> {html_text(display_text(condition["action"], zh))}</p>'
                if condition.get("action") else ""
            )
            + f'<code>{html_source(condition["source"])}</code></div>'
            for condition in step.get("conditions", [])
        )
        step_items.append(
            f'<li class="flow-step" style="--i:{index}" data-step="{html_text(step["number"])}">'
            f'<h3>{html_text(display_text(step["title"], zh))}</h3>'
            f'<p>{html_text(display_text(step.get("summary") or ("未提取摘要" if zh else "No summary extracted"), zh))}</p>'
            f'<span class="source-ref">{html_source(step["source"])}</span>{conditions}</li>'
        )
        step_selectors.append(
            f'<button type="button" class="step-selector" data-select-step="{html_text(step["id"])}" '
            f'aria-pressed="{str(index == 1).lower()}"><span>{html_text(step["number"])}</span>'
            f'{html_text(display_text(step["title"], zh))}</button>'
        )
        detail_items = "".join(
            '<li class="step-detail-item">'
            f'<span class="detail-kind">{html_text(detail_kind_labels.get(item.get("kind"), detail_kind_labels["instruction"]))}</span>'
            f'<p>{html_text(display_text(item.get("text"), zh))}</p>'
            f'<code>{html_source(item.get("source", step["source"]))}</code></li>'
            for item in step.get("details", [])
        ) or (
            f'<li class="empty-evidence">{html_text("没有提取到可审阅的执行细节。" if zh else "No reviewable execution detail was extracted.")}</li>'
        )
        resources_html = "".join(
            f'<li><code>{html_text(path)}</code></li>' for path in step.get("resources", [])
        )
        module_sections: List[str] = []
        linked_gate_items: List[str] = []
        for module_id in step.get("module_ids", []):
            module = module_by_id.get(module_id)
            if not module:
                continue
            module_steps = "".join(
                '<li>'
                f'<strong>{html_text(display_text(item.get("title"), zh))}</strong>'
                f'<span>{html_text(display_text(item.get("summary"), zh))}</span>'
                f'<code>{html_source(item.get("source", {}))}</code></li>'
                for item in module.get("workflow_steps", [])
            )
            module_gates = "".join(
                f'<li>{html_text(display_text(item.get("text"), zh))}<code>{html_source(item.get("source", {}))}</code></li>'
                for item in module.get("quality_gates", [])
            )
            linked_gate_items.extend(
                f'<li>{html_text(display_text(item.get("text"), zh))}<code>{html_source(item.get("source", {}))}</code></li>'
                for item in module.get("quality_gates", [])
            )
            module_sections.append(
                '<details class="module-evidence">'
                f'<summary><code>{html_text(module_id)}</code><span>{len(module.get("workflow_steps", []))} '
                f'{html_text("个子步骤" if zh else "substeps")}</span></summary>'
                '<div class="module-body">'
                + (f'<p>{html_text(display_text(module.get("description"), zh))}</p>' if module.get("description") else "")
                + (f'<h5>{html_text("模块内部流程" if zh else "Module workflow")}</h5><ol class="module-step-list">{module_steps}</ol>' if module_steps else "")
                + (f'<h5>{html_text("模块质量门" if zh else "Module quality gate")}</h5><ul class="module-gate-list">{module_gates}</ul>' if module_gates else "")
                + '</div></details>'
            )
        support_html = "".join(module_sections)
        if step.get("pipeline_ids"):
            pipeline_support = "".join(
                '<li><code>' + html_text(pipeline_id) + '</code><span>'
                + html_text(
                    " → ".join(
                        compact(item.get("module") or item.get("id"))
                        if isinstance(item, dict) else compact(item)
                        for item in (
                            pipeline_by_id.get(pipeline_id, {}).get("steps")
                            or pipeline_by_id.get(pipeline_id, {}).get("modules")
                            or []
                        )
                    )
                )
                + '</span></li>'
                for pipeline_id in step.get("pipeline_ids", [])
                if pipeline_id in pipeline_by_id
            )
            if pipeline_support:
                support_html += (
                    f'<h5>{html_text("关联执行管线" if zh else "Associated pipelines")}</h5>'
                    f'<ul class="pipeline-support-list">{pipeline_support}</ul>'
                )
        if resources_html:
            support_html += f'<h5>{html_text("直接引用资源" if zh else "Direct resources")}</h5><ul class="resource-chip-list">{resources_html}</ul>'
        if not support_html:
            support_html = f'<p class="evidence-gap">{html_text("本步骤只有控制器声明，未直接关联模块、脚本或参考文档。" if zh else "This step has only a controller declaration and no directly linked module, script, or reference.")}</p>'
        verification_items = [
            item for item in step.get("details", []) if item.get("kind") == "verification"
        ]
        verification_html = "".join(
            f'<li>{html_text(display_text(item.get("text"), zh))}<code>{html_source(item.get("source", step["source"]))}</code></li>'
            for item in verification_items
        ) + "".join(linked_gate_items)
        effect_status = step.get("assurance", {}).get("effect_evidence")
        effect_copy = (
            "已发现可回读的案例或运行产物。" if zh else "Observed cases or runtime artifacts are available."
        ) if effect_status == "observed" else (
            "未发现与本步骤绑定的真实运行案例；以下内容证明“如何声明”，不能单独证明“实际效果”。"
            if zh else
            "No observed runtime case is bound to this step; the evidence below proves what is declared, not the real-world effect."
        )
        verification_block = (
            f'<ul class="verification-list">{verification_html}</ul>'
            if verification_html else
            f'<p class="evidence-gap">{html_text("没有提取到步骤级验收标准，效果需要通过真实任务案例补证。" if zh else "No step-level acceptance criterion was extracted; a real task case is needed to verify effect.")}</p>'
        )
        execution_label = (
            "确定性脚本" if zh else "Deterministic script"
        ) if step.get("assurance", {}).get("execution_mode") == "deterministic_script" else (
            "Agent 指令" if zh else "Agent instruction"
        )
        step_inspectors.append(
            f'<article class="step-inspector-panel" data-step-panel="{html_text(step["id"])}" '
            + ("" if index == 1 else "hidden") + ">"
            f'<header><p>{html_text("内部步骤" if zh else "Internal step")} {html_text(step["number"])}</p>'
            f'<h3>{html_text(display_text(step["title"], zh))}</h3>'
            f'<span class="source-ref">{html_source(step["source"])}</span></header>'
            '<div class="assurance-row">'
            f'<span>{html_text("来源可追溯" if zh else "Source-bound")}</span>'
            f'<span>{html_text(execution_label)}</span>'
            f'<span class="{("observed" if effect_status == "observed" else "gap")}">{html_text("有效果案例" if zh and effect_status == "observed" else "效果未观察" if zh else "Observed effect" if effect_status == "observed" else "Effect unobserved")}</span>'
            '</div>'
            f'<section><h4>{html_text("具体怎么做" if zh else "How it works")}</h4><ol class="step-detail-list">{detail_items}</ol></section>'
            f'<section><h4>{html_text("能力依据" if zh else "Capability basis")}</h4>{support_html}</section>'
            f'<section><h4>{html_text("如何判断效果" if zh else "How effect is judged")}</h4><p class="effect-copy">{html_text(effect_copy)}</p>{verification_block}</section>'
            '</article>'
        )
    flow_html = "".join(step_items)
    step_selector_html = "".join(step_selectors)
    step_inspector_html = "".join(step_inspectors)

    pipelines_html = ""
    for pipeline in model.get("kit", {}).get("pipelines", []):
        if not isinstance(pipeline, dict):
            continue
        modules = pipeline.get("steps") or pipeline.get("modules") or []
        sequence: List[str] = []
        for module_index, module in enumerate(modules if isinstance(modules, list) else []):
            if module_index:
                sequence.append('<span class="arrow" aria-hidden="true">→</span>')
            module_name = compact(module.get("module") or module.get("id")) if isinstance(module, dict) else compact(module)
            sequence.append(f'<span class="module-pill">{html_text(module_name)}</span>')
        pipeline_name = compact(pipeline.get("id") or pipeline.get("name"))
        pipelines_html += (
            f'<article class="pipeline"><h3>{html_text(pipeline_name)}</h3>'
            f'<div class="sequence">{"".join(sequence)}</div></article>'
        )

    def routing_items(items: List[Dict[str, Any]]) -> str:
        return "".join(
            f'<li>{html_text(display_text(item["text"], zh))}<code>{html_source(item["source"])}</code></li>'
            for item in items
        )

    resource_rows: List[str] = []
    for resource in model["resources"]:
        state = "missing" if not resource["exists"] else "linked" if resource["linked"] else "unlinked"
        state_label = {
            "missing": "缺失" if zh else "missing",
            "linked": "已链接" if zh else "linked",
            "unlinked": "未链接" if zh else "unlinked",
        }[state]
        sources = ", ".join(source_label(item) for item in resource.get("sources", [])) or "—"
        resource_rows.append(
            "<tr>"
            f'<td class="resource-path">{html_text(resource["path"])}</td>'
            f'<td>{html_text(display_resource_kind(resource["kind"], zh))}</td>'
            f'<td><span class="tag {state}">{html_text(state_label)}</span></td>'
            f'<td><code>{html_text(sources)}</code></td>'
            "</tr>"
        )
    edge_items = "".join(
        f'<li>{html_text(edge["source"])} → {html_text(edge["target"])} · L{edge["line"]}</li>'
        for edge in model["resource_edges"]
    )

    if diagnostics:
        diagnostics_html = "".join(
            '<article class="diagnostic">'
            f'<span class="level level-{html_text(item["level"])}">{html_text(item["level"])}</span>'
            f'<code>{html_text(item["code"])}</code><p>{html_text(display_text(item["message"], zh))}</p></article>'
            for item in diagnostics
        )
    else:
        diagnostics_html = (
            '<article class="diagnostic"><span class="level level-info">OK</span>'
            f'<p>{html_text("未发现结构性问题。" if zh else "No structural diagnostics.")}</p></article>'
        )

    effect_evidence_state = trust.get("verification", {}).get("effect_evidence")
    observed_effect = effect_evidence_state == "observed_bound"
    unbound_observed = effect_evidence_state == "observed_unbound"
    effect_gap_html = (
        '<article class="diagnostic">'
        f'<span class="level level-info">{html_text("证据" if zh else "evidence")}</span>'
        f'<code>observed_effect</code><p>{html_text("已发现真实运行案例或产物，可继续逐项核对预期与实际结果。" if zh else "Observed runtime cases or artifacts are available for expected-versus-actual review.")}</p></article>'
        if observed_effect
        else '<article class="diagnostic">'
        f'<span class="level level-warning">{html_text("缺口" if zh else "gap")}</span>'
        f'<code>effect_evidence_unbound</code><p>{html_text("发现了案例或运行产物，但无法静态确认它们覆盖了哪些内部步骤，因此不会把任一步骤标记为效果已证明。" if zh else "Cases or runtime artifacts exist, but static analysis cannot bind them to individual internal steps, so no step is marked as effect-proven.")}</p></article>'
        if unbound_observed
        else '<article class="diagnostic">'
        f'<span class="level level-warning">{html_text("缺口" if zh else "gap")}</span>'
        f'<code>effect_not_observed</code><p>{html_text("未发现真实任务案例、结果产物或效果回读。当前报告能证明声明与依据完整度，不能证明这个 Skill 实际产出的页面质量。" if zh else "No real task case, result artifact, or effect readback was found. This report proves declaration and support coverage, not the quality of pages the Skill actually produces.")}</p></article>'
    )
    trust_title = (
        "已有步骤级真实效果证据，可继续核对"
        if zh and observed_effect
        else "发现运行产物，但尚未绑定到具体步骤"
        if zh and unbound_observed
        else "可审阅，但真实效果尚未被运行案例证明"
        if zh
        else "Step-bound runtime effect evidence is available for review"
        if observed_effect
        else "Runtime artifacts exist, but are not bound to specific steps"
        if unbound_observed
        else "Reviewable, but real-world effect is not yet proven by runtime cases"
    )
    trust_copy = (
        f"{coverage['workflow_steps']} 个内部步骤都可追溯到源码；"
        f"{coverage.get('steps_with_support', 0)} 个步骤关联模块或资源，"
        f"{coverage.get('steps_with_checks', 0)} 个步骤具有声明的验收规则。"
        if zh
        else
        f"All {coverage['workflow_steps']} internal steps are source-bound; "
        f"{coverage.get('steps_with_support', 0)} have linked modules or resources and "
        f"{coverage.get('steps_with_checks', 0)} have declared acceptance checks."
    )

    html_parts = [
        "<!doctype html>",
        f'<html lang="{"zh-CN" if zh else "en"}" data-theme="light">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f'<meta name="description" content="{html_text(skill.get("description"))}">',
        f'<title>{html_text(skill["name"])} · {html_text("Skill 信任审阅" if zh else "Skill Trust Review")}</title>',
        "<style>", HTML_CSS, "</style>",
        "</head><body>",
        '<header class="hero"><div class="hero-inner">',
        f'<p class="kicker">{html_text("Skill 内部运行 · 证据信任审阅" if zh else "Skill internal runtime · evidence review")}</p>',
        f'<h1>{html_text(skill["name"])}</h1>',
        '<div class="hero-meta">',
        f'<span class="status {status_class}">{html_text(status_label)}</span>',
        f'<span>{html_text("目标版本" if zh else "Target version")}: {html_text(skill.get("version") or "unknown")}</span>',
        f'<span>{html_text("来源" if zh else "Source")}: {html_text(skill["source"])}</span>',
        f'<span>{html_text(model["schema"])}</span>',
        "</div></div></header>",
        '<nav class="review-nav" aria-label="Report sections"><div class="nav-inner">',
        f'<div class="nav-links">{nav_html}</div>',
        '<div class="nav-actions">',
        f'<button type="button" data-download-json data-filename="{html_text(skill["name"])}-logic.json">{html_text(labels["download"])}</button>',
        f'<button type="button" data-print>{html_text(labels["print"])}</button>',
        "</div></div></nav>",
        "<main>",
        '<section id="overview">',
        f'<div class="section-head"><span class="section-index">01</span><div><h2>{html_text(labels["overview"])}</h2><p>{html_text(display_text(skill.get("description"), zh))}</p></div></div>',
        '<article class="trust-verdict">',
        f'<div><span class="eyebrow">{html_text("当前信任结论" if zh else "Current trust verdict")}</span><h2>{html_text(trust_title)}</h2><p>{html_text(trust_copy)}</p></div>',
        f'<div class="trust-boundary"><strong>{html_text("置信度边界" if zh else "Confidence boundary")}</strong><span>{html_text("静态解析可以证明 Skill 声明了什么、依据放在哪里；只有真实任务、产物和回读才能证明运行效果。" if zh else "Static analysis proves what the Skill declares and where its basis lives; only real tasks, artifacts, and readback prove runtime effect.")}</span></div>',
        '</article>',
        f'<div class="stats">{stats_html}</div>',
        '<dl class="meta-strip">',
        f'<div class="meta-card"><dt>{html_text("执行形态" if zh else "Execution mode")}</dt><dd>{html_text("Agent 指令驱动" if zh and trust.get("implementation", {}).get("mode") == "agent_guided" else "Agent-guided" if trust.get("implementation", {}).get("mode") == "agent_guided" else "确定性脚本" if zh else "Deterministic")}</dd></div>',
        f'<div class="meta-card"><dt>{html_text("运行时" if zh else "Runtime")}</dt><dd>{html_text(model["runtime_context"].get("runtime") or "—")}</dd></div>',
        f'<div class="meta-card"><dt>{html_text("引用深度" if zh else "Reference depth")}</dt><dd>{coverage["reference_depth"]}</dd></div>',
        "</dl></section>",
        '<section id="diagrams" class="diagram-section">',
        f'<div class="section-head"><span class="section-index">02</span><div><h2>{html_text("Skill 内部运行与证据" if zh else "Skill internal runtime and evidence")}</h2><p>{html_text("触发匹配属于宿主路由，不进入主图。点击任一步骤，查看具体做法、能力依据、验收规则与尚未证明的效果。" if zh else "Activation matching belongs to host routing and is excluded from the primary graph. Select any step to inspect its method, capability basis, acceptance rules, and unproven effects.")}</p></div></div>',
        f'<div class="step-selector-strip" aria-label="{html_text("内部步骤" if zh else "Internal steps")}">{step_selector_html}</div>',
        '<div class="trust-workspace" data-trust-workspace>',
        f'<div class="diagram-studio" data-diagram-studio data-inspect-label="{html_text("查看步骤证据" if zh else "Inspect step evidence")}" data-loading-label="{html_text("正在渲染 Mermaid…" if zh else "Rendering Mermaid…")}" data-rendering-label="{html_text("正在渲染…" if zh else "Rendering…")}" data-ready-label="{html_text(diagram_ready_label)}" data-partial-label="{html_text("张图已渲染" if zh else "diagrams rendered")}" data-renderer-missing="{html_text("内嵌 Mermaid 渲染器不可用" if zh else "Embedded Mermaid renderer unavailable")}" data-filename-prefix="{html_text(skill["name"])}">',
        '<div class="diagram-studio-bar">',
        f'<span class="diagram-brand">Mermaid {MERMAID_VERSION}</span>',
        f'<div class="diagram-tabs" role="tablist" aria-label="{html_text("Mermaid 图表" if zh else "Mermaid diagrams")}">{diagram_tabs_html}</div>',
        '<div class="diagram-tools">',
        f'<button type="button" class="diagram-tool" data-fit-diagram>{html_text("适配" if zh else "Fit")}</button>',
        f'<button type="button" class="diagram-tool square" data-zoom-out aria-label="{html_text("缩小图表" if zh else "Zoom out")}" title="{html_text("缩小" if zh else "Zoom out")}">−</button>',
        '<span class="diagram-zoom-value" data-diagram-zoom-value>100%</span>',
        f'<button type="button" class="diagram-tool square" data-zoom-in aria-label="{html_text("放大图表" if zh else "Zoom in")}" title="{html_text("放大" if zh else "Zoom in")}">+</button>',
        f'<button type="button" class="diagram-tool" data-toggle-source aria-pressed="false" data-show-label="{html_text("显示源码" if zh else "Show source")}" data-hide-label="{html_text("隐藏源码" if zh else "Hide source")}">{html_text("显示源码" if zh else "Show source")}</button>',
        f'<button type="button" class="diagram-tool" data-export-svg>{html_text("导出 SVG" if zh else "Export SVG")}</button>',
        '</div></div>',
        '<div class="diagram-workspace">',
        f'<div class="diagram-canvas"><div class="diagram-preview" id="diagram-preview" role="tabpanel" aria-live="polite" data-diagram-preview><div class="diagram-loading">{html_text("正在渲染 Mermaid…" if zh else "Rendering Mermaid…")}</div></div></div>',
        '<aside class="diagram-source-panel" data-diagram-source-panel hidden>',
        f'<div class="diagram-source-head"><span data-diagram-source-name>{html_text(diagram_specs[0][1])} · Mermaid</span><button type="button" class="diagram-tool" data-copy-diagram-source data-copied-label="{html_text(labels["copied"])}">{html_text("复制源码" if zh else "Copy source")}</button></div>',
        '<pre class="diagram-source" data-diagram-source></pre>',
        f'<div class="diagram-source-foot"><span>{html_text("只读 · 与生成模型同步" if zh else "Read only · synchronized with model")}</span><span class="diagram-render-status" data-diagram-render-status>{html_text("等待渲染" if zh else "Waiting")}</span></div>',
        '</aside></div></div>',
        f'<aside class="step-inspector" data-step-inspector aria-live="polite">{step_inspector_html}</aside>',
        '</div></section>',
        '<section id="flow">',
        f'<div class="section-head"><span class="section-index">03</span><div><h2>{html_text("步骤源码索引" if zh else "Step source index")}</h2><p>{html_text("用于连续浏览全部步骤；日常审阅优先直接点击运行图节点。" if zh else "Use this for sequential browsing; prefer selecting runtime nodes during normal review.")}</p></div></div>',
        f'<details class="evidence-disclosure"><summary>{html_text(flow_evidence_label)}</summary><div class="details-body"><ol class="flow-list">{flow_html}</ol></div></details></section>',
    ]
    if pipelines_html:
        html_parts.extend([
            '<section id="kit">',
            f'<div class="section-head"><span class="section-index">04</span><div><h2>{html_text(labels["kit"])}</h2><p>{html_text("每行是一条可执行命名管线；重复模块表示复审或回归阶段。" if zh else "Each row is one executable pipeline; repeated modules indicate review or regression stages.")}</p></div></div>',
            f'<details class="evidence-disclosure"><summary>{html_text(kit_detail_label)}</summary><div class="details-body"><div class="pipeline-list">{pipelines_html}</div></div></details></section>',
        ])
    html_parts.extend([
        '<section id="routing">',
        f'<div class="section-head"><span class="section-index">05</span><div><h2>{html_text(labels["routing"])}</h2><p>{html_text("这部分只帮助宿主判断何时调用 Skill，不属于 Skill 启动后的内部运行逻辑。" if zh else "This section only helps the host decide when to invoke the Skill; it is not part of the Skill internal runtime after activation.")}</p></div></div>',
        f'<details class="evidence-disclosure"><summary>{html_text("查看外部触发与排除条件" if zh else "View external activation and exclusion rules")}</summary><div class="details-body"><p class="external-boundary-note">{html_text("已从主运行图移除，避免把路由逻辑误当成 Skill 能力。" if zh else "Removed from the primary runtime graph so host routing is not mistaken for Skill capability.")}</p><div class="routing-grid">',
        f'<article class="panel route-panel"><h3>{html_text("应触发" if zh else "Activate")}</h3><ul>{routing_items(model["routing"]["activate"])}</ul></article>',
        f'<article class="panel route-panel out"><h3>{html_text("不应触发" if zh else "Do not activate")}</h3><ul>{routing_items(model["routing"]["do_not_activate"])}</ul></article>',
        "</div></div></details></section>",
        '<section id="resources">',
        f'<div class="section-head"><span class="section-index">06</span><div><h2>{html_text(labels["resources"])}</h2><p>{html_text("区分运行链已链接资源、包内未链接文件和真实缺失。" if zh else "Distinguish linked runtime resources, unlinked packaged files, and real missing files.")}</p></div></div>',
        f'<details class="evidence-disclosure"><summary>{html_text(resource_detail_label)}</summary><div class="details-body"><div class="table-wrap"><table><thead><tr>',
        f'<th>{html_text("路径" if zh else "Path")}</th><th>{html_text("类型" if zh else "Kind")}</th><th>{html_text("状态" if zh else "State")}</th><th>{html_text("引用来源" if zh else "Declared at")}</th>',
        f'</tr></thead><tbody>{"".join(resource_rows)}</tbody></table></div>',
        '<details><summary>' + html_text("查看资源边" if zh else "View resource edges") + '</summary><div class="details-body">',
        f'<ol class="edge-list">{edge_items}</ol></div></details></div></details></section>',
        '<section id="diagnostics">',
        f'<div class="section-head"><span class="section-index">07</span><div><h2>{html_text(labels["diagnostics"])}</h2><p>{html_text("优先暴露影响信任的效果证据缺口，再列出结构性诊断。" if zh else "Effect-evidence gaps that affect trust come first, followed by structural diagnostics.")}</p></div></div>',
        f'<div class="diagnostics">{effect_gap_html}{diagnostics_html}</div></section>',
        '<section id="artifacts">',
        f'<div class="section-head"><span class="section-index">08</span><div><h2>{html_text(labels["artifacts"])}</h2><p>{html_text("Mermaid 与 JSON 都内嵌在本文件，可复制或下载继续加工。" if zh else "Mermaid and JSON are embedded for copying, downloading, and downstream use.")}</p></div></div>',
        '<details><summary>' + html_text("运行流程 Mermaid" if zh else "Runtime Mermaid") + '</summary><div class="details-body">',
        f'<div class="code-tools"><button type="button" data-copy-target="#runtime-mermaid" data-copied-label="{html_text(labels["copied"])}">{html_text(labels["copy"])}</button></div>',
        f'<pre id="runtime-mermaid">{html_lib.escape(runtime_mermaid)}</pre></div></details>',
        '<details><summary>' + html_text("资源关系 Mermaid" if zh else "Resource Mermaid") + '</summary><div class="details-body">',
        f'<div class="code-tools"><button type="button" data-copy-target="#resource-mermaid" data-copied-label="{html_text(labels["copied"])}">{html_text(labels["copy"])}</button></div>',
        f'<pre id="resource-mermaid">{html_lib.escape(resource_mermaid)}</pre></div></details>',
    ])
    if kit_mermaid:
        html_parts.extend([
            '<details><summary>' + html_text("Kit 管线 Mermaid" if zh else "Kit Mermaid") + '</summary><div class="details-body">',
            f'<div class="code-tools"><button type="button" data-copy-target="#kit-mermaid" data-copied-label="{html_text(labels["copied"])}">{html_text(labels["copy"])}</button></div>',
            f'<pre id="kit-mermaid">{html_lib.escape(kit_mermaid)}</pre></div></details>',
        ])
    html_parts.extend([
        '<details><summary>' + html_text("完整 JSON 模型" if zh else "Complete JSON model") + '</summary><div class="details-body">',
        f'<div class="code-tools"><button type="button" data-copy-target="#json-preview" data-copied-label="{html_text(labels["copied"])}">{html_text(labels["copy"])}</button></div>',
        f'<pre id="json-preview">{html_lib.escape(model_json)}</pre></div></details>',
        f'<p class="honesty-note">{html_text("本页面区分三件事：源码声明了什么、哪些模块和资源支撑它、是否存在真实运行效果。前两项来自静态解析；没有案例和产物时，第三项明确保持为未证明。" if zh else "This page separates what the source declares, which modules and resources support it, and whether real runtime effect has been observed. The first two come from static analysis; without cases and artifacts, the third remains explicitly unproven.")}</p>',
        "</section></main>",
        f'<footer>{html_text(skill["name"])} · {html_text(model["schema"])} · Mermaid {MERMAID_VERSION} · {html_text("离线单文件信任审阅" if zh else "offline single-file trust review")}</footer>',
        f'<script id="logic-model" type="application/json">{embedded_json}</script>',
        f'<script data-vendor="mermaid@{MERMAID_VERSION}">{mermaid_bundle}</script>',
        "<script>", HTML_JS, "</script>",
        "</body></html>",
    ])
    return "\n".join(html_parts)


BRIEF_HTML_CSS = r"""
:root {
  color-scheme: light;
  --paper: #f6f6f2;
  --surface: #ffffff;
  --ink: #171916;
  --muted: #656a63;
  --line: #d9ddd6;
  --soft-line: #e9ebe7;
  --accent: #176b57;
  --accent-soft: #e7f0ec;
  --warn: #8a5a16;
  --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  --sans: Inter, "SF Pro Text", "PingFang SC", "Noto Sans CJK SC", system-ui, sans-serif;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  color: var(--ink);
  background: var(--paper);
  font-family: var(--sans);
  line-height: 1.65;
  -webkit-font-smoothing: antialiased;
}
a { color: inherit; }
code, pre { font-family: var(--mono); }
[hidden] { display: none !important; }
.page {
  width: min(1080px, calc(100% - 40px));
  margin: 0 auto;
}
.hero { padding: 72px 0 58px; border-bottom: 1px solid var(--line); }
.meta-line, .eyebrow {
  color: var(--muted);
  font: 600 11px/1.4 var(--mono);
  letter-spacing: .08em;
  text-transform: uppercase;
}
.meta-line { display: flex; flex-wrap: wrap; gap: 10px 20px; margin-bottom: 38px; }
.hero h1 {
  max-width: 920px;
  margin: 12px 0 18px;
  font-size: clamp(40px, 6vw, 72px);
  line-height: 1.06;
  letter-spacing: -.045em;
  font-weight: 680;
}
.hero-lede {
  max-width: 780px;
  margin: 0;
  color: #454a44;
  font-size: clamp(18px, 2vw, 23px);
  line-height: 1.55;
}
.fit-signal {
  display: grid;
  grid-template-columns: 132px 1fr;
  gap: 22px;
  margin-top: 40px;
  padding: 22px 0 0;
  border-top: 2px solid var(--accent);
}
.fit-signal strong { color: var(--accent); font-size: 14px; }
.fit-signal p { margin: 0; font-size: 17px; }
main section { padding: 58px 0; border-bottom: 1px solid var(--line); }
.section-label {
  display: grid;
  grid-template-columns: 132px minmax(0, 1fr);
  gap: 22px;
  margin-bottom: 34px;
}
.section-label h2 {
  margin: -5px 0 0;
  max-width: 780px;
  font-size: clamp(27px, 3.2vw, 40px);
  line-height: 1.18;
  letter-spacing: -.03em;
}
.three-part {
  display: grid;
  grid-template-columns: 1fr 64px 1fr 64px 1fr;
  align-items: start;
  border-top: 1px solid var(--ink);
  border-bottom: 1px solid var(--ink);
}
.three-part article { min-height: 250px; padding: 28px 0; }
.three-part h3 { margin: 0 0 18px; font-size: 13px; color: var(--accent); }
.three-part ul, .outcome-list, .fit-list { margin: 0; padding: 0; list-style: none; }
.three-part li, .outcome-list li, .fit-list li { position: relative; padding: 8px 0 8px 18px; }
.three-part li::before, .outcome-list li::before, .fit-list li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 19px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--accent);
}
.arrow { align-self: center; text-align: center; color: var(--muted); font-size: 24px; }
.logic-intro { max-width: 780px; margin: -12px 0 36px 154px; color: var(--muted); }
.logic-line {
  margin: 0;
  padding: 0;
  list-style: none;
  border-top: 1px solid var(--ink);
}
.logic-line li {
  display: grid;
  grid-template-columns: 48px 190px minmax(0, 1fr) minmax(260px, .9fr);
  gap: 24px;
  align-items: start;
  padding: 24px 0;
  border-bottom: 1px solid var(--line);
}
.logic-line .index { color: var(--accent); font: 600 12px var(--mono); }
.logic-line h3 { margin: -4px 0 0; font-size: 18px; line-height: 1.4; }
.stage-cell span { display: block; margin-bottom: 7px; color: var(--muted); font: 10px var(--mono); letter-spacing: .06em; }
.stage-cell p { margin: 0; color: #424741; font-size: 13px; line-height: 1.65; }
.stage-basis p { color: var(--muted); }
.stage-basis code { display: block; margin-top: 10px; color: var(--accent); font-size: 10px; overflow-wrap: anywhere; }
.decision {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 64px;
}
.decision h3 { margin: 0 0 18px; font-size: 20px; }
.decision p { color: var(--muted); }
.not-fit { margin-top: 30px; padding-top: 22px; border-top: 1px solid var(--line); }
.outcome {
  display: grid;
  grid-template-columns: 1.05fr .95fr;
  gap: 70px;
  align-items: start;
}
.outcome-copy { margin: 0; font-size: 20px; line-height: 1.6; }
.trust-band {
  padding: 28px 0;
  border-top: 2px solid var(--ink);
  border-bottom: 1px solid var(--ink);
}
.trust-band h3 { margin: 0 0 12px; font-size: 23px; }
.trust-band p { max-width: 860px; margin: 0; color: var(--muted); }
.metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  margin-top: 30px;
  border-top: 1px solid var(--line);
}
.metric { padding: 20px 16px 0 0; }
.metric strong { display: block; font-size: 28px; letter-spacing: -.03em; }
.metric span { color: var(--muted); font-size: 12px; }
.technical-section { padding-bottom: 80px; }
.technical-evidence > summary {
  cursor: pointer;
  list-style: none;
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: 22px 0;
  border-top: 1px solid var(--ink);
  border-bottom: 1px solid var(--ink);
  font-weight: 650;
}
.technical-evidence > summary::-webkit-details-marker { display: none; }
.technical-evidence > summary::after { content: "+"; color: var(--accent); }
.technical-evidence[open] > summary::after { content: "−"; }
.technical-body { padding: 40px 0 0; }
.technical-note { max-width: 760px; margin: 0 0 38px; color: var(--muted); }
.mermaid-figure { margin: 0 0 46px; }
.mermaid-figure figcaption { margin-bottom: 14px; font-weight: 650; }
.mermaid-host {
  min-height: 180px;
  padding: 22px;
  overflow: auto;
  background: var(--surface);
  border: 1px solid var(--line);
}
.mermaid-host svg { display: block; width: 100%; height: auto; min-width: 680px; margin: 0 auto; }
.render-note { color: var(--muted); font-size: 13px; }
.render-error { color: #a33b2b; white-space: pre-wrap; }
.evidence-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 28px; margin-top: 36px; }
.evidence-grid h3 { margin-top: 0; }
.evidence-grid ul { padding-left: 20px; }
.evidence-grid li { margin: 8px 0; color: var(--muted); }
.evidence-grid code { font-size: 11px; color: var(--ink); overflow-wrap: anywhere; }
.raw-details { margin-top: 24px; border-top: 1px solid var(--line); }
.raw-details summary { cursor: pointer; padding: 16px 0; font-weight: 600; }
pre {
  max-height: 520px;
  margin: 0;
  padding: 18px;
  overflow: auto;
  color: #e9eee9;
  background: #1c211e;
  font-size: 11px;
  line-height: 1.55;
  white-space: pre;
}
footer { padding: 28px 0 54px; color: var(--muted); font-size: 11px; font-family: var(--mono); }
@media (max-width: 820px) {
  .page { width: min(100% - 28px, 680px); }
  .hero { padding: 44px 0 40px; }
  .meta-line { margin-bottom: 28px; }
  .fit-signal, .section-label { grid-template-columns: 1fr; gap: 10px; }
  .logic-intro { margin-left: 0; }
  .three-part { grid-template-columns: 1fr; }
  .three-part article { min-height: 0; padding: 24px 0; }
  .arrow { transform: rotate(90deg); padding: 2px 0; }
  .logic-line li { grid-template-columns: 34px 1fr; gap: 8px 14px; padding: 22px 0; }
  .logic-line h3 { margin: -5px 0 8px; }
  .logic-line .stage-cell { grid-column: 2; }
  .decision, .outcome, .evidence-grid { grid-template-columns: 1fr; gap: 34px; }
  .metrics { grid-template-columns: 1fr 1fr; }
  .mermaid-host { padding: 12px; }
  .mermaid-host svg { min-width: 600px; }
}
@media print {
  body { background: #fff; }
  .page { width: 100%; }
  .technical-evidence > summary { display: none; }
  .technical-evidence > .technical-body { display: block !important; }
}
"""


BRIEF_HTML_JS = r"""
(async () => {
  const hosts = [...document.querySelectorAll('[data-mermaid-host]')];
  if (!hosts.length) return;
  if (!window.mermaid) {
    hosts.forEach((host) => { host.innerHTML = '<p class="render-error">内嵌 Mermaid 渲染器不可用。</p>'; });
    return;
  }
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: 'strict',
    theme: 'base',
    themeVariables: {
      background: '#ffffff',
      primaryColor: '#e7f0ec',
      primaryTextColor: '#171916',
      primaryBorderColor: '#176b57',
      lineColor: '#737a72',
      secondaryColor: '#f6f6f2',
      tertiaryColor: '#ffffff',
      fontFamily: 'Inter, PingFang SC, system-ui, sans-serif'
    },
    flowchart: { htmlLabels: false, curve: 'basis' }
  });
  for (const [index, host] of hosts.entries()) {
    const source = document.querySelector(host.dataset.source);
    if (!source) continue;
    try {
      const result = await mermaid.render(`skill-logic-${index + 1}`, source.value.trim());
      host.innerHTML = result.svg;
      const svg = host.querySelector('svg');
      if (svg) {
        svg.removeAttribute('height');
        svg.setAttribute('role', 'img');
        svg.setAttribute('aria-label', host.dataset.label || 'Mermaid diagram');
      }
    } catch (error) {
      host.innerHTML = `<p class="render-error">Mermaid 渲染失败：${String(error)}</p>`;
    }
  }
})();
"""


def build_review_brief(model: Dict[str, Any], zh: bool) -> Dict[str, Any]:
    """Build a linear, scenario-first explanation without changing extracted facts."""
    skill = model["skill"]
    name = compact(skill.get("name"))
    kit = model.get("kit", {})
    modules = {
        compact(item.get("id")): item
        for item in kit.get("modules", [])
        if isinstance(item, dict)
    }
    pipelines = [item for item in kit.get("pipelines", []) if isinstance(item, dict)]
    preferred = next(
        (item for item in pipelines if compact(item.get("id") or item.get("name")) == "optimize"),
        pipelines[0] if pipelines else None,
    )

    if name == "lov-oh-my-landingpage" and zh:
        stage_specs = [
            ("SKILL.md · Step 0", "确认真实页面", "用户请求与当前项目", "找到真实路由、代码、产品行为和现有素材", "以实际运行面为准，不把截图、简报或单个组件误当成完整页面"),
            ("kit.yaml · optimize", "选择 optimize 管线", "已确认的现有首页", "确定先审、再重建、再复审的执行顺序", "新建、整体优化、重塑品牌、只改文案、只改素材和只读审计分别走不同管线"),
            ("SKILL.md · Step 2", "建立事实账本", "品牌文档、产品行为、代码、公开声明与用户证据", "分成内部上下文、可公开声明、已验证证据、待补证据", "优先级依次是批准的品牌与产品事实、真实行为与线上资产、已验证案例与指标、明确标注的推断；证据缺口不得变成公开声明"),
            ("landing-review", "先审当前页面", "现有页面与事实账本", "定位问题究竟来自记忆点、含义、交互还是证据", "审阅真实页面而非抽象评分，并把根因交给后续模块"),
            ("landing-brand", "定品牌内核", "已核实的产品事实与审阅根因", "形成一条 Brand Spine，决定什么该说、该保留、该放弃", "品牌主张必须具体、真实、可追溯；文案、视觉与交互表达同一个观点"),
            ("landing-strategy", "把内核讲成故事", "Brand Spine 与公开声明边界", "得到用户能按顺序理解的首页叙事、证明与 CTA", "每个公开声明都要配证据或行动，不把原始 brief 直接粘进页面"),
            ("landing-art-direction", "建立专属视觉世界", "同一条品牌主轴与真实素材", "让字体、构图、媒体和交互形成可识别的记忆点", "先说明风格为何适合本产品，并排除至少两个看似可行但不合适的方向"),
            ("landing-builder", "写进真实页面", "已批准的叙事与视觉规则", "落到真实路由、组件、内容、响应式与 CTA", "实现必须保持真实产品行为、已有资产和无障碍边界，而不是另做一张概念稿"),
            ("landing-review · Step 7–8", "复审并报告结果", "改完后的可运行页面", "回读记忆点、含义、交互、证据与限制，并说明实际改了什么", "浏览器、响应式和关键交互都要真实检查；未验证效果继续明确标注"),
        ]
        stages = [
            {
                "module": module_id,
                "title": title,
                "input": input_text,
                "output": output_text,
                "basis": basis,
            }
            for module_id, title, input_text, output_text, basis in stage_specs
        ]
        return {
            "scenario_title": "首页能用，却像任何一家同行时，用它。",
            "scenario_lede": "当问题同时横跨定位、叙事、视觉和真实代码，继续零散改文案、配色或模块，只会让各层更不一致。",
            "fit_signal": "你需要的不是一份改版建议，而是让同一条品牌主轴从事实一路落到可运行页面。",
            "summary_title": "它把跨层混乱收束为一条从事实到页面的闭环。",
            "runtime_title": "先审，再定，再做，最后回到真实页面验。",
            "outcome_title": "不是一张审计卡片，而是一组能继续交付和验收的结果。",
            "outcome_copy": "它承诺的是从品牌判断到真实页面的连续交付；每个后续决定都能回到同一个事实基础。",
            "before": [
                "访客看到了功能，却说不清这个产品是谁",
                "文案、视觉和真实能力各说各话",
                "局部越改越精致，整体仍然像通用模板",
            ],
            "transform": [
                "先确认真实页面并建立事实账本",
                "用一条 Brand Spine 统领叙事、视觉和实现",
                "把决定落实到代码后再回到真实页面复审",
            ],
            "after": [
                "一句可复述、且有事实依据的品牌主张",
                "一套围绕同一观点的叙事与视觉系统",
                "已经落到真实页面的内容、组件、媒体和 CTA",
            ],
            "stages": stages,
            "pipeline_id": "optimize",
            "why": "它不是把设计、文案和前端简单串起来，而是让每一层都服从同一个已核实的品牌判断。这个耦合问题正是单独改 CSS、重写 Hero 或换一套模板解决不了的。",
            "fit_conditions": [
                "产品已经存在，但首页无法让人迅速理解和记住",
                "问题跨越定位、信息层级、视觉语言与实现，而不是一个局部缺陷",
                "你愿意以真实产品事实为准，并接受最终页面回读",
            ],
            "not_fit": "如果只是改一个按钮、修后端、部署、换 Logo，或已经有明确品牌系统只需照稿实现，这个 Skill 太重。",
            "outcomes": [
                "Brand Spine 与可公开声明的证据层级",
                "首页叙事顺序、文案主轴与 CTA 逻辑",
                "一个产品专属的视觉世界与记忆点",
                "真实代码中的页面实现，而不是停在建议稿",
                "浏览器回读、响应式检查与最终验收结论",
            ],
        }

    trigger = next(iter(model.get("routing", {}).get("activate", [])), {}).get("text", "")
    scenario = display_text(trigger, zh) or display_text(skill.get("description"), zh)
    if preferred:
        module_ids = [compact(item) for item in preferred.get("steps", [])]
        stages = []
        for module_id in module_ids[:6]:
            module = modules.get(module_id, {})
            title = compact(module.get("skill")) or module_id
            stages.append({
                "module": module_id,
                "source": compact(module.get("source")),
                "title": display_text(title, zh),
                "input": "承接上一步已确认的信息" if zh else "Uses the prior confirmed state",
                "output": "形成下一阶段可用的结果" if zh else "Produces the next reviewable state",
                "basis": display_text(module.get("description"), zh) or ("使用模块声明的规则" if zh else "Uses the module's declared rules"),
            })
    else:
        stages = [
            {
                "module": compact(step.get("id")),
                "source": source_label(step.get("source", {})),
                "title": display_text(step.get("title"), zh),
                "input": "当前任务上下文" if zh else "Current task context",
                "output": display_text(step.get("summary"), zh),
                "basis": "以对应源码步骤为准" if zh else "Grounded in the corresponding source step",
            }
            for step in model.get("workflow", {}).get("steps", [])[:6]
        ]
    return {
        "scenario_title": (f"当任务是“{scenario}”时，用它。" if zh else f"Use it when the task is: {scenario}"),
        "scenario_lede": display_text(skill.get("description"), zh),
        "fit_signal": "它把分散的指令组织成一条可追溯、可验收的内部路径。" if zh else "It turns dispersed instructions into one traceable, reviewable path.",
        "summary_title": "它把输入、判断、动作与验收收束为一条连续路径。" if zh else "It connects inputs, decisions, actions, and checks in one path.",
        "runtime_title": "所有关键阶段一次展开，不需要逐节点探索。" if zh else "Every key stage is visible without node exploration.",
        "outcome_title": "拿到可继续使用、也能追溯依据的结果。" if zh else "Get a reusable result with traceable grounds.",
        "outcome_copy": "它承诺的是声明工作流中的连续交付，并明确区分源码依据与尚未验证的效果。" if zh else "The contract connects declared workflow outputs while separating source evidence from unproven effect.",
        "before": ["输入与目标分散", "判断依据不透明", "交付结果难以验收"] if zh else ["Scattered inputs", "Opaque decisions", "Hard-to-review output"],
        "transform": ["明确输入", "按顺序转化", "对照规则验收"] if zh else ["Resolve input", "Transform in sequence", "Verify against rules"],
        "after": ["运行路径可解释", "关键决定有依据", "结果与缺口可区分"] if zh else ["Explainable path", "Grounded decisions", "Visible outcomes and gaps"],
        "stages": stages,
        "pipeline_id": compact(preferred.get("id") or preferred.get("name")) if preferred else "workflow",
        "why": "它的价值在于把这个 Skill 的多阶段判断保持在同一条上下文中。" if zh else "Its value is keeping multi-stage decisions in one context.",
        "fit_conditions": [scenario] if scenario else ["任务与 Skill 的声明范围一致"],
        "not_fit": "如果只需要一个更窄、更确定的原子操作，应改用对应的专用 Skill。" if zh else "Use a narrower atomic Skill for a single deterministic operation.",
        "outcomes": ["声明的工作流结果", "来源与验收依据", "明确标出的未证明部分"] if zh else ["Declared workflow output", "Sources and checks", "Explicit unproven gaps"],
    }


def render_html(model: Dict[str, Any], direction: str, language: str) -> str:
    """Render a self-contained, linear trust brief with Mermaid as secondary evidence."""
    zh = choose_language(model, language)
    skill = model["skill"]
    coverage = model["coverage"]
    trust = model.get("trust", {})
    brief = build_review_brief(model, zh)
    diagnostics = model.get("diagnostics", [])
    errors = sum(item.get("level") == "error" for item in diagnostics)
    warnings = sum(item.get("level") == "warning" for item in diagnostics)
    status = (
        f"{errors} 个结构错误" if zh and errors else
        f"{warnings} 个结构警告" if zh and warnings else
        "结构检查通过" if zh else
        f"{errors} structural errors" if errors else
        f"{warnings} structural warnings" if warnings else
        "Structure validated"
    )
    runtime_mermaid = render_runtime_mermaid(model, direction, zh)
    resource_mermaid = render_resource_mermaid(model, zh)
    kit_mermaid = render_kit_mermaid(model, zh)
    diagrams = [
        ("runtime", "内部运行图" if zh else "Internal runtime", runtime_mermaid),
        ("resources", "能力与资源关系" if zh else "Capability and resources", resource_mermaid),
    ]
    if kit_mermaid:
        diagrams.append(("kit", "Kit 管线" if zh else "Kit pipelines", kit_mermaid))

    model_json = json.dumps(model, ensure_ascii=False, indent=2, sort_keys=True)
    embedded_json = model_json.replace("</", "<\\/")
    mermaid_bundle = load_mermaid_bundle()

    def list_items(items: Sequence[str]) -> str:
        return "".join(f"<li>{html_text(item)}</li>" for item in items)

    stages_html = "".join(
        '<li>'
        f'<span class="index">{index:02d}</span>'
        f'<h3>{html_text(stage["title"])}</h3>'
        f'<div class="stage-cell"><span>{html_text("输入 → 输出" if zh else "Input → output")}</span><p>{html_text(stage["input"])} → {html_text(stage["output"])}</p></div>'
        f'<div class="stage-cell stage-basis"><span>{html_text("判断依据" if zh else "Basis")}</span><p>{html_text(stage.get("basis"))}</p><code>{html_text(stage.get("module") or stage.get("source") or "workflow")}</code></div>'
        '</li>'
        for index, stage in enumerate(brief["stages"], start=1)
    )
    metrics = [
        (f'{trust.get("traceability", {}).get("source_bound_steps", 0)}/{trust.get("traceability", {}).get("total_steps", 0)}', "步骤可回到源码" if zh else "steps source-bound"),
        (coverage.get("steps_with_support", 0), "步骤有模块或资源支撑" if zh else "steps supported"),
        (trust.get("support", {}).get("module_quality_gates", 0), "模块质量门" if zh else "module quality gates"),
        (coverage.get("observed_artifacts", 0), "真实任务案例" if zh else "observed task cases"),
    ]
    metrics_html = "".join(
        f'<div class="metric"><strong>{html_text(str(value))}</strong><span>{html_text(label)}</span></div>'
        for value, label in metrics
    )
    observed = trust.get("verification", {}).get("effect_evidence") == "observed_bound"
    trust_title = (
        "运行效果已有步骤级证据" if zh and observed else
        "值得信的是逻辑完整度，不是已证明的页面质量" if zh else
        "Step-bound runtime effect is available" if observed else
        "Trust the declared logic coverage, not an unproven real-world effect"
    )
    trust_copy = (
        f"{coverage['workflow_steps']} 个内部步骤均有源码位置；"
        f"{coverage.get('steps_with_support', 0)} 个步骤有模块或资源支撑，"
        f"共提取 {trust.get('support', {}).get('module_quality_gates', 0)} 条模块质量门。"
        + ("但当前没有与步骤绑定的真实任务和产物回读，所以不能据此断言最终页面一定优秀。" if not observed else "真实案例可继续用于预期与实际结果核对。")
        if zh else
        "The report distinguishes source declarations, supporting capability, checks, and observed outcomes."
    )
    diagnostic_items = "".join(
        f'<li><code>{html_text(item.get("code"))}</code> · {html_text(display_text(item.get("message"), zh))}</li>'
        for item in diagnostics
    ) or f'<li>{html_text("未发现结构性诊断。" if zh else "No structural diagnostics.")}</li>'
    routing_items = "".join(
        f'<li>{html_text(display_text(item.get("text"), zh))} <code>{html_source(item.get("source", {}))}</code></li>'
        for item in model.get("routing", {}).get("activate", []) + model.get("routing", {}).get("do_not_activate", [])
    )
    resource_items = "".join(
        f'<li><code>{html_text(item.get("path"))}</code> · {html_text("存在" if zh and item.get("exists") else "缺失" if zh else "present" if item.get("exists") else "missing")}</li>'
        for item in model.get("resources", [])
    )
    diagrams_html = "".join(
        f'<figure class="mermaid-figure"><figcaption>{html_text(title)}</figcaption>'
        f'<div class="mermaid-host" data-mermaid-host data-source="#{key}-mermaid" data-label="{html_text(title)}"><p class="render-note">{html_text("正在渲染 Mermaid…" if zh else "Rendering Mermaid…")}</p></div>'
        f'<textarea class="mermaid-definition" id="{key}-mermaid" hidden>{html_lib.escape(source)}</textarea></figure>'
        for key, title, source in diagrams
    )
    raw_mermaid = "\n\n".join(f"%% {title}\n{source}" for _, title, source in diagrams)
    stage_count = len(brief["stages"])
    stage_intro = (
        f"{stage_count} 个阶段一次展开，不需要点击节点猜下一步。"
        if zh
        else f"All {stage_count} stages are visible without node exploration."
    )

    html_parts = [
        "<!doctype html>",
        f'<html lang="{"zh-CN" if zh else "en"}">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f'<meta name="description" content="{html_text(skill.get("description"))}">',
        f'<title>{html_text(skill["name"])} · {html_text("什么时候该用" if zh else "When to use it")}</title>',
        "<style>", BRIEF_HTML_CSS, "</style>",
        "</head><body>",
        '<div class="page">',
        '<header class="hero">',
        '<div class="meta-line">',
        f'<span>{html_text(skill["name"])}</span><span>v{html_text(skill.get("version") or "unknown")}</span>',
        f'<span>{html_text(status)}</span><span>{html_text(model["schema"])}</span>',
        '</div>',
        f'<p class="eyebrow">{html_text("什么时候该用" if zh else "When to use")}</p>',
        f'<h1>{html_text(brief["scenario_title"])}</h1>',
        f'<p class="hero-lede">{html_text(brief["scenario_lede"])}</p>',
        '<div class="fit-signal">',
        f'<strong>{html_text("判断信号" if zh else "Decision signal")}</strong>',
        f'<p>{html_text(brief["fit_signal"])}</p>',
        '</div></header>',
        '<main>',
        '<section aria-labelledby="one-look-title">',
        f'<div class="section-label"><span class="eyebrow">01 · {html_text("一句话看懂" if zh else "At a glance")}</span><h2 id="one-look-title">{html_text(brief["summary_title"])}</h2></div>',
        '<div class="three-part">',
        f'<article><h3>{html_text("使用前" if zh else "Before")}</h3><ul>{list_items(brief["before"])}</ul></article>',
        '<div class="arrow" aria-hidden="true">→</div>',
        f'<article><h3>{html_text("Skill 做的事" if zh else "Transformation")}</h3><ul>{list_items(brief["transform"])}</ul></article>',
        '<div class="arrow" aria-hidden="true">→</div>',
        f'<article><h3>{html_text("使用后" if zh else "After")}</h3><ul>{list_items(brief["after"])}</ul></article>',
        '</div></section>',
        '<section aria-labelledby="logic-title">',
        f'<div class="section-label"><span class="eyebrow">02 · {html_text("真实运行逻辑" if zh else "Runtime logic")}</span><h2 id="logic-title">{html_text(brief["runtime_title"])}</h2></div>',
        f'<p class="logic-intro">{html_text("本场景走" if zh else "This scenario uses")} <code>{html_text(brief["pipeline_id"])}</code>。{html_text(stage_intro)}</p>',
        f'<ol class="logic-line">{stages_html}</ol>',
        '</section>',
        '<section aria-labelledby="decision-title">',
        f'<div class="section-label"><span class="eyebrow">03 · {html_text("为什么是它" if zh else "Why this Skill")}</span><h2 id="decision-title">{html_text("只有跨层问题，才值得启动这条完整链。" if zh else "Use the full chain only for a cross-layer problem.")}</h2></div>',
        '<div class="decision">',
        f'<div><h3>{html_text("它不可替代的部分" if zh else "What it uniquely coordinates")}</h3><p>{html_text(brief["why"])}</p></div>',
        f'<div><h3>{html_text("满足这些条件再用" if zh else "Use when")}</h3><ul class="fit-list">{list_items(brief["fit_conditions"])}</ul></div>',
        '</div>',
        f'<p class="not-fit"><strong>{html_text("不要用在：" if zh else "Do not use for: ")}</strong>{html_text(brief["not_fit"])}</p>',
        '</section>',
        '<section aria-labelledby="outcome-title">',
        f'<div class="section-label"><span class="eyebrow">04 · {html_text("你会拿到什么" if zh else "Outcome")}</span><h2 id="outcome-title">{html_text(brief["outcome_title"])}</h2></div>',
        '<div class="outcome">',
        f'<p class="outcome-copy">{html_text(brief["outcome_copy"])}</p>',
        f'<ul class="outcome-list">{list_items(brief["outcomes"])}</ul>',
        '</div></section>',
        '<section aria-labelledby="trust-title">',
        f'<div class="section-label"><span class="eyebrow">05 · {html_text("可信边界" if zh else "Trust boundary")}</span><h2 id="trust-title">{html_text("能确认它想怎么做，也要诚实说明还没证明什么。" if zh else "Know what is declared and what remains unproven.")}</h2></div>',
        '<div class="trust-band">',
        f'<h3>{html_text(trust_title)}</h3><p>{html_text(trust_copy)}</p>',
        f'<div class="metrics">{metrics_html}</div>',
        '</div></section>',
        '<section class="technical-section" aria-labelledby="technical-title">',
        f'<div class="section-label"><span class="eyebrow">06 · {html_text("复核材料" if zh else "Evidence")}</span><h2 id="technical-title">{html_text("结论看完后，再检查 Mermaid、源码与模型。" if zh else "Inspect Mermaid, sources, and model after the conclusion.")}</h2></div>',
        '<details class="technical-evidence">',
        f'<summary>{html_text("展开技术证据" if zh else "Open technical evidence")}<span>{len(diagrams)} Mermaid · {len(model.get("resources", []))} {html_text("个资源" if zh else "resources")}</span></summary>',
        '<div class="technical-body">',
        f'<p class="technical-note">{html_text("这里是复核层，不是理解 Skill 的必经操作。外部触发条件继续排除在内部主逻辑之外；图中节点也不承担点击导航。" if zh else "This is a verification layer, not a required navigation surface. External routing stays outside internal runtime.")}</p>',
        diagrams_html,
        '<div class="evidence-grid">',
        f'<div><h3>{html_text("结构诊断" if zh else "Diagnostics")}</h3><ul>{diagnostic_items}</ul></div>',
        f'<div><h3>{html_text("资源清单" if zh else "Resources")}</h3><ul>{resource_items}</ul></div>',
        '</div>',
        '<details class="raw-details">',
        f'<summary>{html_text("查看外部触发边界" if zh else "View external routing boundary")}</summary><ul>{routing_items}</ul>',
        '</details>',
        '<details class="raw-details">',
        f'<summary>{html_text("查看 Mermaid 源码" if zh else "View Mermaid source")}</summary><pre>{html_lib.escape(raw_mermaid)}</pre>',
        '</details>',
        '<details class="raw-details">',
        f'<summary>{html_text("查看完整 JSON 模型" if zh else "View complete JSON model")}</summary><pre>{html_lib.escape(model_json)}</pre>',
        '</details>',
        '</div></details></section>',
        '</main>',
        f'<footer>{html_text(skill["name"])} · Mermaid {MERMAID_VERSION} · {html_text("离线单文件审阅" if zh else "offline single-file review")}</footer>',
        '</div>',
        f'<script id="logic-model" type="application/json">{embedded_json}</script>',
        f'<script data-vendor="mermaid@{MERMAID_VERSION}">{mermaid_bundle}</script>',
        '<script>', BRIEF_HTML_JS, '</script>',
        '</body></html>',
    ]
    return "\n".join(html_parts)


def default_html_path(markdown_output: Optional[Path], explicit_html: Optional[Path]) -> Optional[Path]:
    if explicit_html:
        return explicit_html
    if markdown_output:
        return markdown_output.with_suffix(".html")
    return None


def write_output(path: Path, content: str) -> None:
    path = path.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path, help="Skill directory or SKILL.md path")
    parser.add_argument("-o", "--output", type=Path, help="Write the Markdown report here")
    parser.add_argument("--json", dest="json_output", type=Path, help="Write the JSON logic model here")
    parser.add_argument("--html", dest="html_output", type=Path, help="Write the standalone HTML review here")
    parser.add_argument("--no-html", action="store_true", help="Do not derive a sibling HTML file from --output")
    parser.add_argument("--direction", choices=("TB", "LR"), default="TB")
    parser.add_argument("--language", choices=("auto", "zh", "en"), default="auto")
    parser.add_argument(
        "--max-depth",
        type=int,
        default=2,
        help="Follow linked local Markdown references to this depth (0-5)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when extraction reports an error diagnostic",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if not 0 <= args.max_depth <= 5:
        print("error: --max-depth must be between 0 and 5", file=sys.stderr)
        return 2
    if args.no_html and args.html_output:
        print("error: --html and --no-html cannot be used together", file=sys.stderr)
        return 2
    try:
        skill_root, skill_file = resolve_skill(args.target)
        model = build_model(skill_root, skill_file, args.max_depth)
        report = render_report(model, args.direction, args.language)
        if args.output:
            write_output(args.output, report)
        else:
            print(report)
        if args.json_output:
            write_output(
                args.json_output,
                json.dumps(model, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            )
        html_output = None if args.no_html else default_html_path(args.output, args.html_output)
        if html_output:
            write_output(html_output, render_html(model, args.direction, args.language))
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.strict and any(item["level"] == "error" for item in model["diagnostics"]):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
