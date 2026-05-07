# lovstudio:expense-report

![Version](https://img.shields.io/badge/version-0.1.3-CC785C)

Invoice images / text → categorized Excel expense report.

## Install

```bash
git clone https://github.com/lovstudio/expense-report-skill \
          "${LOVSTUDIO_SKILLS_INSTALL_DIR:?Set LOVSTUDIO_SKILLS_INSTALL_DIR}/lovstudio-expense-report"
```

## Dependencies

```bash
pip install openpyxl
```

## Usage

Invoke in Claude Code:

```
/lovstudio:expense-report
```

Then provide invoice images or text descriptions. The skill will:

1. Extract invoice details (date, vendor, amount, type)
2. Auto-classify into expense categories
3. Confirm with you before generating
4. Output a styled Excel report with category subtotals

## Categories

| Category | Examples |
|----------|----------|
| 业务招待 | 客户餐费, 商务宴请, 礼品 |
| 差旅-交通 | 机票, 火车票, 打车, 加油 |
| 差旅-住宿 | 酒店, 宾馆 |
| 差旅-餐饮 | 出差工作餐 |
| 办公用品 | 文具, 打印, 办公设备 |
| 通讯费 | 话费, 流量, 宽带 |
| 其他 | 未分类费用 |

## Script CLI

```bash
python scripts/generate_report.py --input invoices.json --output report.xlsx
```

**Input JSON format:**

```json
[
  {
    "date": "2026-04-15",
    "vendor": "海底捞",
    "item": "客户餐费",
    "amount": 486.0,
    "category": "业务招待",
    "note": "与XX公司李总晚餐"
  }
]
```

## Output

Excel with two sheets:

- **发票报销汇总** — Full itemized report grouped by category
- **分类汇总** — Summary: category, count, subtotal

## License

MIT
