# Explicit maintainer paid-case workflow

This preserves existing commands and repository storage. It is only for a user
who explicitly requests a source-maintainer update and has repository write
permission. It never runs as a fallback for failed website contribution.

This route needs the target's local SKILL.md, a listed target with an authoritative
positive Credits price, lov-share-session, and explicit acceptance of both the
public summary and redacted full-session upload. Free, unlisted or unpriced
targets cannot use it. Do not make a requested paid Session public to fit the API.

Prepare true Input → Prompt → Output and evidence. The legacy validator accepts
artifact_type visual/non-visual/mixed (or omitted); the website requires
visual/other. Visual cases require cover. Relative assets must exist inside the
target and have a verified public delivery path.

```bash
python3 "$SKILL_DIR/scripts/add_case_with_session.py" TARGET \
  --case CASE_JSON --share-session-script "$SHARE_SESSION_DIR/scripts/share_session.py" \
  --file REDACTED_TRANSCRIPT --dry-run

# Only after consent to both public case and paid full Session:
python3 "$SKILL_DIR/scripts/add_case_with_session.py" TARGET \
  --case CASE_JSON --share-session-script "$SHARE_SESSION_DIR/scripts/share_session.py" \
  --file REDACTED_TRANSCRIPT
```

Session ID can replace the transcript file flag. The helper verifies the
dependency's structured response before atomically writing cases/cases.json.
Upload failure leaves the local registry unchanged. If uploading succeeds but
writing fails, retain the returned Session reference and report the partial state.

Input omits session. The helper adds the server-returned url, access: paid,
priceCredits, pricingRule: ceil(target-skill-price/10), and targetSkill. This is
the viewer's unlock price, not a client-selected case-submission fee. The
lower-level add_case.py still requires this validated paid reference. Do not
send it to the website case API, which rejects paid fields.

Validate the target and inspect the exact case/asset diff. Only after explicit
publication authorization hand off to lov-skill-publisher, selecting the Skill
Publisher channel and case-only update. Preserve unrelated changes. The publisher
owns source push and cache refresh; no new version is implied unless required by
the target's policy. Local-only targets stay local.

Read back raw source JSON, parent and case pages, every image and the
unauthenticated Session paywall with verify_public_case.py. Verify exact server
price and paid access; report local, pushed and live-verified separately.
