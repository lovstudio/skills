# Skill Card — lov-lovpen-add-wechat-channel-comp

## Description

Normalizes one WeChat Channels DOM or Lovpen DSL and renders it into canonical Markdown,
native component HTML, or one explicitly marked position in an existing document.

## Owner

LovStudio contributors — <https://lovstudio.ai>

## License / Terms

MIT. Users remain responsible for rights to the referenced video, cover, avatar, and article
content. Structural conversion does not grant publication rights.

## Use Case

Writers, editors, developers, and agents can take one copied `mp-common-videosnap` DOM or one
Lovpen video directive and insert a verified component into Markdown or HTML without carrying the
large editor-generated DOM through the source document.

## Deployment Geography

Global, local execution only.

## Requirements / Dependencies

- Python 3.8 or newer and UTF-8 filesystem access.
- Python standard library only for rendering.
- PyYAML only for the full Skill source validator.
- No browser, network, account, Cookie, token, or API credential.

## Known Risks and Mitigations

- Malformed or unrelated DOM is rejected unless exactly one custom element and every canonical
  field pass validation.
- Existing documents are changed only when exactly one explicit marker is present; writes are
  atomic.
- Expired media URLs and publication rights remain downstream concerns and are never inferred from
  structural validity.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Component contract](references/component-contract.md)
- [Composition record](references/skill-composition.md)
- [Verified case](cases/cases.json)

## Skill Output

The Skill returns a canonical one-line Lovpen directive, a native `mp-common-videosnap` fragment,
or an atomically updated `.md` or `.html` file. JSON mode reports schema, input kind, output format,
bytes, SHA-256, component ID, output path, and write state.

## Skill Version

0.1.1

## Ethical Considerations

All transformation stays local. The Skill does not upload source DOM, identifiers, media URLs, or
article text. It does not establish ownership, continued media availability, mobile playback, or
remote publication state.

## LovStudio Evidence

### User Cases

[`cases/cases.json`](cases/cases.json) records the real-input verification, minimum prompt,
redacted portable fixture, generated Markdown and HTML artifacts, hashes, and test results. The
original component identifiers and signed media URL are not copied into the Skill source.

### Dimension Map

- Component contract fidelity: real DOM round-tripped through the canonical DSL.
- Native HTML integrity: one custom element, 11 key attributes, and declarative Shadow DOM.
- File-write safety: exact-marker atomic replacement.
- Portability: six focused standard-library tests passed.

### Pricing Basis

The local release is free because it uses no hosted compute or paid service. See
[`pricing-card.yaml`](pricing-card.yaml) for scope and review triggers.

### Distribution

Locally installed for LovStudio. GitHub, WorkBuddy, and SkillPay are not published.
