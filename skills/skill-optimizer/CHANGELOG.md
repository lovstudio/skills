# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [0.6.3] - 2026-05-07

### Fixed

- avoid CJK false positives for image-only helpers
- limit document CJK hints to scripts that actually render text

## [0.6.2] - 2026-05-07

### Fixed

- remove local path examples from optimizer docs
- refresh publish sync instructions for source plus general/dev catalog repos

## [0.6.1] - 2026-05-07

### Fixed

- recognize lovstudio CLI install commands
- treat npx lovstudio skills add as the canonical README install surface

## [0.6.0] - 2026-05-07

### Added

- recognize LOVSTUDIO_SKILLS config namespace
- recognize LOVSTUDIO_MAINTAIN_PARTNERS skill-specific config cues
- treat AGENT_SKILL and PARTNERS env names as legacy migration cues

## [0.5.0] - 2026-05-07

### Added

- recognize generic AGENT_SKILL config cues
- keep LOVSTUDIO_* only as legacy compatibility cues

## [0.4.0] - 2026-05-06

### Added

- add repo-wide portability audit
- flag hard-coded local paths and legacy skill names
- support --all --root scans across skill directories
- ignore negative examples such as "do not hard-code /Users/mark" when checking required local paths

## [0.3.0] - 2026-04-16

### Added

- Add multi-repo sync in Step 7: source → pro-skills → ~/.claude/skills
- Document 3-location topology (source, symlink, distribution)
- Step 7b: auto-sync lovstudio/pro-skills via skills-upstream remote
- Fail-loud on partial sync instead of silent skip

## [0.2.0] - 2026-04-14

### Added

- Add Step 7: auto commit & push after optimization
- Update README pipeline diagram to include git push step

## [0.1.0] - 2026-04-10

### Added

- initial release: lint + auto-bump + changelog pipeline
- lint_skill.py audits frontmatter, README badge, scripts, structure
- bump_version.py maintains README badge, SKILL.md version, CHANGELOG.md
