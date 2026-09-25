# CLI Testing Requirements

Write `TEST.md` before test implementation. Preserve it as the plan-and-results
record after execution.

## Required layers

1. **Unit tests** cover plan parsing, parameter conversion, backend argv
   construction, errors, and state helpers without external dependencies.
2. **Source invocation tests** run the CLI module with `PYTHONPATH=src` and verify
   help plus JSON introspection.
3. **Installed-command E2E tests** resolve the console script from `PATH`, run it
   from a neutral temporary directory, and execute a real project workflow.
4. **Artifact/state verification** opens or probes the result rather than only
   checking the backend exit code.

## Real backend rule

If the product runtime is missing, a real E2E test fails with an actionable
install message. It does not skip, mock, or substitute a simplified engine. Fast
unit tests may use synthetic inputs; the acceptance workflow may not.

## Minimum workflow

An accepted CLI demonstrates:

1. `doctor --json` confirms the target root and backend;
2. `capabilities --json` lists built-ins and domain commands;
3. one project-specific read or create command succeeds;
4. one material mutation/export, when the project supports it, produces real
   state or an artifact;
5. the postcondition is checked programmatically;
6. a failure path returns nonzero with parseable diagnostics.

## Output-specific checks

- JSON: parse it and assert schema/keys, not substrings.
- SQLite/database: query stable records and transaction results.
- ZIP/OOXML: validate archive structure and required members.
- PDF/image/audio/video: validate signatures and probe relevant content or
  frames/samples with the real toolchain.
- Service calls: read the created or changed resource back from the service.
- Native project files: reopen through the product's parser or renderer.

## Installed resolution

Never hard-code the current interpreter as proof that a console entry point
works. Resolve the declared command with `shutil.which`, require it in the final
acceptance run, and do not set the harness as the subprocess working directory.

Record the exact test count, pass rate, duration, generated artifact paths, and
known gaps in `TEST.md`.
