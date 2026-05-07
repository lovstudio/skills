# Changelog

## [0.1.1] - 2026-05-07

### Fixed

- make install path configurable
- replace fixed runtime install directory with LOVSTUDIO_SKILLS_INSTALL_DIR

## 0.1.0

### Features

- Initial release: analyze sample articles to extract an 8-dimension writing style profile (文风画像)
- Rewrite any target article in the extracted style
- Support for multiple sample articles (extracts shared characteristics)
- Output structured style profile covering: sentence rhythm, paragraph structure, vocabulary, narrative voice, emotional register, argumentation, rhetorical devices, and style DNA
- Optional style profile archival to `./output/style-profiles/`
