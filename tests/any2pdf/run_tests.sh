#!/usr/bin/env bash
# Test runner for any2pdf bug fixes and new features
# Usage: bash tests/any2pdf/run_tests.sh
#
# Generates PDFs into tests/any2pdf/output/ for manual inspection.

set -e

SCRIPT="skills/lovstudio-any2pdf/scripts/md2pdf.py"
DIR="$(cd "$(dirname "$0")" && pwd)"
INPUT="$DIR/test_cases.md"
COVER="$DIR/test_cover.jpg"
OUT="$DIR/output"

mkdir -p "$OUT"

echo "=== Test 1 & 2: code spans with *, tables with #, H3+ headings, anchor tags ==="
python3 "$SCRIPT" --input "$INPUT" --output "$OUT/test_basic.pdf" --theme warm-academic
echo "  → $OUT/test_basic.pdf"
echo "  Check: foo*bar renders as code, tables intact, H4/H5 visible, no anchor text"
echo

echo "=== Test 3: --image-cover true with frontispiece ==="
python3 "$SCRIPT" --input "$INPUT" --output "$OUT/test_image_cover.pdf" \
  --theme warm-academic --frontispiece "$COVER" --image-cover true
echo "  → $OUT/test_image_cover.pdf"
echo "  Check: page 1 = full-bleed cover image, page 2 = text cover"
echo

echo "=== Test 4: watermark params ==="
python3 "$SCRIPT" --input "$INPUT" --output "$OUT/test_watermark.pdf" \
  --theme warm-academic --watermark "机密文件" \
  --wm-size 30 --wm-opacity 0.1 --wm-angle 45
echo "  → $OUT/test_watermark.pdf"
echo "  Check: watermark '机密文件' with small font(30), low opacity(0.1), 45° angle"
echo

echo "=== Test 5: --heading-top-spacer 20 ==="
python3 "$SCRIPT" --input "$INPUT" --output "$OUT/test_spacer20.pdf" \
  --theme warm-academic --heading-top-spacer 20
echo "  → $OUT/test_spacer20.pdf"
echo "  Check: H1/H2 chapter title top spacing visibly larger than test_basic.pdf"
echo

echo "=== All tests generated. Open $OUT/ to inspect. ==="
