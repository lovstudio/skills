---
name: lov-expense-report
category: Finance
tagline: "Invoice images/text → categorized Excel expense report."
description: >
  Extract invoice data from images or text descriptions and generate a
  categorized Excel expense report. Supports receipt photos, scanned invoices,
  and manual text input. Auto-classifies into: business entertainment (客户餐费),
  travel-transport (机票/火车票/打车), travel-accommodation (酒店), travel-meals,
  office supplies, communication, and other. Use when the user mentions
  "发票报销", "expense report", "报销单", "发票整理", "invoice", "报销汇总",
  "发票分类", "reimbursement", or has invoice images to process.
license: MIT
compatibility: >
  Requires Python 3.8+ and openpyxl (`pip install openpyxl`).
  Cross-platform: macOS, Windows, Linux.
metadata:
  author: contributors
  version: "0.2.0"
  tags: invoice expense report reimbursement excel categorize
---

# expense-report — Invoice → Categorized Excel

Extract invoice information from images or text, classify expenses, and generate
a professional Excel report with subtotals per category.

## When to Use

- User has invoice photos / scanned receipts to process
- User describes expenses in text and wants them organized
- User needs a categorized reimbursement report (报销单)
- User mentions 发票报销, 报销汇总, 发票整理, expense report

## Expense Categories

| Category | Keywords / Examples |
|----------|-------------------|
| 业务招待 | 客户餐费, 商务宴请, 礼品, 招待 |
| 差旅-交通 | 机票, 火车票, 高铁, 出租车, 打车, 网约车, 加油, 过路费, 停车费 |
| 差旅-住宿 | 酒店, 住宿, 宾馆 |
| 差旅-餐饮 | 出差期间餐费, 工作餐 |
| 办公用品 | 文具, 打印, 办公耗材, 办公设备 |
| 通讯费 | 话费, 流量, 网费, 宽带 |
| 其他 | 不属于以上类别的费用 |

## Workflow (MANDATORY)

### Step 1: Collect Invoice Data

Accept input in any of these forms:

- **Images**: Read invoice photos using the Read tool. Extract: date, vendor, amount, item type, notes.
- **Text descriptions**: Parse the user's text for the same fields.
- **Mixed**: Multiple images + supplementary text.

For each invoice, extract these fields:

```json
{
  "date": "2026-04-15",
  "vendor": "海底捞(国贸店)",
  "item": "客户餐费",
  "amount": 486.00,
  "category": "业务招待",
  "note": "与XX公司李总晚餐"
}
```

### Step 2: Classify

Assign each invoice to a category from the table above. Rules:

1. If the user explicitly states the category, use it.
2. If the item/vendor clearly matches a category keyword, auto-assign.
3. For ambiguous items (e.g., "餐费" could be 业务招待 or 差旅-餐饮):
   - If the note mentions a client/customer → 业务招待
   - If the context is a business trip → 差旅-餐饮
   - If unclear, ask the user.

### Step 3: Confirm with User

Before generating, show the extracted data as a table:

```
| # | 日期 | 商户 | 项目 | 金额 | 分类 | 备注 |
|---|------|------|------|------|------|------|
| 1 | 2026-04-15 | 海底捞 | 客户餐费 | 486.00 | 业务招待 | 与XX公司李总 |
| 2 | 2026-04-14 | 滴滴出行 | 打车 | 45.50 | 差旅-交通 | 机场→酒店 |
```

Use `AskUserQuestion` to ask: "以上信息是否正确? 需要修改或补充吗?"

### Step 4: Generate Excel

Write the confirmed data to a temp JSON file, then run:

```bash
python expense-report-skill/scripts/generate_report.py \
  --input /tmp/invoices.json \
  --output "发票报销汇总-YYYYMMDD.xlsx"
```

**JSON format** (array of objects):

```json
[
  {"date": "2026-04-15", "vendor": "海底捞", "item": "客户餐费", "amount": 486.0, "category": "业务招待", "note": "与XX公司李总"},
  {"date": "2026-04-14", "vendor": "滴滴出行", "item": "打车", "amount": 45.5, "category": "差旅-交通", "note": "机场→酒店"}
]
```

### Step 5: Deliver

Tell the user:
- Output file path
- Total amount and breakdown by category
- Remind them to review the "分类汇总" sheet for the summary

## Output Format

The Excel file contains two sheets:

1. **发票报销汇总** — Full detail, grouped by category with subtotals
2. **分类汇总** — Summary table: category, count, subtotal

Style: Skill Publisher warm-academic (terracotta headers #4F46E5, warm cream accents).

## Edge Cases

- **Blurry/unreadable image**: Tell the user which fields couldn't be extracted; ask them to provide manually.
- **Foreign currency**: Note the currency; convert to CNY if user provides rate, otherwise keep original with note.
- **Duplicate invoices**: Flag potential duplicates (same date + vendor + amount) before generating.
- **No date on invoice**: Use the date the user provides, or mark as "日期不详".

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
