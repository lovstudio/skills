# Skill Group Composition

Inspection of the installed skill group against this skill's input/output
contract: input is a goal plus optional constraints; output is a decision that
either adopts an existing plugin with a usage path or produces a new-plugin
brief based on the closest open source.

## Nearby Skills Inspected

- dsh-search-plugin — sibling created in the same request: search-only stage
  over the same gateway. Its ranked JSON is an optional artifact-level input
  here, and its search procedure is embedded below to keep this source
  self-contained.
- dsh-plugin-creator — downstream atom: accepts a new-plugin brief and authors
  the plugin package end-to-end in the deepseek-harness repo, running its own
  gates.
- dsh-plugin-publisher — downstream atom: publishes a finished plugin to npm,
  git, or tarball; out of scope until a plugin exists.
- find-skills — discovers and installs Claude agent skills, not DSH plugins;
  different outcome domain.
- lov-skill-creator — creates portable local agent Skills; different outcome
  domain.
- dsh-pre-push-checks, dsh-prose-standard, dsh-code-review — repo gate skills;
  not composed with the use-or-create decision.

## Atomic Handoffs

- upstream, optional: dsh-search-plugin JSON artifact — the ranked candidate
  list from an earlier search-only run; when absent, run the embedded Step 2
  procedure against the same gateway.
- core: dsh-search-or-create-plugin owns the decision outcome: a verdict per
  candidate (MATCH / PARTIAL / NO-MATCH) with gateway-field evidence, and the
  chosen path.
- downstream, optional: dsh-plugin-creator consumes the new-plugin brief (goal,
  required capabilities, closest base implementations, gaps) and produces the
  package source; dsh-plugin-publisher consumes the finished package.
  Acceptance for the create path is dsh-plugin-creator's own gate, not this
  skill's.

## Overlap Decisions

- The search stage is intentionally embedded with the same gateway contract as
  dsh-search-plugin because search is a hard prerequisite of the decision
  outcome; relying on an external sibling would make this source
  non-portable. The decision stage is not duplicated anywhere.
- dsh-plugin-creator's creation domain overlaps only as the downstream
  handoff; this skill does not author package code itself.

## Composition Decision

Single Skill, self-contained. The workflow has two stages, but the second is a
hard prerequisite of the outcome and both share one context; per the kit rule,
hard-coupled stages for one user-visible result are embedded rather than split
into external siblings. Two standalone skills with embedded search is the
chosen shape because the user wants two independently triggerable outcomes:
search-only (dsh-search-plugin) and decide-or-create (this skill). No
kit.yaml.
