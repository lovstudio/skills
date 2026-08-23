# Security model

## Storage split

`registry.json` contains only hierarchy, dates, states, variable names, backend type, bindings, and redacted validation evidence. Secret material lives in one of these sources:

| Backend | Secret location | Notes |
| --- | --- | --- |
| `keychain` | macOS login Keychain | Default on macOS when `security` is available |
| `file` | `vault.json`, mode `0600` | Portable fallback; plaintext at rest and protected only by filesystem permissions |
| `op` | Explicit 1Password `op://` item reference | Requires an authenticated `op` session when resolving |
| `env` | Existing process environment variable | Useful for invocation-scoped or externally injected sources |

The file backend is intentionally honest: `0600` prevents access by other local users but is not encryption. Prefer Keychain or 1Password on shared or high-risk machines.

## Secret input and output

- Interactive input uses `getpass`; automation reads one value from standard input with `--secret-stdin`.
- There is no CLI option that accepts the secret as an argument.
- JSON output, exceptions, probe evidence, Dashboard state, and audit reports contain no raw secret or secret reference.
- Fingerprints are one-way SHA-256 prefixes and are emitted only when the caller explicitly asks for them.

## Environment exposure

Any environment variable is readable by the process receiving it and commonly by its children. Putting a Key in `~/.zshenv` makes it broadly available to zsh processes. Prefer invocation-scoped injection for narrow tasks.

`sync-system` uses `launchctl setenv` on macOS or `systemctl --user set-environment` on Linux. Those tools necessarily receive the value in a process argument and the resulting value becomes available to the current user session. The command therefore requires `--acknowledge-process-env-risk` and never runs during an ordinary shell sync.

## Dashboard boundary

The Dashboard:

- binds only to `127.0.0.1`;
- sends a restrictive Content Security Policy and no external assets;
- embeds a random process-local write token that is never saved;
- requires an exact same-origin request plus the token for mutation;
- returns only redacted registry state;
- excludes add, reveal, export-secret, and delete-secret operations.

Closing the Dashboard process invalidates the token and ends the HTTP listener.
