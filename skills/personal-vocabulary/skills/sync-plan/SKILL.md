---
name: lov-sync-plan
description: >
  比较规范词库与各 App 实际词条，产出同步计划：新增、已存在、冲突三类，确认后再执行，默认不覆盖对方已有词条。Trigger: 同步词汇到 App、看看哪些词没同步、生成同步计划、vocabulary sync plan.
license: MIT
metadata:
  author: LovStudio / 手工川工作室
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  tags:
    - vocabulary
    - sync
    - diff
  compatibility: "Portable Agent Skills format; Python 3.9+ standard library only."
  dependencies:
    - python
---

# lov-sync-plan — 同步计划

比对规范词库与目标 App 的词条，给出**只读差异**，用户确认后再执行写入。默认不覆盖对方已有词条，避免把用户攒下的命中数据或自定义词清掉。

## Triggers

### Activate when

- 用户要求把规范词库同步到某款 App。
- 用户想先看"哪些词没同步 / 哪些冲突"再决定。
- The user wants to diff and plan a vocabulary sync.

### Do not activate when

- 用户只维护规范词库或只读某 App 词库（交给对应模块）。

## Output classes

| class | 含义 | 处理 |
|---|---|---|
| add | canonical 有、App 没有 | 建议写入 |
| skip | 两边 phrase 相同且关键字段一致 | 无需处理 |
| conflict | phrase 相同但关键字段不同 | 需用户裁决，默认保留 App 侧 |
| app_only | App 有、canonical 没有 | 提示是否回填 canonical |

## Workflow

1. 读取规范词库与目标 App 词条（经 app-adapters）。
2. 按 phrase 归一化后匹配，关键字段为 `note`、`category`、`lang`、`enabled`。
3. 输出差异清单给用户，标注每类数量；**先确认再执行**。
4. 执行时只做 `add`，绝不覆盖 `conflict` 或删除 `app_only`，除非用户明确要求。

## Diff example

```bash
python3 "$KIT_DIR/scripts/vocab_cli.py" diff \
  --app openless \
  --canonical vocabulary.json \
  --app-file openless-dictionary.json
```

脚本输出纯文本差异，不写入任何 App。

## Dependencies

- Python 3.9+，仅标准库。
