# Codeex 插件工坊 · Codeex Plugin Studio · Skill Card

## Description

Creates and validates independent Codeex runtime plugins, including staged
renderer hooks, launch hooks, authenticated control routes, native UI matching,
and reload-boundary evidence.

## Owner

Maintained by LovStudio Codeex contributors. Contact the Codeex maintainers for contract changes.

## License / Terms

MIT. Target applications and plugin dependencies retain their own license terms.

## Use Case

For developers and agents turning a capability brief or an existing Codeex modification into a self-contained runtime plugin. Inputs are a Codeex repository, plugin outcome, hook boundary, and permissions. The output is plugin source plus lifecycle evidence.

## Deployment Geography

Global, local-first use in Codeex source repositories, isolated smoke profiles, and explicitly authorized managed production wrappers.

## Requirements / Dependencies

- Python 3.8 or newer.
- Node.js 24 or newer.
- A Codeex repository exposing the audited local plugin contract.
- No credentials or remote service.

## Known Risks and Mitigations

- Live DOM mutation can damage official UI. Use staged transforms and verify official tabs recover.
- Approximate icons and surfaces can drift from the adjacent native control. Inspect and reuse packaged DOM/SVG before styling a fallback.
- A restarted Electron runtime can still talk to stale backend code in the long-lived launcher service. Reload and read back the control route separately.
- Desired state can be mistaken for runtime activation. Report installed, prepared, active, and verified separately.
- Destructive uninstall can remove source or data. This Skill only disables a plugin; deletion is outside the lifecycle command.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Codeex plugin contract](references/plugin-contract.md)
- [Atomic lifecycle](references/atomic-lifecycle.md)
- [Lifecycle evidence](cases/evidence/lifecycle-report.json)

## Skill Output

Produces `plugin.json`, an ESM hook entry, declared permissions, focused
validation results, reload-boundary guidance, desired-state transitions,
active-state evidence, and a rollback report. The portable CLI recognizes
`transformWebview`, `beforeLaunch`, and `handleControlRequest`.

## Skill Version

0.2.0

## Ethical Considerations

Do not conceal permissions, persist credentials, inject surveillance, bypass host authorization, or claim activation without runtime evidence. Respect upstream Codex and third-party terms.

## LovStudio Evidence

### User Cases

[`cases/cases.json`](cases/cases.json) records the real request and the lifecycle exercise produced against the current Codeex contract.

### Dimension Map

- Contract correctness: manifest, entry, all three hook types, desired state, and failure preservation passed the stored exercise.
- Lifecycle reversibility: source staging, duplicate transitions, uninstall, and non-live-state exercise passed.
- Routing clarity: the composition record separates Codeex runtime plugins from adjacent plugin systems.
- Reload fidelity: the development loop distinguishes renderer/runtime restart from launcher/control-service reload and requires packaged readback.

### Pricing Basis

Free local developer infrastructure. See [`pricing-card.yaml`](pricing-card.yaml) for value, boundary, and review trigger.

### Distribution

- Local: installed and verified.
- GitHub: not published.
- LovStudio: not published.
- WorkBuddy: not published.
- SkillPay: not published.
