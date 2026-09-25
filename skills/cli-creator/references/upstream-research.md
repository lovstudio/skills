# Upstream Research: CLI-Anything

Research snapshot: 2026-08-24.

Primary reference: [HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything),
licensed under Apache License 2.0. Its `cli-anything-plugin/HARNESS.md` describes
an agent harness methodology for turning open-source GUI applications into
stateful CLIs.

## Principles retained

- analyze the codebase, backend engine, data model, and GUI-to-API mappings first;
- call the real software or runtime instead of rebuilding its behavior;
- provide both human-readable and machine-readable JSON output;
- expose cheap introspection before mutation;
- plan tests before implementation;
- combine unit tests, real-file E2E tests, installed-command subprocess tests,
  and programmatic output verification;
- document architecture, commands, dependencies, tests, and known gaps;
- auto-save one-shot state mutations and support dry-run when applicable.

## Deliberate differences

- Scope expands from GUI applications to any local project with a callable
  backend: application, library, service, native-format tool, or existing CLI.
- Project path is optional and defaults to the Skill invocation directory.
- Generated commands use the `lov-cli-` prefix by default.
- Packaging uses PEP 621 `pyproject.toml` and a regular `src/` package instead of
  a shared PEP 420 namespace. A minimal `setup.py` shim only preserves editable
  installation on old bundled pip versions.
- Python's standard `argparse` is the default, avoiding a mandatory Click runtime.
- A REPL is conditional on meaningful persistent state rather than mandatory.
- The first local outcome is installation and verification; PyPI publication is
  intentionally excluded.
- The generated contract uses explicit JSON success/error envelopes and stable
  exit-code meanings.

No upstream implementation file is copied into this Skill. The source retains
its own MIT license while attributing the researched methodology and keeping the
upstream license boundary explicit.
