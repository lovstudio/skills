# lovstudio:review-doc

![Version](https://img.shields.io/badge/version-0.3.1-CC785C) ![Category](https://img.shields.io/badge/category-business-blue)

Review & annotate documents/contracts — output annotated docx with comments or tracked changes.

批阅文档与合同 — 审阅文档并以批注或修订模式输出带标注的 docx。

Part of [lovstudio/skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx skills add lovstudio/skills --skill lovstudio:review-doc
pip install python-docx --break-system-packages
```

## Usage

```
/review-doc @合同.docx
```

AI 提取段落 -> 确认审阅模式 -> 逐条分析 -> 输出带批注的 docx。

## CLI

```bash
# 提取段落文本（供 AI 分析）
python3 scripts/annotate_docx.py extract --input contract.docx

# 应用批注/修订
python3 scripts/annotate_docx.py annotate \
  --input contract.docx \
  --annotations review.json \
  --output contract-reviewed.docx
```

## Annotations JSON

```json
{
  "comments": [
    {"paragraph": 3, "text": "【风险】此条款...", "author": "手工川"}
  ],
  "revisions": [
    {"paragraph": 5, "old": "原文", "new": "修改后", "author": "手工川"}
  ]
}
```

## License

MIT
