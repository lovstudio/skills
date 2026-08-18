# CLAUDE.md

Guidance for Claude Code when working in this repo.

## What This Is

The **central index** for Lovstudio skills. The source of truth for each skill is its own repo at `github.com/lovstudio/{name}-skill`. Locally, skills are developed under `~/lovstudio/coding/skills/{name}-skill/`.

This index repo also carries a **read-only mirror** of every free skill under `./skills/<name>/` and encrypted distribution bundles for paid skills. The mirror exists so that the `npx skills add lovstudio/skills` discovery flow (used internally by the `lovstudio` CLI) can find every skill in a single clone — that flow only resolves local paths in `.claude-plugin/marketplace.json`, not external `github` sources.

## Repo Layout

```
.
├── README.md / README.en.md          # Human-readable catalog (CI-rendered between SKILLS:START/END)
├── skills.yaml                       # Machine-readable manifest — SOURCE OF TRUTH
├── skills/<name>/                    # Free mirrors or encrypted paid bundles (generated distribution content)
├── .claude-plugin/marketplace.json   # Claude Code marketplace manifest (auto-rendered)
├── scripts/sync-skills.py            # Mirrors each free repo into ./skills/<name>/ (shallow clone + rsync)
├── scripts/render-marketplace.py     # Regenerates marketplace.json from skills.yaml
├── scripts/render-readme.py          # Regenerates README skill table from skills.yaml
├── CHANGELOG.md                      # Index repo history (not per-skill)
├── LICENSE                           # MIT (for this index; each skill has its own LICENSE)
└── .github/workflows/                # render-readme.yml runs sync → render-marketplace → render-readme
```

**Edit `skills.yaml`, not the README table or marketplace.json.** Free mirrors and paid bundles under `skills/` are distribution outputs. CI regenerates the catalog and free mirrors on push and nightly. You can preview locally with `python3 scripts/sync-skills.py && python3 scripts/render-marketplace.py && python3 scripts/render-readme.py`.

## How users install

**Canonical surface — always advertise this form:**

```bash
npx lovstudio skills add <name>                                      # free: direct install
npx lovstudio skills add skills                                      # all free skills
npx lovstudio skills add <paid-name>                                # paid: sign in + Credits redemption
```

`npx lovstudio` (the `lovstudio` npm package, lovstudio-cli repo) is a thin wrapper:
- `lovstudio skills add` resolves the unified `lovstudio/skills` catalog, gates paid entries through account sign-in and Credits redemption, then shells out to the underlying Skills installer.
- Paid bundles remain encrypted on disk; the helper requests a decryption key only after the account entitlement is verified.

Both underlying CLIs still work and remain the actual implementation. **Do not advertise them in user-facing docs** — only `npx lovstudio` should appear in READMEs, SKILL.md, marketplace blurbs, blog posts, agentskills.io listings, etc.

`-g -y` are non-negotiable in AI/CI/non-TTY contexts because the underlying CLI opens three `@clack/prompts` interactive selectors (skills → agents → confirm) and hangs without a TTY.

The native Claude Code marketplace path (`/plugin marketplace add lovstudio/skills` then `/plugin install <name>@lovstudio`) still works off `.claude-plugin/marketplace.json`, but treat it as a fallback — `npx lovstudio` is the path we promote.

## skills.yaml Schema

```yaml
version: 1
skills:
  - name: any2pdf                       # skill short name (no prefix)
    repo: lovstudio/any2pdf-skill       # GitHub repo (always lovstudio/{name}-skill)
    paid: false                         # true = private repo + purchase required
    category: "Document Conversion"     # display category
    version: "0.7.1"                    # from SKILL.md (optional, CI-synced)
    description: "Markdown → …"         # Agent-facing trigger copy (English, terse). CI-synced from GitHub repo description.
    tagline_en: "Typeset Markdown …"    # Human-facing English one-liner for README. Hand-maintained.
    tagline_zh: "把 Markdown 排成 …"    # Human-facing Chinese one-liner for README. Hand-maintained.
    skill_path: "skill/lov-xxx"         # OPTIONAL. Use only when SKILL.md is not at repo root.
```

### Field responsibilities

- **`description`** — read by Claude Code / Agents to decide when to trigger the skill.
  Keep it professional, English, and terse (Agents have a skills-token budget).
  CI pulls this from each skill's GitHub repo description nightly (`GH_SYNC=1`) — so the repo
  description on GitHub is the source of truth; don't hand-edit this field as marketing copy.
- **`tagline_en` / `tagline_zh`** — shown to humans in README.md / README.zh-CN.md and on
  agentskills.io. Value-oriented ("what the user gets"), NOT implementation details.
  Hand-maintained — CI never overwrites them.
- **Paid skills**: `tagline_*` must not leak implementation specifics (no library names,
  no auth/token mechanics, no internal endpoints) — they sit in a public index.

## Key Conventions

- **`paid` field is only here**, not in individual SKILL.md files. It's business classification, not skill metadata.
- **Current totals live in `skills.yaml`** — the README count line is auto-rendered, so don't hand-edit it. See `scripts/render-readme.py`.
- **Naming**: an entry is either a local `skills/<name>/` mirror or an independent GitHub repo `lovstudio/{name}-skill`; no `lovstudio-` prefix in the catalog name.
- Skill short name (`any2pdf`) is what users invoke via `lov-any2pdf` in Claude Code.

## Adding a New Skill

1. In `~/lovstudio/skills/`: run the [`skill-creator`](https://github.com/lovstudio/skill-creator-skill) skill to scaffold `{name}-skill/`.
2. `cd {name}-skill && git init && git add -A && git commit && gh repo create lovstudio/{name}-skill --public --source=. --push`
3. Open a PR against this repo appending an entry to `skills.yaml`. **Don't touch the README table** — CI regenerates it from the manifest.

For **paid** skills: pass `--private` to `gh repo create` and set `paid: true`.

## Historical Context

This repo used to be a monorepo containing all skills under `skills/lovstudio-<name>/`. In 2026-04-16 it was refactored into a pure index + 27 independent skill repos. The old `lovstudio/pro-skills` repo (which mirrored free + added 3 paid skills) was archived at the same time. See the 0.8.0 CHANGELOG entry.

## Cross-session Notes

- `skills.yaml` 里含 `: ` 的 description 必须加引号，否则 CI 的 `yaml.safe_load` 直接 ScannerError（2026-08-18, e32d199）
