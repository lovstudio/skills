# Changelog

## 0.1.1 — 2026-10-05

- Fix: Step 0 now defines `CAM` as a shell function and Steps 1, 2, 3 and 5 call
  `CAM <args>` instead of `$CAM <args>`. In zsh (the macOS default) an unquoted `$CAM`
  holding `python3 /path/to/script.py` is not word-split, so `$CAM scan` failed with
  `no such file or directory: python3 ...` (exit 127); bash was unaffected. The function
  also quotes `$SKILL_DIR`, so install paths containing spaces work.
- `scripts/claude_account_migrate.py` is unchanged.

## 0.1.0 — 2026-10-04

- `scan`, `migrate` (plan by default, `--apply` to write) and `retention` subcommands.
- Additive copy of Code-tab and Cowork sessions between desktop accounts, with archive
  index and backlog merge, orphan detection, and Cowork `cleanupPeriodDays` protection.
- Storage reference for the Claude desktop session layout observed on macOS.
