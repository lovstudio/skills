# HTML Generation: McKinsey Style Report

## Design Principles

- Sharp corners (NO border-radius)
- Muted corporate colors (navy #003d5c, gray #f8f9fa)
- Ultra-compact layout
- Info-first structure
- 14px base font, compact spacing
- No decorative gradients or colors
- NO EMOJIS in final HTML

---

## Generation Steps

### Step 1: Read McKinsey Template
Load template from: `./templates/mckinsey_report_template.html`

### Step 2: Extract Key Metrics
Extract 3-4 key quantitative findings for dashboard display at top.

### Step 3: Convert MD to HTML

Use Python script:
```bash
cd ~/.claude/skills/deep-research
python scripts/md_to_html.py [markdown_report_path] --embed-images
```

**Script outputs two parts:**
- **Part A ({{CONTENT}}):** All sections except Bibliography
- **Part B ({{BIBLIOGRAPHY}}):** Bibliography section only

**Script handles all conversion:**
- Headers: `##` -> `<div class="section"><h2 class="section-title">`
- Headers: `###` -> `<h3 class="subsection-title">`
- Lists: Markdown bullets -> `<ul><li>` with nesting
- Tables: Markdown tables -> `<table>` with thead/tbody
- Paragraphs: Text wrapped in `<p>` tags
- Bold/italic: `**text**` -> `<strong>`, `*text*` -> `<em>`
- Citations: [N] preserved for tooltip conversion
- Figures: a standalone `![alt](figures/{name}.png)` line plus an italic `*图 N：...*` caption line becomes `<figure class="report-figure">`; `--embed-images` inlines local files as data URIs so the HTML stays self-contained. Style figures at max-width 100% with `break-inside: avoid` for print

### Step 4: Add Citation Tooltips (Optional)

Attribution Gradients - wrap each [N] citation:
```html
<span class="citation">[N]
  <span class="citation-tooltip">
    <div class="tooltip-title">[Source Title]</div>
    <div class="tooltip-source">[Author/Publisher]</div>
    <div class="tooltip-claim">
      <div class="tooltip-claim-label">Supports Claim:</div>
      [Extract sentence with this citation]
    </div>
  </span>
</span>
```
NOTE: This step is optional for speed. Basic [N] citations are sufficient.

### Step 5: Replace Template Placeholders

| Placeholder | Content |
|-------------|---------|
| {{TITLE}} | Report title (from first ## heading) |
| {{DATE}} | Generation date (YYYY-MM-DD) |
| {{SOURCE_COUNT}} | Number of unique sources |
| {{METRICS_DASHBOARD}} | Metrics HTML from step 2 |
| {{CONTENT}} | HTML from Part A |
| {{BIBLIOGRAPHY}} | HTML from Part B |

### Step 6: Verify HTML

```bash
python scripts/verify_html.py --html [html_path] --md [md_path]
```
- Pass: Proceed to open
- Fail: Fix errors and re-run

### Step 7: Open in Browser
```bash
open [html_path]
```

---

## PDF Generation

**Option A: WeasyPrint Direct (Preferred)**

1. Create print-optimized HTML following `./reference/weasyprint_guidelines.md`
2. Critical CSS:
   - `page-break-inside: avoid` on tables, boxes
   - `page-break-after: avoid` on headings
   - `orphans: 3; widows: 3` on paragraphs
   - Use `display: table` not Flexbox/Grid
   - Font sizes in pt (10pt body, 8pt citations)
3. Generate: `weasyprint [html_path] [pdf_path]`
4. Open: `open [pdf_path]`

**Option B: generating-pdf Skill**

Use Task tool with general-purpose agent, invoke generating-pdf skill.

**After printing (required, before opening or delivering)**

Headless Chrome / Playwright writes every ideograph that shares a glyph with a CJK radical as the radical code point (U+2F00–U+2FD5, U+2E80–U+2EF3): the pages look right, but copying or searching 「手工川」 returns 「⼿⼯川」. Run the fixer shipped by the `lov-rich-export` dependency (resolve its directory through the active Agent Skills environment) on every PDF you deliver:

```bash
python3 "<lov-rich-export>/scripts/fix_pdf_tounicode.py" [pdf_path]
```

It rewrites only the text layer, so the pages render unchanged. Pass only when it prints `radicals left in text 0` (exit 0); a clean WeasyPrint PDF is left untouched.
