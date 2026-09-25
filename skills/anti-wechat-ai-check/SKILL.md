---
name: lov-anti-wechat-ai-check
description: >
  兼容旧命令的中文表层模式扫描器，只定位套话、句段均匀和过渡词等可观察特征，
  不判断作者身份或平台风险。新任务请使用 lov-human-writing。Use only for legacy
  “anti-ai-check” commands. Use when reproducing a legacy surface scan; route
  “去 AI 味” and “humanize article” to lov-human-writing.
license: MIT
compatibility: >
  Requires Python 3.8+ (stdlib only, no external dependencies).
  Cross-platform: macOS, Windows, Linux.
depends_on:
  - lov-branding-consistency
metadata:
  author: contributors
  version: "1.1.2"
  content_class: deterministic-output
  tags:
    - legacy-compatibility
    - surface-patterns
    - content-review
---

# 文风扫描（旧入口） · Writing Pattern Scan (Legacy)

本 Skill 已弃用，只为旧命令和脚本调用保留兼容入口。它能扫描模板短语、过渡词、
句长与段长均匀度，但这些都是表层启发式，不能证明文本由 AI 生成，也不能预测
微信或其他平台的审核结果。新的诊断、改写和复测任务交给 `lov-human-writing`。

不得把本 Skill 用于规避平台标识、内容披露、学术诚信或审核机制。

## Triggers

### Activate when

- 用户明确要求复现旧版 `anti-ai-check` 报告或维护 `scripts/analyze.py` 兼容调用。
- “Run the legacy anti-ai-check surface scan.”

### Do not activate when

- “去 AI 味”“人性化润色”“像不像 AI 写的”“humanize article”——使用
  `lov-human-writing`，先审作者性和篇章结构，再做表层度量。
- 用户要求“通过检测”“绕过审核”或删除 AI 标识——拒绝规避目标，只提供质量改进、
  事实核查和合规披露帮助。

## Workflow (MANDATORY)

**You MUST follow these steps in order:**

### Step 1: Get the article

Determine the input source:
- If user provides a **file path** → read the file
- If user **pastes text** in the conversation → save to a temp file or use `--text`

### Step 2: Run analysis

```bash
python skills/lov-anti-wechat-ai-check/scripts/analyze.py \
  --input <path> --format json
```

Or with inline text:

```bash
python skills/lov-anti-wechat-ai-check/scripts/analyze.py \
  --text "文章内容" --format json
```

### Step 3: Present findings

Show the user:
1. **Legacy heuristic score** (0-100) and band (LOW / MEDIUM / HIGH). Explain
   that it is an uncalibrated surface-pattern sum, not an AI probability or
   platform risk score.
2. **Template phrases found** — list each one with its location
3. **Structure issues** — transition word density, paragraph uniformity, etc.
4. **Sentence issues** — length uniformity, repeated starters, excessive "的"

### Step 4: Hand off

只交付兼容报告，并明确推荐下一步使用 `lov-human-writing`。不要在本 Skill 中
改写全文，不要为了“增加人味”补造个人经历、数字、情绪、错别字或不规范表达。
任何真实改写都必须从作者提供的事实、判断和可追溯材料开始。

## CLI Reference

| Argument | Default | Description |
|----------|---------|-------------|
| `--input`, `-i` | — | Input file path (.md, .txt) |
| `--text`, `-t` | — | Inline text to analyze |
| `--format`, `-f` | `text` | Output format: `text` or `json` |

## Dependencies

No external dependencies — stdlib only.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
