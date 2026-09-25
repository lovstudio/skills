# Changelog

## [0.18.0] - 2026-09-11

### Changed

- `references/charts.md` 补一条：图形内部文字先量再放——中心数字放不下就扩大内环或上移标题，
  不得压住色块，也不得把字号压到下限以下

## [0.17.0] - 2026-09-11

### Changed

- 长卡默认顺序固定为：关键数字 → 构成与名单 → 时间线 → 手法/流程 → 专题；同一信息不拆成两节
- `references/charts.md` 增加「直接标注」：引线 + HTML 标注块替代图例，标注后整体缩放保证完整显示

## [0.16.0] - 2026-09-11

### Changed

- 卡片不写作者总结与个人观点：正文只放来源的事实、数字与口径；`data-claim` 行改为可选（最多一条）
- `single_claim` 审计改为「最多一条」：没有 claim 行是合法状态
- 文案红线：小节副标题不复述标题、不写「报告称／报告显示」这类来源提示、不写「最该记住」这类元话术
- docs：SKILL 红线、手机可读性标准、模板语法与 spec-schema 同步

## [0.15.0] - 2026-09-11

### Added

- `references/charts.md`：在卡片里使用 D3 等图表库的工程约定——库内联离线渲染、图形与文字分层
  （SVG 只画形状，标签留 HTML 层）、颜色与角度编码写进 `data-encoding`

## [0.14.0] - 2026-09-11

### Changed

- 长卡密度契约：优先用名单行、矩阵、小倍数、关键数字块与流程条带压缩篇幅，逐案写段落是最后手段
- docs：SKILL 红线第 9 条与手机可读性标准记录这条密度规则

## [0.13.0] - 2026-09-11

### Changed

- 标题契约补一条：不写「要点」「速览」「全览」「一图读完」「一图看懂」这类放在任何信息图上
  都成立的废话；作用式标题必须给出真实信息（给谁看、回答什么、覆盖什么范围）
- 新增 `title_filler` 审计项拦截通用废话词；作用式示例同步改成带真实信息的写法

## [0.12.0] - 2026-09-11

### Changed

- 标题契约：标题只写这张图的作用或主题，判断与结论归 claim 行；`data-claim` 从标题移到 claim 行
- `title_is_thesis` 换成 `title_is_subject`：只拦截没有主题信息（纯数字/符号）的标题，不再要求判断句
- `step-strip` 模板补 claim 行；七套模板统一「标题不挂 data-claim」
- docs：SKILL 红线、README、模板骨架与 spec-schema 同步新的标题与 claim 契约

## [0.11.0] - 2026-09-11

### Changed

- 长卡内容契约：必须按来源章节还原要点、关键数字与代表案例，只给总量与结论句不算反映原文
- `bar_value` 检查：条形数值必须以数字开头（像「（10 起）」这种写法无法解析，会让倒序校验失效）
- docs：SKILL 红线、手机可读性标准与模板语法同步这条内容契约

## [0.10.0] - 2026-09-11

### Changed

- 输出契约改为「永远一张图」：内容再多也把这张 `long` 卡加长，不再因为超过三屏就拆系列；
  系列只保留用户显式要求多张时的路径
- `long_height` 从上限警告改为信息项：单卡不设高度上限，审计只记录实际高度与约合屏数
- `bar_order` 改为按 `.chart` 分组分别校验倒序，支持长卡里的「总览 + 分领域小节」
- `render` 把截图框对齐到设备像素网格：长卡的小数高度不再产生 1–2 设备像素的尺寸偏差
- docs：SKILL、README、reading standard、series-and-export、template-grammar、spec-schema 同步单卡契约

## [0.9.1] - 2026-09-11

### Fixed

- appendix entries use the page title followed by the URL
- appendix item format: page title, comma, full URL; never invent a short name
- docs record that the title must come from the target page's title/h1

## [0.9.0] - 2026-09-11

### Added

- divider instead of an Appendix heading, larger trimmed logo
- appendix starts with a thin rule (.appendix-rule); the Appendix heading word is gone
- footer logo renders at 80px and uses the trimmed asset so the mark fills its box
- docs: logo minimum and no-heading rule recorded

## [0.8.0] - 2026-09-11

### Added

- appendix block above the footer, logo-only centred footer for single cards
- new .appendix component: bullets for 数据来源 / 信息图呈现 with plain-text URLs
- single cards centre the logo and drop the page number; series keep left logo + n/N
- packaged footer credit is empty by default because provenance now lives in the appendix
- series_page check accepts an empty page mark when data-series-size is 1

## [0.7.1] - 2026-09-11

### Fixed

- print URLs as text because the deliverable is a PNG
- footer credit and source line print the domain as plain text; no anchors whose meaning depends on being clickable
- footer shows the tool URL alone so the line stays inside the note width limit

## [0.7.0] - 2026-09-11

### Added

- credit carries a real URL, source credits the data tool, counts sit right of the bar
- brand credit defaults to 'Powered by' + credit_link so the footer prints an actual URL instead of a bare word
- source line may credit the processing tool with its public page (e.g. WDB CLI → lovstudio.ai/skills/wdb-cli) while still banning local paths and table names
- bar-ranking prints the count in parentheses at the right end of the bar instead of a left column

## [0.6.0] - 2026-09-11

### Added

- three stacked full-width lines per ranked row, public nicknames
- bar-ranking rows are three full-width stacked lines: item + description / count + bar / roster, no side column
- scope remarks move to the footnote; titles carry no kicker jargon
- member names use the person's own public nickname instead of internal remarks, so no masking is needed
- footnote explains the inference: 依据群聊记录自动分析得出的可能匹配成员

## [0.5.0] - 2026-09-11

### Added

- two-line ranked rows with the value column beside the bar
- bar-ranking rows are now exactly two lines: item + one-line description, then bar + count + roster
- --row takes LABEL|VALUE|DESCRIPTION|MEMBERS|GROUP; the count sits next to the bar
- header slimming: subject title + plain conclusion line, no redundant prefixes or '结论：'
- SKILL.md 明确：标题与副标题不再重复上下文前缀，副标题不写「结论：」
- bar-order, long-height and source-hygiene gates unchanged

## [0.4.0] - 2026-09-11

### Added

- rank bars descending, expand what each item is, keep masked names
- bar-ranking must be sorted by value descending; new bar_order audit check
- each ranked row needs a one-line 'what it is' description before the roster
- titles: McKinsey action title or plain subject, no vague meta phrasing
- masking defaults to light masking that keeps surname and identity instead of full anonymisation
- ban restating chart numbers as bullet prose in the same card

## [0.3.0] - 2026-09-11

### Added

- require a thesis title, graphical ranking, and safe sourcing
- new bar-ranking template with --row LABEL|VALUE|NOTE|GROUP so comparable items are read as bar length instead of prose
- title_is_thesis warning: a title that only restates numbers is not an infographic thesis
- source_hygiene error: internal database paths, table names and tool names never appear on a card
- footer credit is now optional (credit / credit_link in the brand profile) and defaults to 'Powered by 卡片'
- docs: masking rule targets name-out identity-in, and list/flow-chart anti-patterns are named

## [0.2.0] - 2026-09-11

### Added

- default to one long card with adaptive height
- default ratio is long (single card, content-driven height, ceiling of three 3:4 screens)
- series is now opt-in: only when the user asks for several cards or a long card exceeds the ceiling
- audit adds a long_height warning for adaptive-height cards
- README gains an install command and documents the new default

### Fixed

- `image_size` 审计允许 1 设备像素容差：长卡高度是小数，浏览器元素盒与截图位图会差 1px，
  更大的偏差仍按错误处理

## 0.1.0

- 初始版本：1080 宽手机信息图，支持 `3:4`、`4:5`、`9:16`、`1:1` 与 `long` 五种画布比例。
- 六个语义模板：`single-claim`、`step-strip`、`metric-focus`、`compare-pair`、`checklist-gate`、`quote-evidence`。
- `scripts/infographic_cli.py`：`init-brand`、`scaffold`、`render`、`audit` 四个子命令。
- 移动可读性门禁：字号下限、行宽上限、对比度、安全区、裁切与越界、单一结论、证据挂载、
  品牌页脚、系列页码、骨架文案残留与省略号截断，100 分制代理分与 85 分阈值。
- 真实案例：三卡系列，机器审计 3/3 通过（各 100/100），附原图与 320px 缩略图复核记录。
