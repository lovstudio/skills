# 富文档导出 · Rich Export

![Version](https://img.shields.io/badge/version-0.2.3-CC785C)

将一份 Markdown、HTML 或 `rich-export.json` 导出为单文件 HTML、HTML 文件夹、Markdown、DOCX、PDF 与 ZIP 交付包；HTML 保留交互媒体，其余格式提供可读的静态投影与原链接。

```bash
python3 scripts/export_rich.py \
  --input ./article.md \
  --out ./exports \
  --formats html-single,html-dir,md,docx,pdf \
  --zip
```

Chrome/Playwright 打印的中文 PDF，复制出来会是「⼿⼯川」这类部首码位；导出 PDF 时已自动修复，其他流程打印的 PDF 可单独修复：

```bash
python3 scripts/fix_pdf_tounicode.py ./report.pdf
```

完整工作流和输入契约见 `SKILL.md` 与 `references/`。