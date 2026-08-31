# Skill Card — lov-create-qrcode

## Description

`lov-create-qrcode` turns a URL or UTF-8 text into a styled QR PNG, reuses durable visual
preferences, and can scan the finished image to prove exact payload equality. Its default output
is the code alone, without a header, footer, title, visible payload, or poster frame.

## Owner

LovStudio maintains the Skill. Product information is available at
[lovstudio.ai](https://lovstudio.ai).

## License / Terms

The source is MIT licensed. Users remain responsible for the legality and safety of the encoded
content and for permission to use supplied Logos or trademarks.

## Use Case

The Skill is for people or agents that need a local, repeatable QR workflow rather than a one-off
web generator. It accepts a positional value, stdin, or a UTF-8 file and produces a PNG plus an
optional JSON verification receipt.

## Deployment Geography

It runs locally in any geography and makes no network request during generation or verification.

## Requirements / Dependencies

- Python 3.10 or newer
- `qrcode` 7.4 or newer and Pillow 9 or newer
- OpenCV Python for real `scan` verification
- `lov-branding-consistency` for audience-visible poster text
- No credential, browser, hosted service, or sibling Skill is required

## Known Risks and Mitigations

- Low contrast, small modules, heavy damage, or Logo occlusion can break scanning. The CLI gates
  contrast, preserves at least four quiet-zone modules, requires H correction for Logos, and can
  compare a real decode to the exact input.
- Private payloads can leak through terminal history or visible poster text. The workflow prefers
  stdin, never writes payloads to Profile or JSON, and makes visible disclosure opt-in.
- A valid QR code can still point to a harmful destination. Generation is not an endorsement or
  safety review of the encoded content.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Style and verification contract](references/style-contract.md)
- [Skill composition record](references/skill-composition.md)

## Skill Output

The normal output is a non-overwriting PNG. `--poster` adds Warm Academic card framing, optional
title, and optional visible payload. `--json` reports absolute path, image dimensions, output hash,
payload length and hash, effective style, Profile sources, and the actual verification level.

## Skill Version

0.1.1

## Ethical Considerations

The Skill minimizes disclosure but cannot judge the truth, safety, or ownership of supplied content.
Do not use it to disguise malicious links, impersonate a brand, or expose private credentials.

## LovStudio Evidence

### User Cases

[`cases/cases.json`](cases/cases.json) records both the default bare-code path and the explicitly
requested poster path for the public LovStudio site. Both are verified by exact OpenCV decode
comparison.

### Dimension Map

The machine-readable card tracks encoding correctness, preference fidelity, payload privacy, and
local portability with named evidence. Scores reflect the current verified v0.1.1 implementation,
not a guarantee for arbitrary printers, cameras, damage, or custom colors.

### Pricing Basis

The Skill is free because encoding and verification are deterministic local operations. The free
boundary excludes hosted redirects, analytics, publication, and remote asset acquisition.

### Distribution

The current evidence is `local-installed`. GitHub, LovStudio, WorkBuddy, and SkillPay have not been
published or verified in this creation workflow.
