---
name: lov-canonical-store
description: >
  维护规范个人词汇表 vocabulary.json 的结构与读写：新增、去重合并、按 phrase 比对与导入导出。Trigger: 建规范词库、合并去重词条、导出词汇表、manage the canonical vocabulary file, dedupe imported terms.
license: MIT
metadata:
  author: LovStudio / 手工川工作室
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  tags:
    - vocabulary
    - canonical
    - dedupe
  compatibility: "Portable Agent Skills format; Python 3.9+ standard library only."
  dependencies:
    - python
---

# lov-canonical-store — 规范词汇表

规范词库是**单一事实来源**：一份 `vocabulary.json` 持有你的全部词条，其它 App 只是它的下游视图。本模块负责这份文件的结构、去重合并与导入导出。

## Triggers

### Activate when

- 用户要建立、读取或维护一份统一词汇表。
- 用户给了外部词条（文件、粘贴、口述）要求合并去重进规范词库。
- The user asks to create, merge, or export the canonical vocabulary.

### Do not activate when

- 用户只关心某款具体 App 的词库读写（交给 app-adapters）。
- 用户要制定跨 App 同步策略（交给 sync-plan）。

## Canonical shape

`vocabulary.json`：

```json
{
  "version": 1,
  "updated_at": "2026-08-21T00:00:00+00:00",
  "entries": [
    {
      "phrase": "手工川工作室",
      "note": null,
      "category": "general",
      "lang": "zh-CN",
      "enabled": true,
      "hits": 0,
      "source": "manual",
      "created_at": "2026-08-21T00:00:00+00:00",
      "updated_at": "2026-08-21T00:00:00+00:00"
    }
  ]
}
```

字段约定：`phrase` 唯一键；`category` 取 general/company/person/product/place/other；`lang` 用 BCP-47 标签；`hits` 只增不手动清；`source` 记录 manual/import/openless/typeless 等来源。

## Workflow

1. 定位 `vocabulary.json`：优先用 `records.canonical_path`，其次当前工作目录，最后 `workspace` 下的默认路径。没有则新建。
2. 用 `scripts/vocab_cli.py merge` 导入新词条：按 `phrase` 精确去重，已存在则保留已有条目，仅在缺失时追加。
3. 导出到某 App 格式时用 `render` 子命令，仅做字段映射，不改 canonical。

## Merge / render examples

```bash
python3 "$KIT_DIR/scripts/vocab_cli.py" merge \
  --canonical vocabulary.json \
  --import source.json \
  --from-app openless

python3 "$KIT_DIR/scripts/vocab_cli.py" render \
  --app openless \
  --canonical vocabulary.json \
  --output openless-dictionary.json
```

脚本不访问网络、不写目标 App；合并与渲染都是纯文本、幂等。

## Dependencies

- Python 3.9+，仅标准库。
