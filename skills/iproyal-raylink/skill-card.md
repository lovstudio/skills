# IPRoyal 链式出口 · IPRoyal Chain Exit · Skill Card

## Description

Chains an IPRoyal ISP static residential proxy behind an encrypted RayLink
group in Clash Verge Rev, exposes it as the exit for AI sites, verifies the exit
IP on the running core, and supports remove and rollback.

## Owner

LovStudio — https://lovstudio.ai

## License / Terms

MIT for the Skill source. IPRoyal, RayLink and Clash Verge Rev are third-party
products under their own terms; users need their own subscriptions and must
follow IPRoyal's acceptable use policy.

## Use Case

Mainland China users of Clash Verge Rev with a RayLink subscription and an
IPRoyal ISP proxy, whose standalone IPRoyal profile fails or is intermittent,
and who want AI sites to leave through the fixed IPRoyal IP.

## Deployment Geography

Global. Automatic restart on macOS; manual restart on Windows and Linux.

## Requirements / Dependencies

Python 3.8+ standard library; Clash Verge Rev 2.0+ with mihomo. Optional PyYAML
and node. The IPRoyal proxy string comes from the user's environment or a file.

## Known Risks and Mitigations

- Overwriting a custom script: refused unless `--wrap-existing`; dry run by
  default; backups; byte-for-byte removal.
- Credential leakage: env/file input only, masked output, mode 600, never
  stored in the Profile.
- Proxy loops: carrier cannot be exposed; groups reachable from the carrier are skipped.
- Unintended full-traffic routing: only `--select` groups lead with the exit.
- Carrier blocked on some networks: `verify` fails explicitly; server-side
  remedy documented.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Why a carrier is required](references/why-chain.md)

## Skill Output

A managed block in the RayLink profile's Clash Verge script, a backup
directory with a manifest, and a JSON verification report (exit group loaded,
chained delay, selections, trace IP, pass).

## Skill Version

0.1.0

## Ethical Considerations

For users configuring their own subscriptions on their own devices. It does
not bypass organizational policy, purchase services, or share credentials.

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json): a real standalone-IPRoyal failure,
diagnosed, then replayed through this Skill on a fresh sandbox and on a custom
profile, verified on a real mihomo core.

### Dimension Map

Exit correctness, safety and reversibility, and portability, each with evidence
in `skill-card.yaml`. Scores are not assigned yet.

### Pricing Basis

Free. See [`pricing-card.yaml`](pricing-card.yaml).

### Distribution

Planned free channels: github, lovstudio. Current status: local source only; nothing is published on github, lovstudio, workbuddy or skillpay.
