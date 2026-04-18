# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [0.3.0] - 2026-04-13

### Added

- Add image embedding, auto-refresh TOC, YAML frontmatter stripping, adaptive cover title
- Images: local paths (relative to .md) and remote URLs auto-downloaded and embedded
- TOC: field code + static fallback + updateFields=true for auto-refresh on open
- Frontmatter: YAML front matter block fully stripped from output
- Cover: title font size adapts to length (36pt→22pt) to prevent overflow
- Version: corrected from 1.0.0 to 0.x per repo conventions

