# Skill Publisher Rich Export

![version](https://img.shields.io/badge/version-0.1.0-CC785C.svg)

将一份 Markdown、HTML 或 `rich-export.json` 导出为单文件 HTML、HTML 文件夹、Markdown、DOCX、PDF 与 ZIP 交付包；HTML 保留交互媒体，其余格式提供可读的静态投影与原链接。

```bash
python3 scripts/export_rich.py \
  --input ./article.md \
  --out ./exports \
  --formats html-single,html-dir,md,docx,pdf \
  --zip
```

完整工作流和输入契约见 `SKILL.md` 与 `references/`。
