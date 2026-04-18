# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [2.0.0] - 2026-04-18

### Changed

- Rewrite for per-skill-repo architecture. Each skill is now an independent repo at `lovstudio/{name}-skill` instead of a subdirectory of a monorepo.
- Default scaffold path: `~/lovstudio/coding/skills/{name}-skill/` (was `skills/lovstudio-{name}/`).
- Install hint: `git clone` each skill repo (replaces `npx skills add lovstudio/skills`).
- `init_skill.py`: accepts `--paid`, auto-creates `.gitignore`, and prints `gh repo create` + symlink + index-registration next-steps instead of monorepo-dev-flow hints.

### Added

- Step 5b: PR to `lovstudio/skills` central index (`skills.yaml` + `README.md`).
- Step 5d: lovstudio.ai ISR cache revalidation via `skills-index` tag.
- Migration note for legacy skills still in the monorepo structure.

### Removed

- Step 0 (repo choice): `lovstudio/pro-skills` was archived 2026-04-16. `paid` now lives only in `index/skills.yaml` as a business classification, not as a skill property.

## [1.2.0] - 2026-04-15

### Added

- Add Step 0: repo selection (lovstudio/skills vs lovstudio/pro-skills)
- Step 5c: create PR to chosen target repo instead of push to main

## [1.1.1] - 2026-04-14

### Fixed

- Add publish workflow: symlink chain + git push to Step 5

## [1.1.0] - 2026-04-14

### Added

- Fix init_skill.py repo detection — prefer lovstudio-skills over cwd
- README template now includes version badge
- Remove CHANGELOG from 'What NOT to Include' (managed by skill-optimizer)

