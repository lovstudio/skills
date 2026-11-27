# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [1.2.1] - 2026-11-27

### Fixed

- SKILL.md frontmatter 通过发布校验：去掉 `category`、`tagline`，描述压到 200 字以内，`metadata.tags` 改为列表
- 新增 `## Triggers`，写明触发与不触发的条件

## [1.2.0] - 2026-11-27

### Added

- 新增 `mono` 风格（单色印刷：暖灰纸纹 + 锈橙油墨 + 近黑），规范见 `references/styles/mono.md`；视觉参考 yanliudesign/mono-color-skill 的 reference-04
- 新增 `scripts/mono_pptx_kit.py`：可编辑 PPTX 工具包，纸纹与 Logo 写进母版、图片与图标转单色调、问题页、结论句、Q&A 二维码页、按 `## Pxx` 写演讲者备注；`--demo` 生成 5 页样张并自检
- 预设表、自动选风格表、维护备注补上 mono 及其踩坑

## [1.1.3] - 2026-11-20

### Fixed

- README 的安装命令改为 `npx lovstudio skills add any2deck -g -y`：不带斜杠的名字会被 `npx skills add` 当作 git 源，报 repository does not exist，装不上。

## [1.1.2] - 2026-10-31

### Added

- 维护备注：补回 2026-08-21 至 2026-09-05 的 5 条经验（此前只在未接入真源的安装副本里），涵盖 `apply-branding.py` 调用目录、大图合成耗时与二维码透明底、`build-batch.ts` 标题识别、讲稿与画面指令分离、满幅风格不叠 logo

### Changed

- `merge-to-pptx.ts` 优先读取 `notes/<stem>.md` 作为演讲者备注，`prompts/` 仅作兜底；只有回退到 `prompts/` 时才拼接基础 prompt（补回安装副本里的改动）

## [1.1.1] - 2026-09-25

### Added

- 合并本地未提交改动到上游 1.1.0 之上
- 本地改动：统一展示名为「PPT 大师」，保持调用 ID 与能力契约。

## [1.1.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## [1.0.2] - 2026-05-07

### Fixed

- split detailed workflow into progressive disclosure reference
- move long workflow instructions to references/workflow.md

## [1.0.1] - 2026-05-07

### Fixed

- add release metadata
- add README version badge and changelog entry

