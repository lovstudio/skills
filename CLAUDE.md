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
├── scripts/sync-runtime-names.py      # Syncs runtime_name and free-entry version from mirrored SKILL.md frontmatter
├── scripts/render-marketplace.py     # Regenerates marketplace.json from skills.yaml
├── scripts/render-readme.py          # Regenerates README skill table from skills.yaml
├── scripts/mirror-catalog-cn.py      # CI-only: uploads skills.yaml to the lovstudio.cn OSS mirror
├── scripts/validate_runs_on.py       # Rejects `runs_on` claims with no real run behind them
├── evidence/runs-on/<skill>/<id>.md  # Prompt, fixture hashes and independent checks for each recorded run
├── CHANGELOG.md                      # Index repo history (not per-skill)
├── LICENSE                           # MIT (for this index; each skill has its own LICENSE)
└── .github/workflows/                # render-readme.yml runs sync → render-marketplace → render-readme → mirror-cn
```

**Edit `skills.yaml`, not the README table or marketplace.json.** Free mirrors under `skills/` are distribution outputs. CI regenerates the catalog and free mirrors on push and nightly. You can preview locally with `SKILLS_CLONE_PROTOCOL=ssh python3 scripts/sync-skills.py && python3 scripts/render-marketplace.py && python3 scripts/render-readme.py` (SSH lets the sync clone private sources with your own key).

**lovstudio.cn reads the catalog from Aliyun OSS, not GitHub.** The `mirror-cn` job uploads `main`'s `skills.yaml` to `lovstudio-downloads/catalogs/skills.yaml` after every render (push and nightly) and checks the anonymous copy's SHA-256. It assumes an Aliyun RAM role through GitHub OIDC, so no AccessKey is stored here; the role only trusts this repo's `main` and may only put that one object. It needs the repo variables `ALIYUN_CATALOG_MIRROR_ROLE_ARN` and `ALIYUN_GITHUB_OIDC_PROVIDER_ARN` and is skipped without them. Every run re-uploads on purpose: the site treats a mirror whose Last-Modified is older than 48 hours as stale and reads GitHub first. If the job fails at the credentials step after GitHub changes its OIDC certificate chain, add the new fingerprint to the Aliyun OIDC provider (runbook: lovstudio-home `docs/deploy-lovstudio-cn.md`).

## Source Visibility and the Mirror

- **Private by default.** Create every new `lovstudio/{name}-skill` source repo as private, free or paid. A free skill never needs a public source to be installed or shown on the website: both read it from `skills/<name>/`. Paid skills never need one either: they are not mirrored, and lovstudio.ai serves owners a download of the private source.
- **`pricing.visibility` is not repo visibility.** In `skills.yaml`, `public` / `internal` decides whether the catalog lists and mirrors an entry (internal entries are never mirrored); it says nothing about the source repo's GitHub visibility.
- **Private sources need read access.** `scripts/sync-skills.py` clones with the `SKILLS_SOURCE_TOKEN` repository secret in CI and with `SKILLS_CLONE_PROTOCOL=ssh` locally. The secret is a fine-grained token owned by `lovstudio` with Contents: read-only. In CI an empty secret fails the mirror step before any clone; anonymous HTTPS could only read public sources. When you add a private source, make sure the token can read it (a token limited to selected repositories needs the new repo added). An expired, revoked or under-scoped token shows up as `Authentication failed` or `Repository not found` annotations on the private entries.
- **Keep the mirror complete.** Every free, non-internal entry in `skills.yaml` must have a full copy of its skill directory under `skills/<name>/` on `main`: `SKILL.md`, `README.md`, `skill-card.yaml` when the source has one, and the images and references they link to. The website falls back to this copy, so a gap there is a 404 or a broken image for visitors. Don't hand-delete mirrored files or add `RSYNC_EXCLUDES` patterns that drop content the docs link to.
- **A failed clone fails the run, not the catalog.** An entry whose source cannot be refreshed (clone failure, no `SKILL.md`, rsync error) keeps its last mirror. `sync-skills.py` still attempts every entry, reports each failure as an error annotation with git's message, lists them all in the job summary (a step shows only its first 10 annotations) and exits 1. The mirror step continues on error, so version sync, rendering, the bot commit and `mirror-cn` still publish the other entries; the last step, `Fail on stale mirrors`, then turns the run red. A red `Render index` run therefore means a stale mirror: read its annotations. A new entry whose clone fails gets no mirror, and `sync-runtime-names.py` still fails CI with `installable catalog entry has no mirrored SKILL.md` before anything is committed. After adding or updating a free skill, check that `skills/<name>/` on `main` matches the source.

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
    version: "0.7.1"                    # free: CI-synced from the mirror's SKILL.md metadata.version; paid/internal: hand-maintained
    updated_at: 2026-10-31 11:19:40+00:00  # last catalog update (UTC); CI restamps it when it syncs a new free version
    description: "Markdown → …"         # Agent-facing trigger copy (English, terse). CI-synced from GitHub repo description.
    tagline_en: "Typeset Markdown …"    # Human-facing English one-liner for README. Hand-maintained.
    tagline_zh: "把 Markdown 排成 …"    # Human-facing Chinese one-liner for README. Hand-maintained.
    skill_path: "skill/lov-xxx"         # OPTIONAL. Use only when SKILL.md is not at repo root.
```

### `runs_on`: can it run on my machine with my tools

Optional per-entry record that answers one question for a reader: "can I run this on my machine, with the tools I have?" lovstudio.ai leads the Skill page with it and falls back to `compatibility` and `skill-card.yaml` when an entry has none.

**The rule: a claim that something works needs a real run behind it.** Anything nobody ran stays `unverified`. Do not infer portability from the code, and do not copy a claim from a README. `scripts/validate_runs_on.py` enforces this in CI (through `scripts/test_validate_runs_on.py`), and the website enforces it again when it parses the record.

```yaml
  runs_on:
    checked_at: '2026-11-06'           # when this record was last checked
    skill_version: 0.33.0              # the version it was checked against; the page flags a newer one
    verdict_zh: 有 Apple 芯片的 Mac 能跑完……  # the per-Skill answer the page leads with
    verdict_en: ...
    systems:                           # all four, exactly once: macos-arm64, macos-intel, windows, linux
    - id: macos-arm64
      status: verified
      evidence: [messi-film]
    - id: windows
      status: unverified
      note_zh: 转写脚本只调用 mlx-whisper……   # known obstacles are facts from the source, not a verdict
      note_en: ...
    agents:                            # only what was actually tried
    - label: WorkBuddy
      model: kimi-k2.7
      domestic: true                   # no overseas model account needed
      status: partial
      evidence: [wb-kimi-review]
      gap_zh: 只跑了审校版……              # required for partial and blocked: say what is missing
      gap_en: ...
    requires:                          # [] means no extra account or key
    - name: OpenRouter API Key
      required: false
      for_zh: AI 配乐
      for_en: AI music
    alternatives:                      # optional: what stands in for a dependency, and what it costs you
    - replaces_zh: OpenRouter AI 配乐
      replaces_en: OpenRouter AI music
      with_zh: 自备无人声音乐
      with_en: Your own instrumental track
      status: verified
      evidence: [wb-kimi-review]
      gap_zh: ...
      gap_en: ...
    evidence:
    - id: wb-kimi-review
      date: '2026-11-06'
      env: macOS 26.6 arm64 · WorkBuddy CLI 2.115.0 · kimi-k2.7   # where it ran
      skill_version: 0.33.0
      result: passed                   # passed | partial | failed
      kind: run                        # run (default) | source (quotes the Skill's declaration; can only record a failure)
      scope_zh: 58 秒合成口播 → 审校版……   # what actually ran, and how it was checked
      scope_en: ...
      url: https://github.com/lovstudio/skills/blob/main/evidence/runs-on/media-creator/wb-kimi-review.md
```

| Status | Meaning | Needs |
| --- | --- | --- |
| `verified` | Ran through and passed | A cited `run` with `result: passed` |
| `partial` | Part of it ran; `gap_*` or `note_*` says what did not | A cited `run` with `result: passed` or `partial` |
| `blocked` | Does not run here | Cited evidence with `result: failed`, plus the reason |
| `unverified` | Nobody has run it | No evidence |

- **A run counts only when the Skill really ran and something other than the model checked it.** An agent can finish with a correct-looking file while skipping the Skill (one run downloaded a file with bare `curl`, another hand-rolled `ffmpeg` after failing to find the scripts). Check that the Skill was invoked, then verify the output independently: `ffprobe`, the Skill's own validator, a known transcript.
- **Evidence text is public, paid Skills included.** No local paths, no secrets, no names from private material, no script names of a paid Skill. `evidence/runs-on/<skill>/<id>.md` holds the prompt, fixture hashes and check results for a run; never commit raw transcripts.
- **Only name a model you saw in the run's own log.** When a case does not record its agent or model, it can back a `systems` row but not an `agents` row.
- Bumping a Skill does not invalidate its record: the page shows that the evidence comes from an older version. Re-run when a dependency or a gated step changes.

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
- **`version` / `updated_at`** — for free entries, CI copies `version` from the mirrored
  `SKILL.md` (`metadata.version`, else a top-level `version`) and, only when the value
  changes, stamps `updated_at` with the sync time as `YYYY-MM-DD HH:MM:SS+00:00`.
  lovstudio.ai dates and ranks Skill updates by `updated_at` and skips GitHub history for
  entries that have one, so a version bump without a fresh stamp never shows up as an update.
  Paid and internal entries are not mirrored: bump both fields by hand when releasing.
- **Paid skills**: `tagline_*` must not leak implementation specifics (no library names,
  no auth/token mechanics, no internal endpoints) — they sit in a public index.

## Key Conventions

- **`paid` field is only here**, not in individual SKILL.md files. It's business classification, not skill metadata.
- **Current totals live in `skills.yaml`** — the README count line is auto-rendered, so don't hand-edit it. See `scripts/render-readme.py`.
- **Naming**: an entry is either a local `skills/<name>/` mirror or an independent GitHub repo `lovstudio/{name}-skill`; no runtime prefix belongs in the catalog `name`.
- Users install with the short catalog name (`any2pdf`); installers and Agents use the explicit `runtime_name` (`lov-any2pdf`).

## Adding a New Skill

1. In `~/lovstudio/skills/`: run the [`skill-creator`](https://github.com/lovstudio/skill-creator-skill) skill to scaffold `{name}-skill/`.
2. `cd {name}-skill && git init && git add -A && git commit && gh repo create lovstudio/{name}-skill --private --source=. --push`, then confirm `SKILLS_SOURCE_TOKEN` can read the new repo; otherwise the next `Render index` run fails on it.
3. Open a PR against this repo appending an entry to `skills.yaml`. **Don't touch the README table** — CI regenerates it from the manifest.
4. After the catalog CI run on `main`, confirm `skills/<name>/` holds the complete skill directory (free skills), since the website renders private-source free skills from it.

For **paid** skills: set `paid: true`. The source repo stays private, nothing is mirrored here, and step 4 does not apply.

## Historical Context

This repo used to be a monorepo containing all skills under `skills/lovstudio-<name>/`. In 2026-04-16 it was refactored into a pure index + 27 independent skill repos. The old `lovstudio/pro-skills` repo (which mirrored free + added 3 paid skills) was archived at the same time. See the 0.8.0 CHANGELOG entry.

## Cross-session Notes

- `skills.yaml` 里含 `: ` 的 description 必须加引号，否则 CI 的 `yaml.safe_load` 直接 ScannerError（2026-08-18, e32d199）
- 官网 revalidate 的 secret 环境变量名是 `LOVSTUDIO_REVALIDATE_SECRET`（publisher 文档里的 `SKILL_REVALIDATE_SECRET` 已过时），curl 用 `x-revalidate-secret` header 直接读该变量（2026-08-20, 18bc301）
- `sync-skills.py` 全量 sync 80+ 免费 skill 会 >120s；本地只新增单个 skill 时，手动 `rsync -a --delete --exclude .git <源目录>/ skills/<name>/` 即可，不必全量跑（2026-08-20, 18bc301）
