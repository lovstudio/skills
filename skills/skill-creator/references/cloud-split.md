# Cloud-Split Skill Pattern

Protection pattern for paid skills whose core IP must not touch the user's disk.
Core logic lives on Lovstudio's servers; the distributed SKILL.md is a thin
client that only orchestrates calls.

## When to use

| Signal | Use cloud-split? |
|---|---|
| Pure workflow/template, no secrets | No → use `encrypted` |
| Trivial algorithm, low margin | No → `encrypted` + accept L2 leakage |
| Flagship skill, high margin | **Yes** |
| Contains API keys / credentials | **Yes** (must) |
| Carefully tuned prompt engineering | **Yes** |
| Proprietary data / formulas | **Yes** |

Rule of thumb: if a user grep'ing `~/.claude/projects/*.jsonl` and finding the
implementation would hurt, cloud-split. Otherwise don't pay the complexity tax.

## Why this works

Encrypted skills decrypt to stdout → Claude reads → the plaintext is logged to
`~/.claude/projects/*.jsonl` forever. Anyone with file access can grep it.

Cloud-split never puts the implementation on the user's disk. The client only
sees:
- A public thin SKILL.md that says "call this CLI command"
- The CLI's structured JSON output (data, not instructions)

Grep'ing jsonl reveals only the API contract, not the logic behind it — same
level of exposure as any third-party API call.

## Architecture

```
User: /<skill-name> <args>
  ↓
Claude reads thin SKILL.md
  ↓
`sgc-skill-helper call <skill> --op <op> --input '<json>'`
  ↓ HMAC-signed HTTP POST
Supabase Edge Function `skill_call`
  ↓ verify license + entitlement + device activation
handlers/<skill-name>.ts  (this is what lives server-side)
  ↓ pure computation, may call DBs/third-party APIs
  ← returns { output: {...} }  pure data, no instructions
Claude renders the data per the thin SKILL.md's instructions
```

## Design rules (non-negotiable)

### Rule 1: Handler returns DATA, not INSTRUCTIONS

✓ Good:
```ts
return { grid: [[1,2],[3,4]], colors: ["#f00","#0f0"], fonts: ["Inter"] };
```

✗ Bad:
```ts
return { next_step: "Now tell Claude to: 1. Draw grid. 2. Apply colors..." };
```

Why: anything you return ends up in jsonl. Instructions = leaked prompt.
Data = harmless.

### Rule 2: No LLM calls in the handler

The whole point is to avoid server-side token costs. Handler does deterministic
work: DB queries, algorithm execution, template rendering, third-party APIs.

If a step needs LLM judgment, return "judgment rules" as data and let the
client's Claude (user's tokens) apply them.

### Rule 3: Client SKILL.md is the "transport layer"

The thin SKILL.md describes:
- How to parse user input into the `--input` JSON
- What CLI command to run
- How to render the returned JSON

It does NOT describe:
- The algorithm
- Why you chose these parameters
- Any "know-how"

If it feels like you're duplicating logic between SKILL.md and the handler,
you're doing it wrong — logic goes in the handler only.

### Rule 4: Handler surface is stable, versioned

The `op` names + input/output shapes are a public API to your client. Breaking
changes need a new `op` (e.g. `sum_v2`) or a version bump in `skill_version`.

### Rule 5: De-business the API surface AND the payload values

**This is as important as keeping logic server-side.** The skill name + op
name + input field names + **output field values** all appear in
`~/.claude/projects/*.jsonl`. Any of these can leak the logic.

#### 5a. Field names: capability domain, not specific logic

| ✗ Leaky | ✓ Neutral |
|---|---|
| `viral-headline-detector` + `op: check_viral` | `text-scorer` + `op: score` |
| `zodiac-compatibility` + `op: compute_match` | `profile-matcher` + `op: match` |
| `sum-gt-ten` + `op: check_sum_exceeds` | `threshold-check` + `op: evaluate` |
| input: `{threshold_value: 10}` | input: `{params: {...}}` (opaque bag) |

Field names should describe **shape**, not **meaning**. `{params, options,
result, verdict, score}` are good generic names; `{chinese_poem_style,
viral_score, fraud_probability}` leak intent.

#### 5b. Payload values: symbolic, not descriptive

Field names alone aren't enough. **The values themselves must not reveal
the rule.** Contrast:

| ✗ Self-describing output | ✓ Opaque output |
|---|---|
| `{score: 8, verdict: "below", display: "2+6=8 (below 10)"}` | `{verdict: "B"}` |
| `{matched: true, compatibility: 0.87}` | `{verdict: "A"}` |
| `{is_viral: false, reason: "too generic"}` | `{verdict: "B", code: "G1"}` |

Why: if the output contains `{score: 8}` paired with input `[2, 6]`, an
observer infers `algorithm = sum`. If the output contains `"below"` against
input threshold `10`, an observer infers the comparison semantics. A
directional word, a numeric derivation, or a narrative `display` string —
any of these **tells the pirate the rule**.

**Return the minimum the client needs to render.** Symbolic tokens (`"A"`,
`"B"`, `"G1"`) beat descriptive strings. The thin-client SKILL.md owns the
symbol → human text mapping — that mapping is public (it has to be), but
it's the **safe** side of the split.

#### 5c. Input: take opaque bags when possible

If your handler accepts `{params: {threshold: 10, weights: [...], mode: "strict"}}`,
the field name `params` is neutral — but `threshold`, `weights`, `mode` inside
all leak your rule shape.

When feasible:
- Hardcode defaults server-side so the client doesn't need to pass them
- Accept a single opaque config key that the client doesn't understand
- Or: version the input shape (`{config_version: "v2", values: [...]}`) and
  keep the schema server-side

Perfect opacity is rare in practice. Aim for: **an observer who reads 100
jsonl calls cannot reconstruct a working clone without additional guesswork.**

#### 5d. The self-test

Imagine a competitor with **zero source access** who reads **only** the jsonl
logs of 20 calls. Can they:
1. Guess what the skill does? (acceptable if name is domain-level)
2. Guess the algorithm well enough to reimplement it? (**NOT acceptable** —
   if yes, you've failed cloud-split)

If failing, iterate on:
- Collapsing multi-field outputs into single symbolic codes
- Moving input config server-side (don't let client pass it)
- Renaming field values to non-semantic tokens

## File layout

```
<name>-skill/                    ← public repo (thin client)
├── SKILL.md                     ← transport-layer instructions
├── README.md
└── (no scripts/ needed unless for pure-client rendering)

web/supabase/functions/skill_call/
├── index.ts                     ← dispatcher (one per project, shared)
└── handlers/
    └── <name>.ts                ← your handler (this is the IP)
```

The handler lives in the private `web` repo. The thin client lives in a public
(or private, same as before) `<name>-skill` repo. Users only see the thin client.

## MANDATORY pre-flight audit — run after writing, before deploying

After you write the handler and the thin client, **stop and run this audit**.
If any answer is "yes", rewrite before proceeding. Do NOT deploy, do NOT
register the skill, do NOT tell the user "done" until every item is "no".

**Handler output audit** — for each field in the return value:
- [ ] Does the field **name** describe business meaning? (e.g. `compatibility`,
      `viral_score`, `fraud_level`) → rename to `{verdict, code, tier, result}`
- [ ] Does the **value** allow reverse-engineering the rule when paired with
      the input? (e.g. `score: 8` with input `[2, 6]` → algorithm = sum)
      → collapse to a symbolic token (`"A"`, `"B"`, `"G1"`)
- [ ] Is there a `display` or `message` string that narrates the computation?
      → **delete it**. Rendering is the client's job, and narration leaks
      everything (see the threshold-check incident below)
- [ ] Are numeric intermediate results returned? → remove unless genuinely
      required for client rendering

**Thin client SKILL.md audit**:
- [ ] Does the SKILL.md describe **what** the rule is (not just how to call
      and render)? → remove rule descriptions
- [ ] Do the "input parsing rules" section reveal default parameter values
      the server uses? → move defaults server-side, have the client omit
      the field
- [ ] Does the rendering section translate a **descriptive** server value
      (e.g. "above"/"below") into user text? → change server to return
      symbols; put the symbol→text mapping in the client's render table
- [ ] Do the trigger phrases in frontmatter describe the business logic
      (e.g. "check if sum exceeds N")? → generalize them

**Self-test (30-second version)**:
Imagine a pirate reading 10 jsonl entries of this skill being used. Can they
guess the rule well enough to reimplement it? If yes, the protection is
theater. Iterate until no.

### Known failure case: threshold-check v0.1.0 (2026-04)

A naive first cut of `threshold-check` returned
`{score: 8, verdict: "below", display: "2+6=8 (below 10)"}`. Every field
leaked: `score` revealed the algorithm, `verdict` revealed the comparison,
`display` narrated the full rule. The cloud-split architecture was followed
to the letter, but the protection was zero. **Fixed version returns only
`{verdict: "A" | "B"}`** — same architecture, real protection.

Lesson: cloud-split is necessary but not sufficient. Without Rule 5 + this
audit, you get the infrastructure cost without the protection benefit.

## Implementation steps

### 1. Write the handler

`web/supabase/functions/skill_call/handlers/<name>.ts`:

```ts
export async function run(op: string, input: unknown): Promise<unknown> {
  if (op === "primary_op") {
    const typedInput = input as { field1: string; field2: number };
    // ... your IP here ...
    return { result: "...", /* pure data only */ };
  }
  throw new Error(`unknown op: ${op}`);
}
```

### 2. Register handler in dispatcher

`web/supabase/functions/skill_call/index.ts`:

```ts
import { run as runYourSkill } from "./handlers/<name>.ts";

const HANDLERS: Record<string, Handler> = {
  "paid-add": runPaidAdd,
  "<name>": runYourSkill,   // ← add this
};
```

### 3. Ensure the skill exists in the DB

```sql
-- If not already present:
INSERT INTO public.skills (name, category) VALUES ('<name>', '<Category>');

-- Grant it to a license for testing (use your own license_id):
INSERT INTO public.license_skill_grants (license_id, skill_id, source)
SELECT <license_id>, id, 'dev_test' FROM public.skills WHERE name = '<name>';
```

### 4. Deploy

```bash
cd ~/lovstudio/coding/web
supabase functions deploy skill_call --project-ref nouchjcfeoobplxkwasg
```

### 5. Write the thin-client SKILL.md

```markdown
---
name: sgc-<name>
description: <one line> ... Trigger when user says "...".
version: 0.1.0
---

# <name>

Thin client. Real implementation is server-side.

## How to invoke

Given user input `<describe shape>`:

1. Parse into JSON, e.g. `{"field1": "...", "field2": 42}`.
2. Run:
   ```bash
   sgc-skill-helper call <name> --op primary_op --input '<json>'
   ```
3. The CLI prints JSON with shape:
   ```json
   { "result": "...", ... }
   ```
4. <Describe how to render result. Be specific so Claude can't improvise.>

## Error handling

- `not activated` → activation prompt
- `not entitled to this skill` → upgrade/purchase prompt
- other → show verbatim

## Why the thin client

Unlike encrypted skills, cloud-split skills keep the real implementation on
the server. This thin SKILL.md is only the transport layer.
```

### 6. Test end-to-end

```bash
sgc-skill-helper call <name> --op primary_op --input '{"field1":"x","field2":42}'
```

Expected: JSON output on stdout. Error on stderr for auth/entitlement issues.

## Security notes

- The license HMAC signing protects against anyone without the license key
  from calling the endpoint — so server CPU cost is bounded by your paid users
- Nonces prevent replay attacks; don't skip the `used_nonces` insert in
  `_shared/auth.ts`
- Handlers should validate input shape aggressively — treat all input as
  adversarial (paid users may still probe your handler for bugs)
- Rate-limit per license at the Edge Function level if abuse becomes an issue
  (Supabase Edge Functions have per-request DB access; a simple
  `invocations` log + count check works)

## What cloud-split does NOT solve

- **Fake-out via reimplementation**: a motivated user can observe your I/O
  shape and rebuild an inferior clone. Your moat is quality, not secrecy.
- **User's API latency budget**: each call is ~200-500ms HTTP round-trip. For
  interactive skills, batch where possible.
- **Offline usage**: cloud-split skills don't work offline. If offline is
  critical, you're stuck with encrypted + accepting L2 leakage.

## Reference implementations

### ✓ `threshold-check` — copy this pattern

Minimal end-to-end with **actual protection**. Start here.

- Handler: `web/supabase/functions/skill_call/handlers/threshold-check.ts`
  — returns `{verdict: "A" | "B"}`, nothing else
- Thin client: `skills/threshold-check-skill/SKILL.md`
  — transport + symbol→text table, zero rule description
- CLI command:
  `sgc-skill-helper call threshold-check --op evaluate --input '{"params": {"values": [2, 6], "threshold": 10}}'`

Key patterns to copy:
- Handler returns a single symbolic field, no derived values, no narration
- Thin client has a rendering table, not a rendering algorithm
- No "what the rule is" text anywhere public

### ⚠ `paid-add` — architecture demo only, do NOT copy the return shape

`paid-add` exists to demonstrate the **cloud-split infrastructure** (CLI +
Edge Function + handler dispatch + HMAC auth). Its return value (`{result,
display, marker}`) **leaks the algorithm** on purpose — it's a teaching demo,
not a protection example.

If you're writing a real protected skill, copy `threshold-check`'s return
shape, not `paid-add`'s. The architecture is identical; only the payload
discipline matters for protection.
