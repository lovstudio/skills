# Skill Group Composition

## Nearby Skills Inspected

| Skill | Classification | Decision |
| --- | --- | --- |
| `lov-dev-blog` | required downstream atom (`depends_on`) | Owns the website blog publishing contract. `deep-research` runs its research-artifact sync as the Phase 8 completion gate and never redefines publishing semantics. |
| `lov-branding-consistency` | required dependency (`depends_on`) | Branding contract for authored, reader-visible report prose. Quotes, citations, source data, repository identifiers, and code stay untouched. |
| `lov-dev-research` | adjacent atom | Turns a software requirement into reuse strategy, technology choices, and a development plan. `deep-research` produces general citation-tracked reports and does not replace that planning outcome. |
| `lov-solution-architect` | optional downstream atom | Builds product or technical solution plans and can consume a finished research report as evidence. It is not invoked from this pipeline. |
| `lov-fact-check` | adjacent atom | Verifies one user-supplied claim. `deep-research` keeps its own claim ledger and claim-support verification across a whole report. |
| `autoglm-deepresearch` | overlapping alternative | A lighter search-and-summarize flow without the persisted source, evidence, and claim ledgers. Not composed. |
| `lov-professional-infographic`, `baoyu-diagram` | optional downstream atoms | Can turn finished findings into standalone exhibits. In-report figures stay governed by `reference/rich-media.md`, so neither is a hidden requirement. |
| `md2pdf` | not composed | `deep-research` ships its own Markdown to HTML and WeasyPrint PDF path for reports. |

## Atomic Handoffs

```text
deep-research   (authored prose follows lov-branding-consistency)
  Markdown report + sources.jsonl + evidence.jsonl + claims.jsonl
  + run_manifest.json + figures/ + HTML + PDF
                |
                v
required gate: lov-dev-blog
  research-artifact sync to the website blog, unless the user keeps it private
                |
                v
optional: lov-solution-architect, lov-professional-infographic
  solution plans or standalone exhibits built on the finished report
```

`deep-research` owns scoping, retrieval, triangulation, evidence persistence,
claim verification, report assembly, and local validation. `lov-dev-blog` owns
remote publishing state.

## Overlap Decisions

`deep-research` does not invoke every nearby Skill. Single-claim checks stay
with `lov-fact-check`, development planning stays with `lov-dev-research`, and
solution design stays with `lov-solution-architect`. Each of them may consume a
finished report at the artifact boundary, but none becomes a prerequisite for
running research.

## Composition Decision

`deep-research` remains a **Single Skill**. Its reference files, templates,
validators, and converters are implementation support for one outcome: a
citation-tracked, validated research report package. Publishing and brand review
are declared in `depends_on`; downstream planning and exhibit Skills remain
optional atoms.
