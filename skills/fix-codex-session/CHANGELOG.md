# Changelog

## 0.2.0

- Adds `scripts/sync_thread_provider.py` for "Model provider not found" after
  switching CC Switch or another provider manager.
- Syncs `state_*.sqlite` `threads.model_provider` to the active config provider
  by default with a read-only `--json` dry run, SQLite backup before `--apply`,
  stale-provider detection, and protection of built-in providers.
- Deliberately does not rewrite rollout JSONL to avoid breaking paginated
  byte-offset lineage; documents that boundary in the troubleshooting guide.
- Adds a real provider-migration case and updates the trust bundle to 0.2.0.

## 0.1.0

- Initial local Skill source for Codex session recovery.
- Adds `scripts/fix_codex_session.py` (stdlib-only) for read-only diagnosis of
  dangling tool-call/output pairing and an optional repaired rollout copy.
- Adds `references/troubleshooting.md` documenting the root cause, recovery, and
  prevention for the "No tool output found for tool call" failure.
- Adds the trust bundle: `skill-card.yaml`/`.md`, `pricing-card.yaml`, a real
  `cases/cases.json`, and `references/skill-composition.md`.
