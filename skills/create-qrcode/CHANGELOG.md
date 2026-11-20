# Changelog

## [0.1.3] - 2026-11-20

### Fixed

- README 的安装命令改为 `npx lovstudio skills add create-qrcode -g -y`：不带斜杠的名字会被 `npx skills add` 当作 git 源，报 repository does not exist，装不上。

## [0.1.2] - 2026-09-07

### Added

- 统一展示名为「二维码工坊」，保持调用 ID 与能力契约。

## 0.1.1

- Made the bare QR image the explicit default with no header, footer, title, visible payload, or poster frame.
- Persisted the user-stated no-poster and no-visible-data preferences while retaining request-level overrides.
- Added regression and real scan evidence for the default bare-code path.

## 0.1.0

- Added local PNG QR generation for URL, text, file and stdin payloads.
- Added Warm Academic palettes, rounded shapes, poster mode and optional Logo embedding.
- Added Profile-backed preferences without persisting QR payloads.
- Added structural and real scan verification with privacy-preserving JSON results.
