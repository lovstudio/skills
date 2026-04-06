# lovstudio:fill-form

Fill Word document form templates (.docx) with structured data. Auto-detects table-based form fields (label → value cell pairs), supports CJK/Latin mixed text with proper font switching, merged cells, and paragraph-based forms.

Part of [lovstudio/skills](https://github.com/lovstudio/skills) &mdash; by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx skills add lovstudio/skills --skill lovstudio:fill-form
```

Requires: Python 3.8+ and `pip install python-docx`

## How It Works

```
┌─────────────────────────────────────────────────┐
│  Template (.docx)                               │
│  ┌──────────┬───────────┬──────────┬──────────┐ │
│  │ 主讲人   │           │ 职称     │          │ │
│  ├──────────┼───────────┴──────────┴──────────┤ │
│  │ 单位     │                                 │ │
│  ├──────────┼───────────┬──────────┬──────────┤ │
│  │ 讲座题目 │           │ 时间     │          │ │
│  └──────────┴───────────┴──────────┴──────────┘ │
└────────────────────┬────────────────────────────┘
                     │ --scan → detect fields
                     │ --data → fill values
                     ▼
┌─────────────────────────────────────────────────┐
│  Filled (.docx)                                 │
│  ┌──────────┬───────────┬──────────┬──────────┐ │
│  │ 主讲人   │ 张三      │ 职称     │ 教授     │ │
│  ├──────────┼───────────┴──────────┴──────────┤ │
│  │ 单位     │ 北京大学                        │ │
│  ├──────────┼───────────┬──────────┬──────────┤ │
│  │ 讲座题目 │ AI与未来  │ 时间     │ 4月10日  │ │
│  └──────────┴───────────┴──────────┴──────────┘ │
└─────────────────────────────────────────────────┘
```

## Usage

**Step 1** — Scan the template to see all detected fields:

```bash
python fill_form.py --template form.docx --scan
```

Output:

```
Detected 6 form fields:

  1. 主讲人
  2. 职称
  3. 单位
  4. 讲座题目
  5. 时间
  6. 地点

--- JSON ---
{
  "主讲人": "",
  "职称": "",
  ...
}
```

**Step 2** — Fill with a JSON data file or inline JSON:

```bash
# From JSON file
python fill_form.py --template form.docx --data-file data.json

# Inline JSON
python fill_form.py --template form.docx \
  --data '{"主讲人": "张三", "职称": "教授", "单位": "北京大学"}'
```

Output saves to the same directory as the template (`form_filled.docx`).

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--template` | (required) | Path to template .doc/.docx |
| `--output` | `<name>_filled.docx` | Output path (defaults to template directory) |
| `--scan` | | List all detected form fields |
| `--data` | | JSON string with field → value mapping |
| `--data-file` | | Path to JSON file with field → value mapping |
| `--font` | Platform CJK serif | Font for filled text |
| `--font-size` | `11` | Font size in points |

## Field Detection

The script detects fillable fields in three ways:

| Method | How it works | Example |
|--------|-------------|---------|
| **Table cells** | Label in one cell, blank value in adjacent cell | `│ 姓名 │ ___ │` |
| **Merged rows** | Full-width cell with `Label：` pattern | `│ 备注：________________ │` |
| **Paragraphs** | Fallback for docs without tables | `姓名：` followed by blank line |

Fields are matched by normalized label (whitespace-insensitive), so `主 讲 人` matches `主讲人`.

## Supported Formats

| Format | Support |
|--------|---------|
| `.docx` | Full support (recommended) |
| `.doc` | Auto-converts via `textutil` (macOS) or LibreOffice. Table structure may be lost — convert to `.docx` first for best results. |

## License

MIT
