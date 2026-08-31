# Changelog

## 0.1.1

- Made the bare QR image the explicit default with no header, footer, title, visible payload, or poster frame.
- Persisted the user-stated no-poster and no-visible-data preferences while retaining request-level overrides.
- Added regression and real scan evidence for the default bare-code path.

## 0.1.0

- Added local PNG QR generation for URL, text, file and stdin payloads.
- Added Warm Academic palettes, rounded shapes, poster mode and optional Logo embedding.
- Added Profile-backed preferences without persisting QR payloads.
- Added structural and real scan verification with privacy-preserving JSON results.
