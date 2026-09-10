# Changelog

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
