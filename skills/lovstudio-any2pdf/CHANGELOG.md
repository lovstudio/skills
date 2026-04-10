# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [1.0.1] - 2026-04-10

### Fixed

- fix silent image drops: resolve relative paths against input md dir
- resolve relative image paths against the input markdown's directory (not cwd)
- warn on missing images instead of silently dropping them (stderr)
- collapse multi-line image refs in _preprocess_md so pandoc --wrap=auto output parses correctly
- SKILL.md: add Input Format section (markdown-only), document pandoc --wrap=none tip
- README.md: add version badge

