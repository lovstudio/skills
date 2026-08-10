# Skill Group Composition

## Nearby Skills Inspected

| Skill | Classification | Decision |
| --- | --- | --- |
| `lov-skill-optimizer` | optional downstream atom | Reviews or refines an already-created Skill source; it does not replace creation, validation, or installation. |
| `lov-skill-publisher` | optional downstream atom | Publishes a validated local source to remote channels; it consumes the source produced here and owns external distribution state. |
| `lov-skill-installer` | adjacent atom | Installs an existing Skill when no source generation is needed. This creator installs its own newly generated source directly, so the two workflows stay distinct. |
| `lov-app-generator` and domain Skills | not composed | These are potential products of the creator, not prerequisites for all Skill generation. |

## Atomic Handoffs

```text
lov-skill-creator
  validated portable local Skill + local install link
                |
                v
optional: lov-skill-optimizer
  reviewed or improved source
                |
                v
optional: lov-skill-publisher
  channel-specific publication and remote verification
```

The creator owns source shape, Profile contract, trust records, group
composition analysis, local validation, and local discoverability. Publisher
owns remote catalog, package, upload, and live-channel state.

## Overlap Decisions

The creator does not invoke every nearby Skill. It inspects the local group to
avoid duplicate outcomes, then records optional handoffs at artifact boundaries.
It never makes unrelated sibling Skills a hidden requirement. If a new result
requires tightly coupled independently useful stages, their modules must be
embedded in one self-contained Skill Kit.

## Composition Decision

`lov-skill-creator` remains a **Single Skill**. Its deterministic initializer,
validator, Profile helper, and templates are implementation support for one
outcome: a validated and locally discoverable portable Skill source. Remote
publishing and later source optimization remain optional downstream atoms.

