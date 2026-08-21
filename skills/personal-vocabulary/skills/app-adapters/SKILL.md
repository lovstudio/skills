---
name: lov-app-adapters
description: >
  定义各语音输入法与剪辑工具的词汇表读写映射：OpenLess、Typeless 等。本地 JSON 直接读写，API 走用户凭据只读探测，未知格式先探测不编造。Trigger: 读/写 OpenLess 词库、同步到 Typeless、适配剪映词库、app vocabulary adapter.
license: MIT
metadata:
  author: LovStudio / 手工川工作室
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  tags:
    - vocabulary
    - adapter
    - openless
    - typeless
  compatibility: "Portable Agent Skills format; reads local JSON or calls a vendor API with the user's own credential. Never persists credentials."
  dependencies: []
---

# lov-app-adapters — 各 App 词库映射

把规范词库的字段映射成某款具体 App 的词汇表格式，并负责读写。映射是声明式的；读取目标 App 时只读、不覆盖对方已有词条。

## Triggers

### Activate when

- 用户要把词库导入/导出到 OpenLess、Typeless 或其它语音输入法。
- 用户提供了某款 App 的词汇表文件或接口，要求解析或转换。
- The user wants to read or write a specific app's vocabulary.

### Do not activate when

- 用户只维护规范词库（交给 canonical-store）。
- 用户要决定哪些词推给哪些 App（交给 sync-plan）。

## Adapter registry

| app | 存储 | 字段映射 | 状态 |
|---|---|---|---|
| openless | `~/Library/Application Support/OpenLess/dictionary.json` | phrase → phrase；note → note；enabled → enabled；hits → hits；createdAt → created_at | 已实测 |
| typeless | `GET https://api.typeless.com/user/dictionary/list`（Bearer 用户 token） | phrase → term；category → category；lang → lang；auto → auto；replace → replace | 已实测 |
| capcut / 剪映 | 待探测 | 待探测 | 未确认 |

OpenLess 词条结构为 `{id, phrase, note, enabled, hits, createdAt}`；Typeless 词条结构为 `{user_dictionary_id, term, lang, category, auto, replace, replace_targets, created_at, updated_at}`。

## Workflow

1. 确认目标 App 与读写方向（读入规范/写回 App）。
2. 本地 JSON（OpenLess）直接按字段映射读写；`vocab_cli.py render` 已内置 openless 映射。
3. 走 API 的（Typeless）用用户自己的凭据，仅做只读探测获取词条。**不得**在命令、日志或聊天中打印 token；查询用 `auto=0/1` 数字值并禁用缓存，避免字符串布尔导致空数据。
4. 格式未确认的 App（剪映）先探测真实存储与字段，确认后再补映射；未确认前标注"未确认"，不编造。

## Dependencies

- Python 3.9+ 标准库；API 调用使用系统代理或用户既有网络。
- 需要用户授权访问其本地词库文件或账号凭据；凭据不持久化。
