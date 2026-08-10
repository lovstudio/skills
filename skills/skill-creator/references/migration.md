# Migration Notes

## 2026-08: v4 local creation and separate publishing

`sgc-skill-creator` now ends at validated local installation. Remove
`--distribution`, `--paid`, platform directories, marketplace builders, remote
repository commands, catalog registration, and live-channel verification from
creation workflows. Use `--user-config` only when inferred persistent settings
are required and pass `--install-dir` for local discovery.

Existing platform packaging and release workflows move to
`sgc-skill-publisher`. Historical sections below describe older layouts and
remain only for migration audits.

## 2026-07: v3 source/distribution split

New scaffolds keep portable Agent Skills frontmatter in the canonical source
and generate marketplace-only fields into distribution copies.

When migrating an existing Skill:

1. Move top-level `compatibility` and `depends_on` under `metadata`.
2. Keep source top-level keys to `name`, `description`, `license`,
   `allowed-tools`, and `metadata`.
3. Add explicit `## Triggers`, activation phrases, and non-trigger conditions.
4. Keep the Skill description between 50 and 200 characters.
5. Convert controller/sibling relationships into a self-contained `kit.yaml`
   plus embedded `skills/<module>/SKILL.md` paths.
6. Add WorkBuddy metadata with `--distribution workbuddy` or copy the generated
   profile from a fresh scaffold.
7. Run `scripts/validate_skill.py` before rebuilding releases.

Do not copy WorkBuddy `version`, `author`, or source-location fields back into
the canonical source frontmatter. The platform builder injects them.

## 2026-07: one source path, no repository-target prompt

The creator no longer exposes `--target`, `--dev-skills`, or a repository
choice in the interactive flow. Every scaffold is created as the source for
`lovstudio/<name>-skill`.

General-skills and dev-skills are downstream distribution indexes. Register
them after the independent repo is released; do not treat either catalog as a
scaffold destination.

## 2026-07: independent sources with a generated dev-skills aggregate

Every skill now has one source of truth: `lovstudio/<name>-skill`. Free Meta /
Dev Tools skills may be listed in `lovstudio/dev-skills`, whose checked-in
skill directories are generated from the latest GitHub Releases.

Do not use `--target dev-skills` and do not edit aggregate mirror directories
as source. Create and release the independent repo, register it in
`independent-skills.json` and `skills.yaml`, then let the sync workflow update
the mirror.

## 2026-05: dev-skills aggregate target (superseded)

The direct-source aggregate model below is retained only as historical context
and must not be used for new work:

```bash
python3 ~/.claude/skills/sgc-skill-creator/scripts/init_skill.py tanstack-query --target dev-skills
```

The skill directory is:

```text
~/lovstudio/coding/sgc-dev-skills/skills/tanstack-query/
```

`skills.yaml` must include:

```yaml
repo: lovstudio/dev-skills
skill_path: skills/tanstack-query
```

## 2026-04: independent per-skill repos

The ecosystem was refactored from a monorepo (`lovstudio/skills` containing
`skills/sgc-<name>/`) + mirror (`lovstudio/pro-skills`) into independent
per-skill repos + central index. The old `lovstudio/pro-skills` was archived.

If working on a legacy skill still in the old structure, migrate it first:

```bash
# 1. Extract from monorepo subdirectory
cp -r ~/projects/sgc-skills/skills/sgc-<name> \
      ~/lovstudio/coding/skills/<name>-skill
cd ~/lovstudio/coding/skills/<name>-skill

# 2. Fresh git history
rm -rf .git
git init && git add -A && git commit -m "import: <name> from monorepo"

# 3. Create independent repo
gh repo create lovstudio/<name>-skill --public --source=. --push
```
