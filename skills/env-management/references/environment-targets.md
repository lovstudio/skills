# Environment targets

## Current command

For a one-time action, prefer resolving the Key and injecting it only into that subprocess. This is narrower than either persistent target and should not create a binding unless the user asks for one.

## zsh startup

`sync-shell` generates a mode-`0600` file inside the Skill storage directory and manages one sentinel block in the selected zsh rc file. The block sources the generated file if it is readable. Existing user content outside the block is preserved, and an on-disk backup is created before a changed rc file is replaced.

Preview is the default. Apply requires `--apply`.

Verification must use a new clean zsh process and report only whether each variable is present or whether its fingerprint matches the selected Key. Never use `env`, `printenv`, or shell tracing on a secret-bearing session.

## Current user GUI session

`sync-system` is not machine-wide persistence:

- macOS: `launchctl setenv` for the current login session;
- Linux: `systemctl --user set-environment` for the current user manager.

Secrets become readable to relevant user processes and may transit a short-lived command argument. Apply only after the user explicitly acknowledges that risk. Platform-wide remote Secret stores and `/etc/environment` remain out of scope.

## Project `.env` files

This Skill deliberately does not generate repository `.env` files. Project policies vary, `.gitignore` can be wrong, and client-side build prefixes can expose secrets. A target project workflow may consume a confirmed variable name and write its own local file after checking ignore rules and runtime boundaries.

## Remote platforms

Vercel, GitHub Actions, Supabase, Cloudflare, Kubernetes, and similar systems own separate encrypted Secret stores and audit trails. Use their official workflows. `lov-env-management` may supply the selected locator and variable name, but never prints a value for copy/paste.
