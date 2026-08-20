# Skill composition: dsh-plugin-creator

Inspection of the nearby `.agents/skills/` group against this skill's input/output contract.

## Classification

- **core atom** — `dsh-plugin-creator`: owns the user-visible outcome of authoring a new plugin package end-to-end.
- **downstream atom** — `dsh-pre-push-checks`: consumes a finished plugin change and selects the narrowest checks that cover its diff.
- **not composed** — `dsh-prose-standard`, `dsh-code-review`, `dsh-doc-standards`, `dsh-archive-agent-notes`, `dsh-find-simplifications`, `dsh-merging-stacked-prs`, `dsh-trim-cot-leakage`, `dsh-doc-site-sync`: adjacent in topic but add no meaningful handoff to plugin creation.

## Handoff

`dsh-plugin-creator` step 7 ("Verify") and step 8 ("Commit") deliberately overlap the pre-push discipline owned by `dsh-pre-push-checks`. The boundary is the artifact: this skill produces the package source and README; `dsh-pre-push-checks` selects the checks for a finished change. After creating a plugin, delegate check selection to `dsh-pre-push-checks` rather than re-enumerating the gate inventory here.

## Single vs Kit

Single skill. Plugin creation is one user-visible outcome; its stages share one context and have no independent input/output contracts. No `kit.yaml`, no `scripts/` (the deterministic steps are shell commands the agent runs, not a reusable local CLI).
