# Changelog

## [4.4.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## 4.3.0

- Add mandatory nearby-Skill composition analysis and a generated atomic-handoff record.

## 4.2.0

- Make `user-profile/v1` a default contract for every generated Skill.
- Add cross-session profile reads and atomic direct-user record persistence.
- Generate `skill.yaml`, `references/user-profile.md`, and `profile_store.py` for
  single Skills and embedded Skill Kit modules.

## 4.1.0

- Require a reusable Skill trust bundle: Skill Card, real user case, dimension
  map, pricing basis, and explicit distribution states.
- Scaffold machine-readable and human-readable card files plus a case template.
- Validate Input → Prompt → Output evidence, dimension evidence, pricing basis,
  and unresolved placeholders before local completion.
- Expand the standard to cover language units such as words, idioms, slang, and
  complex expressions when a Skill's domain needs them.

## 4.0.0

- Make local source creation, validation, and local installation the complete
  default workflow.
- Move remote repositories, catalogs, marketplace packaging, uploads, and live
  verification to the separate `lov-skill-publisher` capability.
- Infer user configuration from persistent workspace, brand, identity, output,
  locale, and provider needs instead of asking users to choose a mode.
- Remove the Skill Publisher-internal configuration branch; every source is portable
  and Skill Publisher is represented through ordinary profile values.
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

- Make synchronization to `example.com/skills` a mandatory publication step.
- Revalidate catalog, detail, cases, and user-facing routes after catalog merge.
- Require live HTTP, version, and content checks before reporting publication.

## 2.9.0

- Remove the repository-target question from the interactive creation flow.
- Remove the obsolete `--target` and `--dev-skills` scaffold arguments.
- Make `skill-publisher/{name}-skill` an unconditional source-repository invariant.
- Keep general-skills and dev-skills as inferred downstream distribution only.

## 2.8.0

- Make `skill-publisher/{name}-skill` the only supported source-repository model.
- Treat `skill-publisher/dev-skills` as a release-driven generated aggregate mirror.
- Scaffold CI, MIT license, and changelog files for every new independent skill.
- Reject the retired `--target dev-skills` mode with migration guidance.

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [2.7.0] - 2026-05-07

### Added

- make scaffold roots profile driven
- resolve source roots from SKILL_SKILL_CREATOR_* env vars or shared profile before safe fallbacks
- remove personal workspace and fixed agent runtime paths from generated templates

## [2.6.1] - 2026-05-07

### Fixed

- publish Skill Publisher skill standard reference
- add references/skill-standard.md as the canonical standardization document

## [2.6.0] - 2026-05-07

### Added

- standardize config env vars on SKILL_SKILLS namespace
- replace AGENT_SKILL_* in generated templates
- keep defaults under ${SKILLS_CONFIG_DIR}

## [2.5.0] - 2026-05-07

### Added

- move default skill profile under ~/.skill-publisher
- keep AGENT_SKILL_PROFILE as the portable override
- default generated brand/design config paths to ${SKILLS_CONFIG_DIR}

## [2.4.0] - 2026-05-07

### Added

- switch public config contract to AGENT_SKILL profile
- replace Skill Publisher-prefixed profile paths in new-skill templates
- keep Skill Publisher paths as private authoring examples, not reusable runtime API

## [2.3.0] - 2026-05-06

### Added

- add portable user configuration scaffolding
- switch new templates to Agent Skills-compatible lov-<name> frontmatter
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
- Document `repo: skill-publisher/dev-skills` + `skill_path: skills/<name>` registration and marketplace plugin updates.

## [2.0.0] - 2026-04-18

### Changed

- Rewrite for per-skill-repo architecture. Each skill is now an independent repo at `skill-publisher/{name}-skill` instead of a subdirectory of a monorepo.
- Default scaffold path: `~/skill-publisher/coding/skills/{name}-skill/` (was `skills/lov-{name}/`).
- Install hint: `git clone` each skill repo (replaces `npx skills add skill-publisher/skills`).
- `init_skill.py`: accepts `--paid`, auto-creates `.gitignore`, and prints `gh repo create` + symlink + index-registration next-steps instead of monorepo-dev-flow hints.

### Added

- Step 5b: PR to `skill-publisher/skills` central index (`skills.yaml` + `README.md`).
- Step 5d: example.com ISR cache revalidation via `skills-index` tag.
- Migration note for legacy skills still in the monorepo structure.

### Removed

- Step 0 (repo choice): `skill-publisher/pro-skills` was archived 2026-04-16. `paid` now lives only in `lov-general-skills/skills.yaml` as catalog metadata, not as a skill property.

## [1.2.0] - 2026-04-15

### Added

- Add Step 0: repo selection (skill-publisher/skills vs skill-publisher/pro-skills)
- Step 5c: create PR to chosen target repo instead of push to main

## [1.1.1] - 2026-04-14

### Fixed

- Add publish workflow: symlink chain + git push to Step 5

## [1.1.0] - 2026-04-14

### Added

- Fix init_skill.py repo detection — prefer lov-skills over cwd
- README template now includes version badge
- Remove CHANGELOG from 'What NOT to Include' (managed by skill-optimizer)
