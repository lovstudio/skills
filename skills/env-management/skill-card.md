# Skill Card — lov-env-management

## Description

`lov-env-management` is a local developer credential ledger for multiple platforms, accounts, and rotating API Keys. It tracks lifecycle evidence, selects exactly one Key per target variable, and projects it without displaying secret values.

## Owner

Maintained by LovStudio Skills contributors through the source repository.

## License / Terms

MIT. Users remain responsible for each provider's credential, access, and acceptable-use terms.

## Use Case

The intended user is a developer or operator with several accounts or rotating Keys for the same provider. Inputs are safe identity metadata, lifecycle dates, a secret supplied through hidden input or a reference, and the requested environment target. Outputs are a redacted inventory, explicit bindings, audit evidence, and optional local projections.

## Deployment Geography

Runs locally on macOS or Linux and is not geographically restricted. Provider availability remains external.

## Requirements / Dependencies

Python 3.9 or newer is required. macOS Keychain and 1Password are optional secret backends. zsh is required only for zsh projection; `launchctl` or `systemctl --user` is required only for current-user session projection.

## Known Risks and Mitigations

- Persistent environment variables are visible to a broader process set. Sync is preview-first and invocation-scoped injection remains the safer recommendation.
- Expired or invalid Keys could be selected accidentally. Binding rejects unhealthy Keys by default and audit reports stale evidence.
- The file backend is plaintext at rest. It is mode `0600`, and Keychain or 1Password is preferred where available.
- A local Dashboard could leak data. This Dashboard serves redacted metadata only on loopback and has no secret reveal or input action.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Security model](references/security-model.md)
- [Data model](references/data-model.md)
- [Verified local case](cases/evidence/smoke-test.json)

## Skill Output

Outputs are redacted JSON inventory, lifecycle and binding records, a mode-`0600` generated zsh source file, an idempotent zsh rc source block, audit results, and a metadata-only local Dashboard. Validation covers hierarchy integrity, redaction, binding health, permissions, expiry, and Dashboard state.

## Skill Version

0.1.0

## Ethical Considerations

The Skill minimizes credential disclosure, does not manage unrelated personal secrets, and does not bypass provider access control or remote Secret governance. It names the weaker guarantees of plaintext file storage and process environments instead of describing them as encrypted.

## LovStudio Evidence

### User Cases

[cases/cases.json](cases/cases.json) records the original multi-account and multi-Key request and the locally verified output. The evidence report records fingerprint assertions and isolated temporary execution, never a real credential or private temporary path.

### Dimension Map

The machine-readable card tracks hierarchy integrity, secret non-disclosure, lifecycle safety, and operational usability. Each dimension is marked `verified-6-tests` after the warning-free local test run.

### Pricing Basis

[pricing-card.yaml](pricing-card.yaml) keeps the Skill free because local credential hygiene is foundational and the implementation has no hosted service cost. Hosted team sync and enterprise enforcement are outside the boundary.

### Distribution

GitHub, LovStudio, WorkBuddy, and SkillPay are all explicitly `not-published`. Local validation and installation are not represented as public distribution.
