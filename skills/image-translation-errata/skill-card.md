# Skill Card — lov-image-translation-errata

## Description

This Skill verifies source text and an existing machine translation, then
produces a proofreader-style corrected image. The decisive old error remains
visible under a strikethrough, the correct wording appears beside it, and the
source image's layout and identity remain the acceptance baseline.

## Owner

Maintained by LovStudio Skill contributors through the local source.

## License / Terms

MIT. Users remain responsible for having the right to edit and redistribute the
supplied image.

## Use Case

Editors, localization teams, product communicators, and readers can provide a
screenshot containing source text plus an awkward or misleading automatic
translation. The Skill returns a source-backed correction map and a marked-up
raster that exposes the old error without redesigning the screenshot.

## Deployment Geography

Global. It runs in an agent environment with vision and reference-image editing.

## Requirements / Dependencies

- Vision capability for the supplied raster.
- Reference-image editing capability for final output.
- Primary-source or web access when product terms or current facts require it.
- No mandatory credential, Python package, or sibling Skill.

## Known Risks and Mitigations

- Context-free translation can be fluent but wrong; verify terms and pragmatic
  meaning before editing.
- Generative editing can redraw untouched content; lock and re-check every
  invariant after rendering.
- Excessive markup can overwhelm the screenshot; strike only decisive fragments
  and omit redundant labels by default.
- Do not persist private image contents or assume redistribution rights.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Errata protocol](references/errata-protocol.md)
- [Verified case](references/verified-case.md)
- [Composition analysis](references/skill-composition.md)

## Skill Output

The primary output is a PNG or source-compatible raster. A concise correction
brief records old wording, replacement wording, reasoning, and evidence. The
image passes meaning, error-visibility, independent-reading, layout-fidelity,
and character-fidelity gates.

## Skill Version

0.1.0

## Ethical Considerations

The Skill corrects language rather than attacking translators. It does not
invent source meaning, persist private screenshots, remove attribution, or grant
rights to redistribute third-party material.

## LovStudio Evidence

### User Cases

[`cases/cases.json`](cases/cases.json) and
[`references/verified-case.md`](references/verified-case.md) record the real
Codex banked-reset screenshot workflow and the user's refinement that a visible
strikethrough does not need an additional “勘误” label.

### Dimension Map

The machine-readable card records semantic correctness, machine-error
visibility, layout fidelity, and editorial restraint. Layout fidelity remains
provisional until deterministic pixel-diff verification is added.

### Pricing Basis

The local Skill is free because its value lies in a portable editorial method,
not proprietary infrastructure. See [`pricing-card.yaml`](pricing-card.yaml).

### Distribution

The source is local-only. GitHub, WorkBuddy, SkillPay, and remote LovStudio
publication have not been performed.
