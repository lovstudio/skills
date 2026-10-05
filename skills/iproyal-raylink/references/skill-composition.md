# Skill Group Composition

## Nearby Skills Inspected

| Skill | Routing contract | Classification | Decision |
| --- | --- | --- | --- |
| `lov-clash-tun-doctor` | Diagnoses and reversibly repairs application failures behind Clash Verge TUN (WeChat media, IPv6, DIRECT lists) | optional downstream atom | Useful when an app still fails after the chain is verified; it does not add proxies or chains |
| `lov-skill-creator` / `lov-skill-publisher` | Create and publish Skills | not composed | Lifecycle tooling, not part of the runtime outcome |
| `lov-check-balance`, airport or subscription Skills | none found that edit Clash Verge profiles | not composed | No overlap |

## Atomic Handoffs

```text
lov-iproyal-raylink
  input: Clash Verge Rev data directory + RayLink profile + IPRoyal proxy string
  output: managed script block, backup manifest, verify JSON (pass, delay, trace IP)
                |
                v
optional: lov-clash-tun-doctor
  input: a still-failing application after verify passes
  output: TUN-level diagnosis and DIRECT/IPv6 repairs
```

This Skill owns acceptance of the chain: exit group loaded, chained delay
works, AI trace IP equals the IPRoyal address.

## Overlap Decisions

`lov-clash-tun-doctor` also writes Clash Verge enhancements, but only rules and
global IPv6 settings, never proxies or groups, and its backups use a different
prefix. The two can run on the same profile without conflict because this Skill
touches only the profile script's managed block.

## Composition Decision

Single Skill. Detect, apply, verify, remove and rollback share one context (the
RayLink profile and its script) and one acceptance criterion; none is useful as
an independent product, so a Kit adds nothing.
