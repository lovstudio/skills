# Skill Card — lov-npm-publisher

## Description

Audits a new or existing npm package, plans publication through one of two equal
auth modes — GitHub Actions OIDC trusted publishing or a local granular NPM_TOKEN
(bypass) — handles the one-time first-publish boundary, and verifies the exact
released version from the npm registry.

## Owner

Maintained by LovStudio contributors. Contact the maintainers of the source in
which this Skill is distributed.

## License / Terms

MIT. Users remain responsible for registry accounts, namespace rights, repository
access, package contents, and authorization to publish.

## Use Case

For npm maintainers who want repeatable releases without storing a long-lived
publish token. Input is a package directory and, for OIDC, its GitHub repository.
Output is a state audit, tokenless workflow or local publish command,
bootstrap/trust plan, and precise release evidence.

## Deployment Geography

The planner runs locally worldwide. OIDC publication targets a GitHub-hosted
Actions runner and the public npm registry; bypass publication runs locally against
the public npm registry.

## Requirements / Dependencies

- Python 3.9 or newer, Git, Node.js, and npm.
- PyYAML only for validating this Skill source.
- No credential for audit or workflow generation.
- npm and GitHub identity proof only for authorized trust setup; a granular
  NPM_TOKEN only for authorized bypass publication.

## Known Risks and Mitigations

- Registry outages remain `registry_unknown`; they are never treated as proof that
  a package name is free.
- Existing workflows are preserved unless an explicit reviewed force replacement
  is requested.
- CI success or an accepted local publish alone is insufficient; the exact package
  version must be read back.
- A missing NPM_TOKEN blocks bypass publication and is reported as a warning, not
  silently ignored.
- Tokens, OTPs, cookies, and OIDC assertions are never written to source or Profile.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [npm publishing contract](references/npm-publishing-contract.md)
- [Skill composition record](references/skill-composition.md)

## Skill Output

The deterministic CLI emits a JSON audit plan and can write
`.github/workflows/publish.yml` (oidc) or resolve a local publish command (bypass).
The instruction layer produces a concise state report with the package/version,
auth mode, CI run or local publish, registry readback, provenance result, and any
blocker. Validation covers state branches, both auth modes, secret absence,
idempotence, source integrity, and trigger routing.

## Skill Version

0.1.0

## Ethical Considerations

Operate only on accounts, namespaces, repositories, and packages the user is
authorized to control. Do not weaken 2FA, capture credentials, conceal provenance
gaps, or claim a package is live without direct registry evidence.

## LovStudio Evidence

### User Cases

[`cases/cases.json`](cases/cases.json) records the real request that motivated this
Skill and the locally verified planner/writer result.

### Dimension Map

`skill-card.yaml` records five verified dimensions: registry-state correctness,
credential safety, auth-mode parity, conservative writing, and release
verifiability.

### Pricing Basis

The Skill is free because it is local safety automation with no hosted service or
credential custody. See [`pricing-card.yaml`](pricing-card.yaml).

### Distribution

Local installation is verified. GitHub and LovStudio publication have not been
performed. WorkBuddy and SkillPay have not been submitted.
