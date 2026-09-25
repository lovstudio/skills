# Skill Group Composition

This record is required for every generated Skill. It prevents adjacent Skills
from becoming accidental duplicates or hidden dependencies.

## Nearby Skills Inspected

- `baoyu-markdown-to-html` — converts Markdown to a single HTML file. Renders a
  document *on disk*; does not read an agent session, normalize transcript roles
  / display levels, or talk to a hosted Lover share endpoint. **Not composed**.
- `lov-any2pdf` / `lov-any2docx` / `lov-any2deck` — turn content into a local
  PDF / DOCX / deck file. Local file output, no session concept, no web URL.
  **Not composed** (downstream of *content*, but no handoff for a live session).
- `lov-rich-export` — exports a session/Markdown into a local rich file. Its
  output is a file, not a shareable hosted page. **Overlap** on the *reading a
  session* step but diverges: this Skill's whole point is a hosted URL.
- `lov-deploy-to-vercel` / `lov-app-release` — deploy an app or site. This Skill
  does not deploy anything; the hosted page already lives and renders on
  lovstudio.ai. **Not composed**.
- `lov-deep-research` / `lov-wechat-*` — content generation and publishing to
  WeChat. No session-transcript-to-public-page contract. **Not composed**.
- Yoda's own in-app `app-tab-context-menu` → `rpc.sessionShares.create` — the
  *inspiration* for this Skill. It is hosted inside Yoda (POST to the same web
  endpoint, needs the Yoda runtime + its encrypted keychain token). This Skill
  replicates that outcome **without** a Yoda runtime: it reads any agent session
  and authenticates via the public device-flow. **Overlap in outcome, reused as
  design reference; not a runtime dependency.**

## Atomic Handoffs

- **Core atom**: `lov-share-session` reads an agent session transcript (Claude
  Code JSONL / Yoda JSON / markdown), normalizes it to the strict
  `yodaSessionShareUpload` schema, authenticates to lovstudio.ai, and POSTs to
  `/api/yoda/session-shares`. Output = a free public or paid hosted URL. This Skill owns that
  user-visible outcome end to end.
- **Upstream (optional, external)**: any harness that exports a session file
  (Claude Code `--file`, Yoda conversation JSON). Handoff artifact = a
  transcript file, ownership stays with the caller. Not a hard dependency —
  the Skill auto-detects the current session on its own.
- **Downstream (optional)**: after obtaining the URL, a user may want to crop a
  cover / card via `lov-any2deck` or `lov-wechat-*`, but that is a separate
  user intent, not part of "make a shareable page". No hard coupling.
- **Downstream (declared caller)**: `lov-skill-add-case` passes a target Skill ID
  and case ID. This Skill returns a paid Session URL and the authoritative Credits
  price (`ceil(target Skill price / 10)`). It never accepts a client price.
- **No hidden sibling dependencies**: the Skill is self-contained (single Python
  CLI + references). It does not import or shell out to any sibling Skill.

## Overlap Decisions

- Reuses Yoda's exact upload schema + display-level semantics so the resulting
  URL is interchangeable with a Yoda-generated share — but does **not** call
  Yoda's `rpc.sessionShares.create` (requires Electron + keychain token).
- Kept separate from `lov-rich-export` (file output) and `baoyu-markdown-to-html`
  (document render) because the deliverable — a live hosted URL — is materially
  different from a local file. No duplication of code; overlap is conceptual.

## Composition Decision

**Single Skill.** One outcome ("turn a session into a hosted LovStudio URL") with
one deterministic local transform (normalize + POST) plus a small auth helper.
No independently useful stages that each deserve their own input/output contract
readable by a user, so a Skill Kit would be over-engineering. The auth step is
internal plumbing, not a separately triggerable deliverable.
