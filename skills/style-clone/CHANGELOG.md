# Changelog

## [0.1.2] - 2026-06-26

### Fixed

- Step 4 存档改为默认执行，不再询问用户
- Step 2 输出画像后默认落盘到 ./output/style-profiles/
- 仅当用户显式拒绝时才跳过存档

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
