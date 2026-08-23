# Skill Group Composition

## Nearby Skills Inspected

- `1password`: installs and operates the `op` CLI, including multi-account sign-in and `op://` reads. It owns password-vault authentication and secret retrieval, not environment lifecycle or target bindings. Classification: optional upstream atom.
- `lov-zsh-alias`: idempotently adds aliases and functions to `~/.zshrc`. It owns command shortcuts, not secret storage or environment variables. Classification: not composed.
- `lov-install-zenmux-api`: installs one ZenMux/Supabase integration and writes one provider secret. It owns a service-specific deployment outcome. Classification: optional downstream atom.
- `lov-install-ai`: adds an AI product boundary to an application and deliberately leaves global API Key configuration to another workflow. Classification: optional downstream atom.
- `lov-integrate-lovstudio-llm-skill`: consumes `LOVSTUDIO_API_KEY` to call a specific API. It owns the API result, not credential rotation. Classification: optional downstream atom.
- `lov-npm-config-oidc`: the current local source is an unfinished scaffold for npm OIDC configuration. OIDC workload identity is materially different from long-lived API Key management. Classification: not composed.

## Atomic Handoffs

| Stage | Owner | Input artifact | Output artifact | Acceptance boundary |
| --- | --- | --- | --- | --- |
| Upstream | `1password` | Authenticated `op` session and an explicit `op://` reference | A secret resolved at invocation time | `1password` proves access; `lov-env-management` never stores or displays the resolved value |
| Core | `lov-env-management` | Platform/account/key metadata plus a secret source | Redacted registry, one binding per target variable, lifecycle evidence, and optional local projections | This Skill owns hierarchy integrity, safe selection, file permissions, expiry audit, and non-disclosure |
| Downstream | Provider or app integration Skill | Confirmed variable name and target, never the raw value | Working provider integration or deployment | The downstream Skill owns its real API/deployment check; this Skill owns only local credential state |

No external Skill is required for the file or macOS Keychain backends. Optional handoffs happen only at the explicit secret-reference or redacted variable-name boundary.

## Overlap Decisions

- Do not duplicate 1Password account login, vault browsing, or `op` installation. Store only the explicit `op://` reference and invoke `op read` when projecting.
- Do not use `lov-zsh-alias` to write exports. Environment projections have their own sentinel block, secure generated file, permissions, and binding audit.
- Do not absorb provider-specific deployment or API semantics. A generic guarded HTTPS probe supplies evidence when possible; a downstream integration still owns functional acceptance.
- Do not treat OIDC identity as an API Key. Short-lived workload identity should remain in the relevant publishing or CI workflow.

## Composition Decision

This is a **Single Skill with a Python CLI and local Dashboard**. Inventory, lifecycle, validation, binding, projection, and dashboard actions share one registry and one acceptance criterion: the intended Key is selected safely without disclosure. Splitting those modes into embedded Skills would fragment the atomic binding state and add no independently useful user outcome.
