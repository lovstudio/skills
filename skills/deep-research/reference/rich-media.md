# Rich Media: Figures, Photos, Maps and Diagrams

Deep-research reports carry evidence in pictures as well as prose. Every report at standard depth or above must include figures, and each figure is held to the same evidence discipline as a cited sentence.

## Minimums

| Mode | Minimum figures | Typical mix |
|------|-----------------|-------------|
| quick | 1 | one overview chart or diagram |
| standard | 3 | data chart, structure or process diagram, one primary-source visual |
| deep | 5 | about one figure per major finding |
| ultradeep | 8 | one or more per finding, plus overview figures for the summary and appendices |

`scripts/validate_report.py` enforces this: zero figures in a standard+ report is an error, fewer than the minimum is a warning, and missing local files are an error. A report may fall short of the minimum only when the topic genuinely has nothing to show; say why in the Methodology appendix.

## What to include, in priority order

1. **First-hand visuals.** Photos, recordings, screenshots or scans supplied by the user or captured during the research (field photos, product UI, document pages, signage). These are the strongest evidence and the least likely to raise rights issues. Look for them in the working directory before searching the web.
2. **Data charts built from the report's own cited numbers.** Time series, comparisons, composition, distributions. The chart must use exactly the numbers in the text, cite the same sources in its caption, and show uncertainty: label estimates, mark values whose method is unpublished, and keep conflicting figures visible rather than averaging them.
3. **Explanatory diagrams.** Timelines, governance or stakeholder structures, process and approval flows, decision trees, before/after comparisons. Draw them from evidence already in the report; a diagram may not introduce new facts.
4. **Maps and spatial graphics** for anything place-based: location, boundaries, routes, venue positions, catchment. Prefer data you can redistribute (the project's own geodata, OpenStreetMap with attribution, official open data).
5. **Third-party images** only when the licence allows reuse (public domain, CC0, CC BY with attribution, official open data with reuse terms). Record the licence in the caption. Otherwise do not embed: describe the image and link to it in the source list ("原图见 [N]"). Never hotlink remote images.

Never present AI-generated imagery as documentary evidence. A generated illustration is allowed only as a clearly labelled schematic ("示意图，非实景"), and only when no real visual exists.

## Preparing photos

- Keep originals untouched; work on copies under `figures/`.
- Convert HEIC and RAW to JPEG (`sips -s format jpeg -Z 1800 in.heic --out figures/fig07-gate.jpg` on macOS), long edge 1600–2000 px, quality about 80.
- Strip EXIF, especially GPS, before publishing.
- Build a contact sheet first when there are many photos, choose deliberately, then open the chosen originals to confirm what they show.
- Avoid close-up identifiable faces of bystanders and minors, private interiors, licence plates and personal documents. Crop or choose another frame.
- A photo proves what was visible when it was taken. Caption it with the capture date or date range and say it is a single observation.

## Making charts and diagrams

- Python with matplotlib is the default; save PNG at 200 dpi or SVG. Set a CJK-capable font for Chinese reports (PingFang SC, Hiragino Sans GB, Noto Sans CJK SC or Source Han Sans SC) and check that no glyph falls back to boxes.
- One message per chart. Title the chart with its takeaway, label axes with units, start bar axes at zero, and put the source line in the caption.
- Use one restrained palette across the report, with a single accent for the point being made. Keep text at least 9 pt in print.
- Diagrams (structures, flows, timelines) can be drawn with matplotlib patches, Graphviz when installed, or hand-written SVG. Mermaid is acceptable only when the HTML/PDF renderer has been verified to draw it; otherwise render to an image first.

## Captions, files and placement

- Number figures in reading order. Put the image on its own line, followed by a caption line in italics:

  ```markdown
  ![南城门南侧立面，城门洞上方门额“宁南”](figures/fig{NN}-{slug}.jpg)
  *图 7：南城门是城垣保存最完整的一段。实地拍摄，2026 年 9 月下旬；城门年代见 [12]。*
  ```

- The caption states the takeaway, then the source: citation numbers for data, "实地拍摄 + date" for first-hand photos, "本报告据 [N][M] 绘制" for charts and diagrams, licence and author for third-party images.
- Alt text describes what is in the picture for readers who cannot see it.
- Store files in `figures/` next to the Markdown report, named `figNN-slug.ext`. Markdown uses relative paths.
- Place each figure next to the paragraph it supports. Aim for at least one figure per major finding when evidence allows; the executive summary may carry one overview figure.
- Add a figure index (图表目录) to the Methodology appendix or after the table of contents for reports with eight or more figures.

## Rendering and delivery

- HTML: `python scripts/md_to_html.py report.md --embed-images` inlines local figures as data URIs so the HTML is self-contained. Style `figure.report-figure` with a max width of 100%, centred, and a muted caption.
- PDF: print the self-contained HTML (headless Chrome or WeasyPrint). Keep figures from splitting across pages (`break-inside: avoid`).
- Size budget: keep the self-contained HTML under about 25 MB and the PDF under 30 MB. Compress photos (JPEG) and keep line art as PNG or SVG.
- Look at the rendered HTML or PDF once before delivery: figures present, captions under the right images, no broken glyphs.

## Gate checklist

- [ ] Figure count meets the mode minimum, or the shortfall is explained in Methodology
- [ ] Every figure has alt text and a numbered caption with a source line
- [ ] Every number in a chart matches the text and is cited
- [ ] First-hand photos are dated, privacy-checked and EXIF-stripped
- [ ] Third-party images are licensed for reuse and attributed, or replaced by links
- [ ] No AI-generated image is presented as real
- [ ] `validate_report.py` passes the Figures check and the rendered output was inspected once
