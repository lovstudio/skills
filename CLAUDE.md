# CLAUDE.md

Guidance for Claude Code when working in this repo.

## What This Is

The **central index** for Lovstudio skills. The source of truth for each skill is its own repo at `github.com/lovstudio/{name}-skill`; new source repos are **private by default**, free and paid alike. Locally, skills are developed under `~/lovstudio/coding/skills/{name}-skill/`.

This index repo also carries a **read-only mirror** of every free, non-internal skill under `./skills/<name>/`. Paid skills are never mirrored: their source repos are private and lovstudio.ai hands out a download only to accounts that own them. The mirror is the public copy of each free skill and has two consumers:

- **Installer** — the `npx skills add lovstudio/skills` discovery flow (used internally by the `lovstudio` CLI) finds every skill in a single clone; that flow only resolves local paths in `.claude-plugin/marketplace.json`, not external `github` sources.
- **Website** — lovstudio.ai renders a free skill's detail page and cases from its source repo when that repo is publicly readable, and otherwise falls back to `lovstudio/skills/main/skills/<name>/` (`SKILL.md`, `README.md`, `skill-card.yaml`, with relative images and links resolved inside the mirror).

For a free skill with a private source, the mirror is therefore its only public display and install surface. See [Source Visibility and the Mirror](#source-visibility-and-the-mirror).

## Repo Layout

```
.
├── README.md / README.en.md          # Human-readable catalog (CI-rendered between SKILLS:START/END)
├── skills.yaml                       # Machine-readable manifest — SOURCE OF TRUTH
├── skills/<name>/                    # Free mirrors (generated distribution content)
├── .claude-plugin/marketplace.json   # Claude Code marketplace manifest (auto-rendered)
├── scripts/sync-skills.py            # Mirrors each free repo into ./skills/<name>/ (shallow clone + rsync)
├── scripts/sync-runtime-names.py      # Syncs runtime_name from mirrored SKILL.md frontmatter
├── scripts/render-marketplace.py     # Regenerates marketplace.json from skills.yaml
├── scripts/render-readme.py          # Regenerates README skill table from skills.yaml
├── CHANGELOG.md                      # Index repo history (not per-skill)
├── LICENSE                           # MIT (for this index; each skill has its own LICENSE)
└── .github/workflows/                # render-readme.yml runs sync → render-marketplace → render-readme
```

**Edit `skills.yaml`, not the README table or marketplace.json.** Free mirrors under `skills/` are distribution outputs. CI regenerates the catalog and free mirrors on push and nightly. You can preview locally with `SKILLS_CLONE_PROTOCOL=ssh python3 scripts/sync-skills.py && python3 scripts/render-marketplace.py && python3 scripts/render-readme.py` (SSH lets the sync clone private sources with your own key).

## Source Visibility and the Mirror

- **Private by default.** Create every new `lovstudio/{name}-skill` source repo as private, free or paid. A free skill never needs a public source to be installed or shown on the website: both read it from `skills/<name>/`. Paid skills never need one either: they are not mirrored, and lovstudio.ai serves owners a download of the private source.
- **`pricing.visibility` is not repo visibility.** In `skills.yaml`, `public` / `internal` decides whether the catalog lists and mirrors an entry (internal entries are never mirrored); it says nothing about the source repo's GitHub visibility.
- **Private sources need read access.** `scripts/sync-skills.py` clones with `SKILLS_SOURCE_TOKEN` in CI and with `SKILLS_CLONE_PROTOCOL=ssh` locally. When you add a private source, make sure that token can read it.
- **Keep the mirror complete.** Every free, non-internal entry in `skills.yaml` must have a full copy of its skill directory under `skills/<name>/` on `main`: `SKILL.md`, `README.md`, `skill-card.yaml` when the source has one, and the images and references they link to. The website falls back to this copy, so a gap there is a 404 or a broken image for visitors. Don't hand-delete mirrored files or add `RSYNC_EXCLUDES` patterns that drop content the docs link to.
- **A failed clone does not fail the sync.** The entry keeps its last mirror, which then goes stale without an error; a new entry gets no mirror, and `sync-runtime-names.py` fails CI with `installable catalog entry has no mirrored SKILL.md`. After adding or updating a free skill, check that `skills/<name>/` on `main` matches the source.

## How users install

**Canonical surface — always advertise this form:**

```bash
npx lovstudio skills add <name>                                      # free: direct install
npx lovstudio skills add skills                                      # all free skills
npx lovstudio skills add <paid-name>                                # paid: sign in + Credits redemption
```

`npx lovstudio` (the `lovstudio` npm package, lovstudio-cli repo) is a thin wrapper:
- `lovstudio skills add` resolves the unified `lovstudio/skills` catalog, gates paid entries through account sign-in and Credits redemption, then shells out to the underlying Skills installer.
- Paid Skills are not encrypted. After ownership is confirmed (Credits purchase or a license bound to the account), the CLI asks `lovstudio.ai/api/skills/download` for a short-lived archive of the private source repo and installs it as plain files. Paying controls who can download, nothing else.

Both underlying CLIs still work and remain the actual implementation. **Do not advertise them in user-facing docs** — only `npx lovstudio` should appear in READMEs, SKILL.md, marketplace blurbs, blog posts, agentskills.io listings, etc.

`-g -y` are non-negotiable in AI/CI/non-TTY contexts because the underlying CLI opens three `@clack/prompts` interactive selectors (skills → agents → confirm) and hangs without a TTY.

The native Claude Code marketplace path (`/plugin marketplace add lovstudio/skills` then `/plugin install <name>@lovstudio`) still works off `.claude-plugin/marketplace.json`, but treat it as a fallback — `npx lovstudio` is the path we promote.

## skills.yaml Schema

```yaml
version: 1
skills:
  - name: any2pdf                       # skill short name (no prefix)
    runtime_name: lov-any2pdf           # exact SKILL.md frontmatter name used by installers/runtimes
    repo: lovstudio/any2pdf-skill       # GitHub repo (always lovstudio/{name}-skill)
    paid: false                         # true = purchase-gated download from lovstudio.ai, never mirrored here
    category: "Document Conversion"     # display category
    version: "0.7.1"                    # from SKILL.md (optional, CI-synced)
    description: "Markdown → …"         # Agent-facing trigger copy (English, terse). CI-synced from GitHub repo description.
    tagline_en: "Typeset Markdown …"    # Human-facing English one-liner for README. Hand-maintained.
    tagline_zh: "把 Markdown 排成 …"    # Human-facing Chinese one-liner for README. Hand-maintained.
    skill_path: "skill/lov-xxx"         # OPTIONAL. Use only when SKILL.md is not at repo root.
```

### Field responsibilities

- **`name_zh` / `display_name`** — Chinese and English product names. Prefer
  short, memorable names and preserve user-approved choices. Functional, role
  and metaphor names are all valid; keep task-defining platform names and omit
  creator/studio prefixes. Runtime IDs, installation slugs and paths remain
  separate. `sync-skills.py` applies these labels to mirrored display surfaces;
  `module-display-names.yaml` supplies names for embedded modules without
  creating standalone catalog listings.
- **`description`** — read by Claude Code / Agents to decide when to trigger the skill.
  Keep it professional, English, and terse (Agents have a skills-token budget).
  CI pulls this from each skill's GitHub repo description nightly (`GH_SYNC=1`) — so the repo
  description on GitHub is the source of truth; don't hand-edit this field as marketing copy.
- **`tagline_en` / `tagline_zh`** — shown to humans in README.md / README.zh-CN.md and on
  agentskills.io. Value-oriented ("what the user gets"), NOT implementation details.
  Hand-maintained — CI never overwrites them.
- **`runtime_name`** — exact `name` from the mirrored `SKILL.md` frontmatter. The
  catalog slug and runtime identifier are separate contracts; CI synchronizes and
  validates this field instead of guessing a prefix.
- **Paid skills**: `tagline_*` must not leak implementation specifics (no library names,
  no auth/token mechanics, no internal endpoints) — they sit in a public index.

## Key Conventions

- **`paid` field is only here**, not in individual SKILL.md files. It's business classification, not skill metadata.
- **Current totals live in `skills.yaml`** — the README count line is auto-rendered, so don't hand-edit it. See `scripts/render-readme.py`.
- **Naming**: an entry is either a local `skills/<name>/` mirror or an independent GitHub repo `lovstudio/{name}-skill`; no runtime prefix belongs in the catalog `name`.
- Users install with the short catalog name (`any2pdf`); installers and Agents use the explicit `runtime_name` (`lov-any2pdf`).

## Adding a New Skill

1. In `~/lovstudio/skills/`: run the [`skill-creator`](https://github.com/lovstudio/skill-creator-skill) skill to scaffold `{name}-skill/`.
2. `cd {name}-skill && git init && git add -A && git commit && gh repo create lovstudio/{name}-skill --private --source=. --push`, then confirm `SKILLS_SOURCE_TOKEN` can read the new repo.
3. Open a PR against this repo appending an entry to `skills.yaml`. **Don't touch the README table** — CI regenerates it from the manifest.
4. After the catalog CI run on `main`, confirm `skills/<name>/` holds the complete skill directory (free skills), since the website renders private-source free skills from it.

For **paid** skills: set `paid: true`. The source repo stays private, nothing is mirrored here, and step 4 does not apply.

## Historical Context

This repo used to be a monorepo containing all skills under `skills/lovstudio-<name>/`. In 2026-04-16 it was refactored into a pure index + 27 independent skill repos. The old `lovstudio/pro-skills` repo (which mirrored free + added 3 paid skills) was archived at the same time. See the 0.8.0 CHANGELOG entry.

## Cross-session Notes

- `skills.yaml` 里含 `: ` 的 description 必须加引号，否则 CI 的 `yaml.safe_load` 直接 ScannerError（2026-08-18, e32d199）
- 官网 revalidate 的 secret 环境变量名是 `LOVSTUDIO_REVALIDATE_SECRET`（publisher 文档里的 `SKILL_REVALIDATE_SECRET` 已过时），curl 用 `x-revalidate-secret` header 直接读该变量（2026-08-20, 18bc301）
- `sync-skills.py` 全量 sync 80+ 免费 skill 会 >120s；本地只新增单个 skill 时，手动 `rsync -a --delete --exclude .git <源目录>/ skills/<name>/` 即可，不必全量跑（2026-08-20, 18bc301）
