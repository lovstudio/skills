# Skill Group Composition

Inspection of the installed skill group against this skill's input/output
contract: input is a goal or keyword plus optional filters; output is a ranked,
evidence-tagged plugin candidate list with gateway provenance.

## Nearby Skills Inspected

- dsh-search-or-create-plugin — sibling created in the same request: searches
  the same gateway, then decides use-or-create; it may consume this skill's
  ranked JSON artifact as an optional upstream handoff.
- dsh-plugin-creator — authors a new DSH plugin package end-to-end in the
  deepseek-harness repo; it consumes search findings as base-implementation
  evidence, but never searches the gateway itself.
- dsh-plugin-publisher — publishes a finished plugin to npm, git, or tarball;
  no search contract.
- find-skills — discovers and installs Claude agent skills, not DSH plugins;
  different outcome domain.
- lov-skill-creator — creates portable local agent Skills; different outcome
  domain.
- dsh-pre-push-checks, dsh-prose-standard, dsh-code-review — repo gate skills;
  not composed with plugin search.

## Atomic Handoffs

- upstream: none. The gateway is an external data source, not a sibling skill.
- core: dsh-search-plugin owns the search outcome: an evidence-tagged, ranked
  plugin list plus the raw gateway JSON.
- downstream, optional: dsh-search-or-create-plugin accepts the raw JSON
  artifact (or re-runs the same procedure) for fit analysis; dsh-plugin-creator
  accepts the candidate list as base-implementation evidence. Each handoff is
  artifact-level, never a hidden runtime dependency.

## Overlap Decisions

- dsh-search-or-create-plugin embeds the same search procedure rather than
  importing this skill, so it stays self-contained; this skill remains the
  dedicated search-only entry point. No duplicated ownership: this skill owns
  search-only outcomes, the sibling owns the decision outcome.

## Composition Decision

Single Skill. One user-visible outcome (ranked search results) with one
input/output contract and no independently triggerable second stage inside
this source; therefore no kit.yaml and no embedded modules.
