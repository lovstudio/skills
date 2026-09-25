# Agent 对话界面 · Agent Chat UI · Skill Card

## Description

Integrates reusable Agent transcript and composer components into an existing React Native/Expo or React app. It includes a normalized data boundary, accessible UI templates, deterministic scaffolding, and recovery-focused verification.

## Owner

Maintained by LovStudio contributors through the local Skill source.

## License / Terms

MIT applies to the Skill instructions, scripts, and original templates. Target applications and third-party dependencies retain their own licenses and obligations.

## Use Case

For product teams that already have, or will separately provide, an Agent transport and need message history, assistant phases, tool progress, session state, structured questions, Markdown, attachments, sending, and safe retry behavior in the host UI.

## Deployment Geography

Runs locally and is suitable for global React Native/Expo and React Web applications. The host remains responsible for regional data handling, provider availability, and compliance.

## Requirements / Dependencies

- Python 3.8 or newer for audit, scaffolding, and structural verification.
- A target React Native/Expo or React + TypeScript project.
- No Skill credential. Host model/API credentials remain outside the UI and this source.

## Known Risks and Mitigations

- Provider payload leakage: normalize once and remove orchestration-only metadata before display.
- Duplicate retry: keep a stable client request ID and clear the draft only after confirmed success.
- Host overwrite: scaffold refuses occupied targets; integrate with existing tokens and conventions.
- Unsafe model links/content: allowlist link protocols and never render arbitrary HTML.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Integration contract](references/integration-contract.md)
- [Yoda mobile patterns](references/yoda-mobile-patterns.md)
- [Acceptance checklist](references/acceptance-checklist.md)

## Skill Output

The output is TypeScript/TSX component source, CSS for React Web, a host adapter, and a verification report. The caller controls target path, detected/explicit stack, theme tokens, and localized copy. Completion requires structural verification, host quality gates, and a real conversation-state exercise.

## Skill Version

0.1.0

## Ethical Considerations

Never expose credentials, hidden prompts, internal memory metadata, private paths, or untrusted HTML. Respect user draft ownership, accessibility, privacy, copyright, localization, and the host's retention policies.

## LovStudio Evidence

### User Cases

[`cases/cases.json`](cases/cases.json) records the initial real request and the resulting local Skill/component assets. It does not claim a production app integration that has not occurred.

### Dimension Map

- Agent semantic coverage: evidence exists in shared types/model and the integration contract; no numeric score is claimed.
- Platform portability: evidence exists in shared logic plus React Native and React renderers; no numeric score is claimed.
- Recovery safety: evidence exists in the send/retry contract and composer behavior; no numeric score is claimed.
- Accessibility: evidence exists in component semantics and the acceptance checklist; no numeric score is claimed.

### Pricing Basis

The initial source is free to maximize reuse and collect real integration evidence. It excludes provider backends, bespoke visual design, remote publication, and support guarantees. Pricing should be reviewed if maintained packages or guaranteed support are added.

### Distribution

- WorkBuddy: not published.
- SkillPay: not published.
- GitHub: not published.
- LovStudio: local install only.
