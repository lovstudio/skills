# Generated CLI Contract

## Required surfaces

Every accepted harness exposes:

- `--help` and `--version`;
- global `--json` before the subcommand;
- `doctor` for runtime and project-root diagnostics;
- `info` for project and harness identity;
- `capabilities` for machine-readable command discovery;
- at least one project-specific command backed by real behavior.

No-argument behavior prints help unless the project genuinely benefits from a
stateful REPL. A REPL never replaces one-shot subcommands.

## JSON envelope

Successful commands return one JSON object on stdout:

```json
{
  "ok": true,
  "command": "validate",
  "data": {},
  "meta": {
    "duration_ms": 14
  }
}
```

Failures return one diagnostic object and a nonzero process exit code:

```json
{
  "ok": false,
  "command": "validate",
  "error": {
    "code": "backend_failed",
    "message": "The project validator returned exit code 1.",
    "context_id": "cli-12ab34cd",
    "hint": "Run doctor and inspect stderr."
  }
}
```

The envelope may include captured backend stdout/stderr in `data` when it is
safe. Never include secrets or reconstruct a shell command string containing
user values.

## Exit codes

- `0`: command and verified postconditions succeeded;
- `2`: CLI usage or plan error;
- `3`: missing project/runtime dependency;
- `4`: backend execution or verified postcondition failure;
- `5`: unsafe or conflicting state.

Project-specific codes may be added, but these meanings remain stable.

## Mutation behavior

- Inspect before mutate where possible.
- Validate inputs before side effects.
- Make repeated calls idempotent or report the conflict explicitly.
- A one-shot state mutation saves before process exit.
- `--dry-run` suppresses writes and explains intended changes when mutation
  planning is meaningful.
- Persistent session writes are atomic and locked when concurrent processes are
  plausible.

## Backend fidelity

The CLI is an interface to the project, not a replacement implementation. Export
and render commands call the real runtime and verify output bytes, structure,
metadata, content, or state. A zero exit code by itself is insufficient evidence.

## Packaging

The generated harness uses a small PEP 621 `pyproject.toml`, a `src/` package,
and a console script. A minimal `setup.py` compatibility entry supports editable
installs in venvs whose bundled pip predates PEP 660; project metadata remains in
the PEP 621 file. The command must run from a working directory outside both the
target project and harness.

The harness also emits `requirements.txt`. On pip older than 21.3, install that
file first and use `python setup.py develop` as the local editable fallback.
