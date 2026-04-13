#!/bin/bash
# Convert Markdown to PDF
# Usage: md2pdf.sh file1.md [file2.md ...]

for f in "$@"; do
  [[ "$f" == *.md ]] || continue
  output="${f%.md}.pdf"
  /opt/homebrew/bin/pandoc "$f" \
    --pdf-engine=xelatex \
    -V mainfont="PingFang SC" \
    -V geometry:margin=2cm \
    -o "$output"
  echo "Created: $output"
done
