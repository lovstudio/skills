# Changelog

## 4.0.0

- Make local source creation, validation, and local installation the complete
  default workflow.
- Move remote repositories, catalogs, marketplace packaging, uploads, and live
  verification to the separate `sgc-skill-publisher` capability.
- Infer user configuration from persistent workspace, brand, identity, output,
  locale, and provider needs instead of asking users to choose a mode.
- Remove the LovStudio-internal configuration branch; every source is portable
  and LovStudio is represented through ordinary profile values.
- Add opt-in `--user-config` and local `--install-dir` scaffold controls.

## 3.1.0

- Infer implementation type and Single Skill versus Skill Kit composition from
  product requirements instead of asking users to choose technical machinery.
- Reserve interactive questions for unresolved product, commercial,
  distribution, and user-facing configuration decisions.
- Prefer contextual prefill and sensible defaults before interactive prompts.

## 3.0.0

- Separate portable source frontmatter from platform distribution metadata.
- Add Tencent WorkBuddy as a first-class distribution profile.
- Generate self-contained Skill Kits with `kit.yaml` and embedded modules.
- Add standard-YAML source, WorkBuddy, and package validation.
- Add deterministic WorkBuddy ZIP building with source metadata injection.
- Emit a combined Connector ZIP plus independently installable controller and
  module ZIPs for composable Skill Kits.
- Reject missing modules, broken local links, unresolved placeholders, private
  paths, caches, and compiled Python artifacts before release.
- Require explicit activation and non-trigger conditions for every Skill.

## 2.9.1

- Make synchronization to `lovstudio.ai/skills` a mandatory publication step.
- Revalidate catalog, detail, cases, and user-facing routes after catalog merge.
- Require live HTTP, version, and content checks before reporting publication.

## 2.9.0

- Remove the repository-target question from the interactive creation flow.
- Remove the obsolete `--target` and `--dev-skills` scaffold arguments.
- Make `lovstudio/{name}-skill` an unconditional source-repository invariant.
- Keep general-skills and dev-skills as inferred downstream distribution only.

## 2.8.0

- Make `lovstudio/{name}-skill` the only supported source-repository model.
- Treat `lovstudio/dev-skills` as a release-driven generated aggregate mirror.
- Scaffold CI, MIT license, and changelog files for every new independent skill.
- Reject the retired `--target dev-skills` mode with migration guidance.

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [2.7.0] - 2026-05-07

### Added

- make scaffold roots profile driven
- resolve source roots from LOVSTUDIO_SKILL_CREATOR_* env vars or shared profile before safe fallbacks
- remove personal workspace and fixed agent runtime paths from generated templates

## [2.6.1] - 2026-05-07

### Fixed

- publish LovStudio skill standard reference
- add references/skill-standard.md as the canonical standardization document

## [2.6.0] - 2026-05-07

### Added

- standardize config env vars on LOVSTUDIO_SKILLS namespace
- replace AGENT_SKILL_* in generated templates
- keep defaults under ~/.lovstudio/skills

## [2.5.0] - 2026-05-07

### Added

- move default skill profile under ~/.lovstudio
- keep AGENT_SKILL_PROFILE as the portable override
- default generated brand/design config paths to ~/.lovstudio/skills

## [2.4.0] - 2026-05-07

### Added

- switch public config contract to AGENT_SKILL profile
- replace LovStudio-prefixed profile paths in new-skill templates
- keep LovStudio paths as private authoring examples, not reusable runtime API

## [2.3.0] - 2026-05-06

### Added

- add portable user configuration scaffolding
- switch new templates to Agent Skills-compatible sgc-<name> frontmatter
- generate references/user-config.md for new skills
- move historical migration notes into references/migration.md for progressive disclosure

## [2.2.0] - 2026-05-06

### Added

- Document optional SKILL.md frontmatter `depends_on` for required skill-level dependencies.
- Scaffold templates now include commented `depends_on` guidance so new skills can declare reuse relationships explicitly.

## [2.1.0] - 2026-05-06

### Added

- Add `dev-skills` as a first-class repository target for free Meta / Dev Tools skills.
- `init_skill.py` now supports `--target dev-skills` and `--dev-skills`.
- Document `repo: lovstudio/dev-skills` + `skill_path: skills/<name>` registration and marketplace plugin updates.

## [2.0.0] - 2026-04-18

### Changed

- Rewrite for per-skill-repo architecture. Each skill is now an independent repo at `lovstudio/{name}-skill` instead of a subdirectory of a monorepo.
- Default scaffold path: `~/lovstudio/coding/skills/{name}-skill/` (was `skills/sgc-{name}/`).
- Install hint: `git clone` each skill repo (replaces `npx skills add lovstudio/skills`).
- `init_skill.py`: accepts `--paid`, auto-creates `.gitignore`, and prints `gh repo create` + symlink + index-registration next-steps instead of monorepo-dev-flow hints.

### Added

- Step 5b: PR to `lovstudio/skills` central index (`skills.yaml` + `README.md`).
- Step 5d: lovstudio.ai ISR cache revalidation via `skills-index` tag.
- Migration note for legacy skills still in the monorepo structure.

### Removed

- Step 0 (repo choice): `lovstudio/pro-skills` was archived 2026-04-16. `paid` now lives only in `sgc-general-skills/skills.yaml` as catalog metadata, not as a skill property.

## [1.2.0] - 2026-04-15

### Added

- Add Step 0: repo selection (lovstudio/skills vs lovstudio/pro-skills)
- Step 5c: create PR to chosen target repo instead of push to main

## [1.1.1] - 2026-04-14

### Fixed

- Add publish workflow: symlink chain + git push to Step 5

## [1.1.0] - 2026-04-14

### Added

- Fix init_skill.py repo detection — prefer sgc-skills over cwd
- README template now includes version badge
- Remove CHANGELOG from 'What NOT to Include' (managed by skill-optimizer)
