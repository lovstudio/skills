# Changelog

## [0.8.4] - 2026-11-10

### Changed

- publishing.md: the catalog's `Refresh website` workflow (lovstudio/skills#66) now refreshes lovstudio.ai after each catalog push and checks `catalog_commits`. It skips the per-Skill tags and only warns without its secret, so the Revalidate request stays part of every publication.
- AGENTS.md: notes that workflow, its `LOVSTUDIO_REVALIDATE_SECRET` secret, and that Cloudflare answers Python's default User-Agent on lovstudio.ai with `403 error code: 1010`.

## [0.8.3] - 2026-11-10

### Changed

- publishing.md: revalidate right after the catalog merge. lovstudio.ai now reads the catalog and the free Skill documents mirrored into it at the commit `main` points to (lovstudio/lovstudio-home#148), and `/api/revalidate` answers with `catalog_commits`; the call worked when that commit is the one `main` points to. The 5-minute wait remains only for a response without the catalog's commit, when the site fell back to raw's cached `main`. The entry-count step is gone: the commit replaces it.
- AGENTS.md: the revalidate note follows the same rule.

## [0.8.2] - 2026-11-10

### Fixed

- publishing.md: a free Skill passes a public-copy gate before its content is first pushed to a public repository (read every case, case-citing paragraph, reference example and test fixture; keep structure and counts only). A commit on a public pull request cannot be recalled: fix on the branch, squash-merge and tell the user which commit stays visible. SKILL.md Step 5 points to the gate.
- publishing.md: revalidate at least 5 minutes after the catalog reaches `main` (raw CDN `max-age=300`), then confirm the site read the new catalog through `pricing_sync.catalog_skills` or the public `/api/skills/catalog`; lovstudio.cn is fed from OSS and is not refreshed by this call.
- publishing.md: while catalog CI cannot clone a private source, the free mirror travels with the pull request (`SKIP_CLONE=1` for a new entry, `git archive` plus the script's excludes for an existing mirror). Distribution state is written `pending` then `live`, the tag follows `live`, and the second, mirror-only pull request does not trigger CI.
- publishing.md: measure existing `tagline_zh` / `tagline_en` lengths before drafting and stay within the current maximum.
- AGENTS.md: one cross-session note per rule above; the tip to rsync a mirror straight from the working directory is replaced by the export-based refresh.

## [0.8.1] - 2026-10-29

### Fixed

- validate_skill.py `--target source` fails when `skill.yaml`, `skill-card.yaml`, or `pricing-card.yaml` declares a `version` different from `SKILL.md` `metadata.version`, listing every file's value; lov-koubo-media-creator 0.2.0 was tagged with `skill.yaml` still at 0.1.0 while this gate passed.
- Step 1 explains the check and why the stale file must be synced before tagging.

## [0.8.0] - 2026-10-04

### Changed

- Paid Skills are no longer encrypted: payment only gates the download. The paid delivery contract now requires a private source repo tagged `v{version}` and catalog metadata (`repo`, `version`, `skill_path`) instead of an encrypted bundle or `public_source`; installs download the tagged source from lovstudio.ai as plain files.

## [0.7.7] - 2026-09-28

### Fixed

- accept the lovstudio CLI install preflight key in source frontmatter
- validate_skill.py source target allows top-level dependencies and checks each entry is {name, check, install}; needed so lov-media-creator 0.20.0 can be published

## [0.7.6] - 2026-09-11

### Fixed

- verify installs in project mode so dev symlinks survive
- publishing.md: run the catalog install command with --project from a throwaway directory
- record the ~/.agents/skills symlink-clobber failure mode and the payload checks that follow

## [0.7.5] - 2026-09-07

### Added

- 统一展示名为「Skill 发布助手」，保持调用 ID 与能力契约。

## [0.7.4] - 2026-09-06

### Fixed

- move mandatory pricing dependency to canonical top-level depends_on

## [0.7.3] - 2026-08-30

- Accept and validate canonical top-level `depends_on` declarations during source publication.

## [0.7.2] - 2026-08-27

### Fixed

- define `global` / `all` licenses as dynamic access to every currently listed Skill instead of a frozen grant snapshot
- require publication verification to cover dynamic global, explicit ownership, and unentitled Credits paths

## [0.7.1] - 2026-08-27

### Fixed

- require paid Skill Publisher entries to declare and verify either protected encrypted delivery or explicit public-source delivery before publication

## [0.7.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## [0.6.0] - 2026-08-24

### Changed

- default channel-less publishing requests to the LovStudio official website
- run all supported adapters only for explicit all-channel or multi-platform requests
- preserve automatic `lov-skill-pricing` as the mandatory pre-publish step
- use the current `LOVSTUDIO_REVALIDATE_SECRET` variable in website revalidation guidance

## [0.5.0] - 2026-08-14

### Added

- support legacy WorkBuddy raw names
- allow external raw_name metadata for updates to existing WorkBuddy listings without changing canonical Skill IDs

## [0.4.1] - 2026-08-14

### Fixed

- target the unified lovstudio/skills catalog
- replace archived General and Dev catalog settings and cache tags

## [0.4.0] - 2026-08-14

### Added

- default every publishing run to evidence-backed automatic pricing
- reuse one lov-skill-pricing Pricing Card across Skill Publisher, WorkBuddy, and SkillPay adapters
- treat explicit user prices as publishing constraints and fix the Skill Publisher reference path

## [0.3.3] - 2026-08-11

### Fixed

- 补齐发布器 compatibility 元数据和 Skills CLI 安装入口

## [0.3.2] - 2026-08-11

### Fixed

- 让 source validator 接受标准 compatibility 元数据

## [0.3.1] - 2026-08-10

### Changed

- 未指定渠道时默认运行全部支持的发布适配器；显式渠道参数仍可收窄发布范围。

## [0.3.0] - 2026-08-03

### Added

- 接入 CodeBuddy WorkBuddy 上架流程
- 使用独立 ZIP、解析成功与审核状态作为发布证据

## [0.2.2] - 2026-08-03

### Added

- 修复 WorkBuddy 子 Skill 的本地资源校验
- 按最近 SKILL.md 解析打包后 references 中的 SKILL_DIR 路径

## [0.2.1] - 2026-08-03

### Added

- 修复 Publisher 自身的 WorkBuddy 自包含打包
- 发布 Publisher 时保留其运行所需的校验与打包脚本

## [0.2.0] - 2026-08-03

### Added

- 统一为 publisher 角色命名
- 同步 Creator 与 Distiller 的发布交接名称

## 0.1.1

- Add Alipay SkillPay as a first-class adapter with explicit package, upload,
  review, and live completion gates.
- Make WorkBuddy Skill Kit modules self-contained by copying shared resources and localizing `$KIT_DIR` references in standalone module packages.
- Preserve the full SemVer suffix when deriving a Connector ZIP name from an output directory such as `v0.2.0`.

## 0.1.0

- Add an independent multi-channel publishing workflow for validated local Skills.
- Support Skill Publisher source, release, catalog, revalidation, and live verification.
- Support external-profile WorkBuddy Connector packaging and import evidence.
- Keep channel metadata and generated artifacts outside canonical Skill source.
- Define a provider adapter contract for future official distribution channels.
