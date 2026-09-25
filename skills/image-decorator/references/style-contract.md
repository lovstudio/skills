# Caption style contract

The default `editorial-caption` style adapts the supplied magazine reference to
LovStudio's Warm Academic palette without copying publication identity.

Use `screenshot-caption` for software screenshots that already contain window
edges, cards, borders, rounded corners, or shadows. It preserves the complete
opaque UI content, trims transparent and semi-transparent screenshot-tool shadow
margins, flattens residual transparent corners against an edge-derived background,
adds no frame or extra rounding, and attaches the caption bar directly beneath
the screenshot. Do not stack a decorative border around an existing interface
boundary.

## Layout

- Preserve the complete source image; do not crop it.
- Add a rounded warm off-white outer frame; keep the complete source image as a
  rectangular inset so no source corner is clipped.
- Append a charcoal caption bar beneath the image.
- Set the caption at the left and a verified brand mark at the right.
- Scale padding, type, bar height, corner radius, and logo from the source width.
- Permit up to three caption lines by default; reduce type within a guarded range
  before failing. Do not truncate user text silently.

## Material routing

- Artwork, photography, and cover imagery: `editorial-caption`.
- Software screenshots and captured UI: `screenshot-caption`.
- Rendered tables and diagrams: keep the caller's explicit choice; do not infer
  screenshot styling solely from a white background.

## Default palette

- Frame: `#F9F9F7`
- Caption bar: `#181818`
- Caption: `#F9F9F7`
- Logo: preserve the bundled or explicitly supplied asset colors and alpha.
- Caption weight: Medium 500 when the selected font exposes a variable weight axis.

## Caption and logo precedence

Caption: explicit `--caption`, Skill Profile `records.default_caption`, then
`Powered by lovstudio.ai/skill/image-decorator`.

Logo: explicit `--logo`, Skill Profile `records.logo_path`, shared Profile
`brand.logo` when it resolves to a local raster file, then the bundled LovStudio
mark. Remote logo URLs are not fetched by this deterministic local CLI.
