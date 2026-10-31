# Skill Group Composition

## Nearby Skills Inspected

| Skill | Routing contract | Classification | Decision |
| --- | --- | --- | --- |
| `lov-iproyal-raylink` | Chains an IPRoyal static residential exit behind RayLink groups in a Clash Verge profile and verifies the AI exit IP | optional upstream atom | Route exit-chain setup there; this Skill never adds proxies or groups |
| `lov-wdb-cli`, `lov-media-crawler` | Query local WeChat data; download platform media such as WeChat Channels videos | not composed | They consume WeChat content; neither diagnoses network routing |
| `lov-skill-creator` / `lov-skill-optimizer` | Create, audit, and version Skills | not composed | Lifecycle tooling, not part of the runtime outcome |

## Atomic Handoffs

```text
optional: lov-iproyal-raylink
  output: verified chained exit in the Clash Verge profile
                |
                v
lov-clash-tun-doctor
  input: an application or site failing behind Clash Verge Rev TUN
  output: diagnosis evidence; optional DIRECT list or WeChat IPv6 repair with a
          backup manifest under <data-dir>/backups/clash-tun-doctor/
```

This Skill owns acceptance of the repair: the live Mihomo rules and IPv6 state
and the user's own application path, not the source configuration alone.

## Overlap Decisions

`lov-iproyal-raylink` also edits Clash Verge, but only the managed block of a
profile script (proxies and groups). This Skill writes only the profile's
`prepend` rules, the generated `clash-verge.yaml`, and the IPv6 override in
`config.yaml`, and keeps its backups in a separate directory, so both can run
on the same profile.

## Composition Decision

Single Skill. Diagnose, DIRECT list, WeChat repair, and rollback share one
runtime context (the Mihomo controller socket and the generated config) and one
acceptance path; none is useful on its own, so a Kit adds nothing.
