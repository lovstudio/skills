---
name: lov-skill-add-case
description: >
  将已验收结果整理成公开案例，并把完整 Session 作为目标 Skill 售价 1/10 的付费证据上传。Use when the user asks to add or publish an accepted Skill case.
license: MIT
compatibility: "Python 3.10+ and PyYAML. LovStudio auth and network access are required for the paid session upload."
depends_on:
  - lov-share-session
metadata:
  author: LovStudio contributors
  version: "0.2.2"
  card_standard: lovstudio/skill-card/v1
  tags:
    - skill-case
    - showcase
    - evidence
    - website-sync
    - paid-session
---

# lov-skill-add-case

Turn one explicitly accepted Skill result into a truthful, privacy-safe public
summary plus a paid full-session evidence page, append both references to the
owning Skill, and—when publicly listed—verify both surfaces live.

## Triggers

### Activate when

- 用户说“这个结果不错，加入这个 Skill 的案例并同步官网”。
- 用户说“用 skill-add-case 收录刚才的结果”。
- The user says “add this accepted result as a skill case” or “publish this case to the website”.

### Do not activate when

- The user merely invokes another Skill or has not accepted its result.
- The result failed, remains a draft, or has no reviewable output evidence.
- The target Skill is free, unlisted, or has no authoritative Credits price;
  the required paid Session cannot be priced in that state.
- The user wants to create or redesign a Skill; use `lov-skill-creator`.
- The user wants a normal release without a new case; use `lov-skill-publisher`.

## User Profile (cross-session)

Read `skill.yaml` and resolve the shared `user-profile/v1` context at the start
of every run. Use current request, project context, Skill records, shared
preferences, and then safe defaults. Persist only a direct durable user statement
through `scripts/profile_store.py record ... --confirm`; never persist case
content, credentials, or inferred private paths.

## Skill Group Composition

Read `references/skill-composition.md`. `lov-share-session` is a declared required
dependency that owns transcript normalization, upload, and the paid access URL.
This Skill owns case qualification and the canonical `cases/cases.json` mutation.
`lov-skill-publisher` remains an optional downstream publication handoff.

## Workflow (MANDATORY)

### Step 0: Resolve the target and runtime context

1. Resolve `SKILL_DIR` to this Skill and read `skill.yaml`.
2. Resolve the target Skill source from an explicit path, the completed
   invocation, the current repository, or a verified installed symlink.
3. Confirm the target contains `SKILL.md`. Read its routing contract and current
   `cases/cases.json` before writing.
4. Resolve the declared `lov-share-session` dependency and its
   `scripts/share_session.py`. Do not substitute a hand-written upload request.
5. Preserve unrelated dirty files. Never stage or commit outside the target case
   file and case assets created for this invocation.

### Step 1: Enforce the acceptance gate

Proceed only when the user explicitly states that the result is good, accepted,
approved, or suitable for publication. A successful command, generated file, or
assistant self-assessment is not acceptance. If acceptance is missing, ask one
focused question and stop before mutation:

> 这个结果已经由你确认满意，并同意将脱敏摘要公开、将脱敏后的完整 Session 上传为付费案例证据吗？

Do not use an old positive statement for a different output. Record the accepted
artifact, the minimum prompt, verification method, and acceptance date.

### Step 2: Build a public-safe case bundle

Follow `references/case-contract.md`. Create one JSON object with:

- stable `id`, `type: case`, title, description;
- real `input`, minimum `prompt`, and real `output`;
- `evidence.acceptance: user-confirmed`, `verified_at`, `method`, and `privacy`;
- for a primarily visual result, `evidence.artifact_type: visual` plus a required
  `cover` showing the accepted final artifact; use `gallery` for additional final
  variants rather than process screenshots;
- optional `cover` and `gallery` for non-visual results. Assets must exist inside
  a publicly readable target source or use stable public HTTPS URLs. A paid or
  private target must not expose an image URL that browsers cannot read.

A visual case without its accepted output image is incomplete even when the
text summary is accurate. Treat the image as reviewable evidence, not decoration.

Redact secrets, personal identifiers, transcript bodies, private absolute paths,
and unpublished customer data. Preserve enough concrete evidence to make the

### Step 3: Preflight, upload the paid Session, then add atomically

The case JSON passed to the composed helper omits `session`; the helper validates
the public bundle, invokes `lov-share-session`, verifies the server-derived price,
adds the exact session reference, and only then mutates `cases/cases.json`.

Run a no-upload dry run first, then execute the same command without `--dry-run`:

```bash
python3 "$SKILL_DIR/scripts/add_case_with_session.py" TARGET \
  --case CASE_JSON --share-session-script "$SHARE_SESSION_DIR/scripts/share_session.py" \
  [--file TRANSCRIPT | --session-id SESSION_ID] --dry-run

python3 "$SKILL_DIR/scripts/add_case_with_session.py" TARGET \
  --case CASE_JSON --share-session-script "$SHARE_SESSION_DIR/scripts/share_session.py" \
  [--file TRANSCRIPT | --session-id SESSION_ID]
```

The service reads the target Skill's authoritative Credits price and charges
`ceil(price / 10)`, minimum 1 Credit. The client never sends a price. If the
target is free, unlisted, or unpriced, the upload fails and the case registry is
not written. Keep the returned URL, price, case ID, and SHA-256 fingerprint.

`scripts/add_case.py` is the lower-level mutation guard. It now rejects any new
case without a validated `session` object; use it directly only when a paid share
has already been uploaded and its exact server response is present.

### Step 4: Validate the owning Skill

Run the target's own validator when present:

```bash
python3 TARGET/scripts/validate_skill.py TARGET
```

Otherwise run the current `lov-skill-creator` validator. Inspect `git diff --
cases/cases.json` and any new case assets. Do not continue if validation fails or
if the diff contains unrelated or private data.

### Step 5: Sync the official website when applicable

Determine whether the target already has a public source repository and a
LovStudio catalog entry.

- **Public target:** hand the validated source to `lov-skill-publisher`, selecting
  only the **Skill Publisher** channel and declaring a **case-only update**. Push
  the intended case diff, update catalog metadata only if required, purge
  `skill-cases:<id>` plus the detail path, and do not claim a new version unless
  the repository's policy requires one.
- **Local-only target:** keep the case validated locally and report that website
  sync is not yet possible. Do not create a public repository or listing unless
  the user authorized publication.

For a public target, publication is incomplete until the raw public
`cases/cases.json`, `https://lovstudio.ai/skills/<id>`, and the linked unauthenticated
Session paywall all resolve. Every `cover` and `gallery` URL must also appear in
the rendered page and return non-empty `image/*` content. The verifier checks all
four surfaces; a written URL or successful cache-refresh response is not image
publication evidence.
Verify them with:

```bash
python3 "$SKILL_DIR/scripts/verify_public_case.py" \
  --cases-url RAW_CASES_URL --page-url PUBLIC_DETAIL_URL \
  --case-id CASE_ID --fingerprint SHA256 --marker CASE_TITLE
```

### Step 6: Report exact state

Report the target Skill, case ID, local file, fingerprint, paid Session URL and
Credits price, source validation, repository commit/push state, cache refresh response, and live detail URL. Use
`local`, `pushed`, and `live-verified` as distinct states. If any downstream step
fails, keep the truthful earlier state and include the copyable diagnostic.

## Dependencies

- Python 3.10+; PyYAML is required by the generated source validator.
- `lov-share-session` is required for transcript upload and paid URL creation.
- Git/GitHub and `lov-skill-publisher` are needed only for public sync.

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
