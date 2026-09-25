# 生产就绪助手 · Production Readiness · Skill Card

## Description

Turns a development workspace into a scoped, verifiable production artifact or local installation. It distinguishes a local build from a public release and does not publish externally without explicit authorization.

## Owner

LovStudio — local Skill source.

## License

MIT. See [LICENSE](LICENSE).

## Use Case

For developers who need to prepare an existing Tauri, Electron, native desktop, or Web project for a production build, a local application install, or a later release handoff.

## Deployment Geography

Global local-agent use. The Skill itself does not deploy anything remotely.

## Requirements

Python 3.8+ standard library for the audit helper, plus the target project's build, signing, and platform verification tools when applicable. No credential is required for the Skill source itself.

## Known Risks

- A development preview can look successful without creating a production artifact; the workflow requires the target production command and native checks.
- Replacing an installed application can lose a known-good bundle; the local-install workflow requires explicit authority and a recoverable prior bundle.
- A local result can be confused with a public release; remote mutation stays with the dedicated release Skills.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Production readiness checklist](references/production-readiness.md)
- [Composition record](references/skill-composition.md)
- [User Profile contract](references/user-profile.md)

## Skill Output

A production-readiness report, verified artifact or local-install evidence, and an optional artifact-level release-handoff summary. Outputs can be Markdown, JSON, and platform-native verification evidence.

## Skill Version

0.1.0

## Ethical Considerations

The Skill never outputs secrets, uploads project data, or claims an external release from a local artifact. It requires explicit authority before replacing local applications or invoking publication workflows.

## User Cases

The initial Vmux case turned a Tauri desktop development workspace into a locally installed, notarized macOS application. It completed the production build, passed 18 native tests, passed code-signing and Gatekeeper checks, and matched the installed executable digest to the staged artifact. See [cases/cases.json](cases/cases.json).

## Dimension Map

| Dimension | Current state | Evidence |
| --- | --- | --- |
| Artifact integrity | Verified in initial local case | Production bundle passed macOS signing, notarization, Gatekeeper, and digest comparison. |
| Scope clarity | Implemented | Workflow divides local install, distributable artifact, and external release authority. |
| Minimal change path | Implemented | The audit helper is read-only and implementation preserves development commands and unrelated worktree changes. |
| Installation safety | Verified in initial local case | Prior local bundle was moved to a recoverable location before replacement. |

## Pricing Basis

Free for local-agent use. It supplies reusable local readiness guidance and audit tooling, not managed infrastructure or paid publication services. Reassess only if managed cloud execution, compliance automation, or support obligations are added.

## Distribution

- Local agent: installed and verified locally.
- WorkBuddy: not published.
- SkillPay: not published.
- GitHub: not published.
- LovStudio catalog: not published.
