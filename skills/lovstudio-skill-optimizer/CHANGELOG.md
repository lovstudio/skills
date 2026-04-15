# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

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

