# Skill 透视镜 · Skill Lens · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

`lov-skill-visualizer` transforms a local Agent Skill into a restrained,
scenario-first trust brief. It explains when the Skill is worth using, exposes
its complete input-to-outcome transformation without an evidence-explorer UI,
then preserves source, supporting capability, checks, and effect gaps for review.

## Owner

Maintained by the LovStudio Skill maintainers through the source repository.

## License / Terms

MIT. Use, modify, and redistribute the source while retaining the license notice.

## Use Case

Skill authors, reviewers, maintainers, and catalog operators supply one local
Skill directory or `SKILL.md`. The Skill separates external routing from
internal runtime, then extracts step details, conditions, Profile context,
dependencies, Kit sub-workflows, quality gates, and local resources for review.

## Deployment Geography

Global, in a local Agent Skill runtime or developer command line.

## Requirements / Dependencies

Python 3.8 or newer, PyYAML, and the packaged Mermaid 11.12.2 browser runtime.
No credential, network connection, Mermaid CLI, or sibling Skill is required.

## Known Risks and Mitigations

- Static extraction may omit logic hidden in prose, code, or remote tools. The
  report only promotes explicit declarations and preserves coverage diagnostics.
- Recursive references might escape the Skill or reveal a private canonical
  path. The extractor rejects out-of-root resources and stores relative paths.
- A diagram, source citation, or quality gate can be mistaken for runtime proof.
  Every report keeps declarations, support, acceptance rules, observed artifacts,
  and step-bound effect evidence separate.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Logic model contract](references/logic-model.md)
- [Real Skill Creator case](cases/artifacts/skill-creator-logic.md)
- [Standalone HTML case](cases/artifacts/skill-creator-logic.html)

## Skill Output

The primary output is standalone offline HTML with a concrete use scenario,
Before → transformation → After summary, fully visible pipeline, deliverables,
and trust boundary. No node clicking, dragging, zooming, or tab switching is
required. Rendered Mermaid graphs, external activation, raw source, resources,
diagnostics, and embedded `lovstudio/skill-logic/v1` JSON stay secondary.

## Skill Version

0.6.0

## Ethical Considerations

Analyze only user-scoped local material, do not execute target code, avoid
absolute-path leakage, and do not present inferred behavior as authored fact.

## User Cases

The first real case visualizes `lov-skill-creator`; see
[`cases/cases.json`](cases/cases.json), its
[Mermaid report](cases/artifacts/skill-creator-logic.md), and its
[JSON model](cases/artifacts/skill-creator-logic.json). The same case also has a
[standalone HTML review](cases/artifacts/skill-creator-logic.html).

## Dimension Map

- Extraction correctness: verified with a focused fixture and the real case.
- Trust insight: verified by reading the concrete scenario and complete pipeline,
  then checking source, capability basis, quality gates, and explicit effect gaps.
- Local repeatability: verified through the standalone CLI and unittest suite.
- Boundary honesty: verified through coverage and diagnostic preservation.

Scores remain unassigned rather than manufacturing a numeric rating from one case.

## Pricing Basis

Free local developer infrastructure. It includes static extraction, standalone
trust brief, linear internal workflow, Kit sub-workflows, quality
gates, JSON, diagnostics, tests, and documentation. Target execution, step-bound
effect capture, semantic repair, hosted rendering, and publication are excluded. See
[`pricing-card.yaml`](pricing-card.yaml).

## Distribution

- WorkBuddy paid channel: not published.
- SkillPay paid channel: not published.
- GitHub free channel: not published.
- LovStudio free channel: local installation verified through the shared Agent link.
