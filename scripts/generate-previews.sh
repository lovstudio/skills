#!/bin/bash
# Generate theme preview images for README
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
PREVIEW_DIR="$REPO_DIR/docs/previews"
MD2PDF="$REPO_DIR/skills/lovstudio-any2pdf/scripts/md2pdf.py"
SAMPLE="$PREVIEW_DIR/_sample.md"

THEMES=(
  warm-academic nord-frost github-light solarized-light
  paper-classic ocean-breeze monokai-warm dracula-soft
  tufte classic-thesis ieee-journal elegant-book
  chinese-red ink-wash
)

mkdir -p "$PREVIEW_DIR"

# Create sample markdown
cat > "$SAMPLE" << 'MARKDOWN'
## 概述 Overview

在现代产品开发中，数据驱动的设计方法已成为行业标准。通过结合 **定量分析** 与 **定性洞察**，团队能够做出更明智的决策。This approach enables teams to iterate faster and build products that truly resonate with users.

### 关键指标 Key Metrics

| 指标 Metric | Q1 | Q2 | 变化 Change |
|---|---|---|---|
| 用户留存率 Retention | 68% | 74% | +6% |
| 转化率 Conversion | 3.2% | 4.1% | +0.9% |
| NPS 得分 Score | 42 | 51 | +9 |
| 月活 MAU | 120K | 158K | +31.6% |

### 技术实现 Implementation

```python
def analyze_cohort(users, period="monthly"):
    """分析用户群组留存 Analyze cohort retention"""
    cohorts = group_by_signup(users, period)
    return {k: retention_curve(v) for k, v in cohorts.items()}
```

### 设计原则 Design Principles

1. **用户至上** — 所有设计决策都应以用户需求为出发点
2. **数据验证** — 通过 A/B 测试验证设计假设
3. **快速迭代** — 小步快跑，持续优化产品体验

> 好的设计是尽可能少的设计。—— Dieter Rams
> Good design is as little design as possible.

### 下一步计划 Next Steps

团队将在 Q3 聚焦于个性化推荐引擎的开发。核心目标是将用户留存率提升至 **80%** 以上，同时保持 `NPS > 50` 的满意度水平。We will leverage machine learning models to deliver personalized experiences at scale.
MARKDOWN

echo "Generating previews..."

for theme in "${THEMES[@]}"; do
  echo "  → $theme"
  pdf="$PREVIEW_DIR/${theme}.pdf"
  png="$PREVIEW_DIR/${theme}.png"

  # Generate PDF
  python3 "$MD2PDF" \
    --input "$SAMPLE" \
    --output "$pdf" \
    --theme "$theme" \
    --cover false \
    --toc false \
    2>/dev/null

  # Convert first page to PNG (300 DPI, then resize for web)
  pdftoppm -png -f 1 -l 1 -r 150 "$pdf" "${PREVIEW_DIR}/${theme}_tmp"
  mv "${PREVIEW_DIR}/${theme}_tmp-1.png" "$png"

  # Cleanup PDF
  rm -f "$pdf"
done

# Cleanup
rm -f "$SAMPLE"

echo "Done! Preview images in $PREVIEW_DIR/"
echo ""
echo "Themes generated: ${#THEMES[@]}"
