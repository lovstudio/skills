---
name: lov-fix-deepseek-tool-call-error
description: >
  修复 Codex 在 DeepSeek（provider=yoda）会话里的 No tool output found for tool call 400 与 thread 永久锁死：扫描本地 rollout 取证，恢复任务并落地看图与批次规避规则。Use when a DeepSeek thread fails with No tool output found for tool call.
license: MIT
compatibility: "Portable Agent Skills format. Python 3.8+ standard library only; reads local Codex rollout JSONL; no network, no credentials."
metadata:
  author: skill-publisher
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  tags:
    - codex
    - deepseek
    - tool-call
    - diagnostics
    - recovery
---

# Codex × DeepSeek 会话急救 · Codex × DeepSeek Thread First Aid

Codex 在 DeepSeek（`provider=yoda`、`wire_api = "responses"`）上跑长任务时，只要一条
assistant 消息里同时发出多个工具调用、且批次里存在被缩放的图片，Codex 就会在批次结果
齐全之前发出下一次请求，DeepSeek 以 `No tool output found for tool call call_XX_...`
返回 400，并让这条 thread 永久失败。本 Skill 负责取证、恢复与预防。

## Triggers

### Activate when

- 用户贴出 `No tool output found for tool call call_...` 报错，或说“又报错了”“这个 thread 又废了”。
- 用户问 Codex + DeepSeek 为什么看图或长任务会 400，或要求“以后别再出现”。
- 需要盘点本机有哪些 thread 中毒、它们是否同一个诱因。
- Use when a Codex thread reports No tool output found for tool call, or the user asks to review every wedged thread on this machine.

### Do not activate when

- 报错发生在别的 provider，或 `wire_api = "chat"` 的配置上；先按 `lov-fix-general` 常规排错。
- 用户只是想读某条 thread 的进度或结果；交给 `lov-read-codex-session`。
- 用户要修的是产品代码缺陷；交给 `lov-fix-general` 或 `debug-pro`。

## Outputs

- 事故清单：时间、thread、被拒调用、同批调用、是否涉及缩放图片、是否已锁死。
- 恢复方案：中毒 thread 的处置方式与接续路径。
- 预防清单：要写入的规则与命令；默认只给方案，不改全局配置。

## Workflow (MANDATORY)

### Step 0: 定位

- 用 `SKILL_DIR`，否则按当前 Skill 上下文推断安装目录。
- 确认 `scripts/scan_deepseek_sessions.py` 存在；缺失时先报出期望路径，不产出半成品。
- 本 Skill 只读：不改 rollout、不改 thread、不写外部服务。

### Step 1: 取证

```bash
python3 "$SKILL_DIR/scripts/scan_deepseek_sessions.py"
```

- 默认扫描 `~/.codex/sessions` 与 `~/.codex/archived_sessions`；用 `--root` 追加目录，
  用 `--file` 指定单个 rollout，用 `--json` 取结构化结果。
- 表格每行是一起事故：时间、session、被拒调用、同批调用、变体、同 call 重复失败次数。
- 用户给了 thread 链接时，同时用宿主的 thread 读取能力看它的实时状态（只读）。
- 大数据量下全量扫描约一分钟；只要相关 thread 时优先用 `--file` 精确扫描。

### Step 2: 判定

- `variant = image_batch_with_resize_notice`：批次含 `view_image`，且该 thread 出现过
  `<image_resize_notice>` —— 当前已知的唯一真实诱因。
- 重复失败次数大于 1，或同一 session 反复出现：thread 已锁死，后续每一轮都会在同一秒失败。
- 批次里没有图片调用时，对照 `references/mechanism.md` 的其它触发路径（hook 注入的
  developer 消息、被中断的批次），不要直接套用图片结论。

### Step 3: 恢复

按 `references/recovery.md` 执行：

- 中毒 thread 不重试、不 fork（fork 继承坏历史，同样 400）。
- 先试 archive → unarchive 让宿主卸载内存中的坏历史；仍失败则新开 thread。
- 新 thread 只通过文本读取旧 thread 的结论与文件路径，绝不导入旧的 assistant 消息。
- 工作产物已在磁盘上，先确认产物完整，再决定是否需要重跑。

### Step 4: 预防

按 `references/prevention.md` 落地，默认顺序：

1. `view_image` 独占一条消息，不与任何其它工具调用同批（含 `sips`、`rg` 这类快命令）。
2. 看图前先生成长边不超过 2048 的副本：`sips -Z 2048 <图> --out <副本>`。
3. 需要高保真视觉复核时，把图交给外部视觉能力（如 `lov-describe-image`），会话内不看图。
4. 规则写入宿主常驻 Prompt 与领域 reference；只在用户明确同意时改动全局配置。
5. 禁止用关闭 `view_image` 工具的方式规避：代价是整机失去看图能力，破坏性远大于收益。

### Step 5: 验证与报告

- 重跑扫描器，确认没有新增事故；如果做了修复动作，回读改动文件确认规则真的存在。
- 输出必须区分：已取证、已恢复、已预防、仍待验证。
- 明确边界：本 Skill 不能修复已中毒的历史，也不能替代上游对竞态的修复；它让用户止损、
  复盘并把规避前移。

## Dependencies

- Python 3.8+ 标准库；可选 PyYAML 仅用于 `scripts/validate_skill.py`。
- 需要本地 Codex 会话目录的读权限；无网络、无凭据。
- 相关能力（可选，不构成硬依赖）：`lov-read-codex-session` 读 thread 状态，
  `lov-describe-image` 提供外部看图通道，`lov-feedback-loop` 记录事故反馈。
