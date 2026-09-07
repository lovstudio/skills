# Skill Publisher Local Skill Source Standard

This standard covers creation, validation, and local installation. Publication
and channel packaging belong to `lov-skill-publisher`.

## Naming and source

- Local source directory: `<name>-skill`.
- Frontmatter and installed directory: `lov-<name>`.
- Names use lowercase letters, numbers, and single hyphens.
- Source top-level fields are `name`, `description`, `license`, `compatibility`,
  `allowed-tools`, `depends_on`, and `metadata`; version and tags live in
  `metadata`.
- Any Skill that authors or presents audience-visible text declares
  `lov-branding-consistency` in top-level `depends_on`.
- New sources classify normal output in `metadata.content_class` as
  `authored-prose`, `microcopy`, `verbatim`, or `deterministic-output`.

## Content class and authorship

- `authored-prose` covers articles, reports, scripts, letters, and prose where
  the writer's reasoning and editorial decisions are part of the result. It
  requires `lov-branding-consistency` plus
  `references/authorship-integrity.md`.
- `microcopy` covers short audience-visible labels, descriptions, prompts, and
  notices. It requires `lov-branding-consistency` but not a long-form ledger.
- `verbatim` covers transcripts, quotations, legal text, identifiers, and other
  material whose acceptance criterion is source fidelity.
- `deterministic-output` covers structured, operational, retrieval, storage,
  diagnostic, deployment, and binary transformation results.

Authored prose is checked in two layers: trace claims and decisions to an
authorship ledger, then audit discourse before surface polish. Surface metrics
or detector scores are never accepted as proof of authorship.

## Trigger contract

Every Skill has a 50–200 character description, concrete Chinese and English
activation phrases, and explicit non-trigger conditions for adjacent tasks.
Routing language describes user outcomes rather than internal architecture.

## Skill Kits

Use a Kit only for independently useful stages that have their own input/output
contracts and participate in named pipelines. Embed every required module under
`skills/` and declare it in `kit.yaml`. Alternative modes alone do not require a
Kit.

## User Profile contract

Every generated Skill declares `user-profile/v1` in `skill.yaml` and reads the
shared `user`, `brand`, `workspace`, `preferences`, and `skills.<skill_id>`
scopes on every run. Direct user statements intended for future sessions are
written atomically to `skills.<skill_id>.records` or the explicit shared
`user` / `brand` scope. All users and brands share the same portable schema;
`--user-config` is only a compatibility flag for older invocations.

## Local completion

- Standard YAML validation passes.
- Required modules, links, scripts, references, and assets resolve locally.
- Source contains no platform package metadata, private absolute paths,
  placeholders, caches, or compiled Python artifacts.
- The local install path resolves to the source directory.
- Trigger and non-trigger behavior has been exercised.

Passing these gates makes the source eligible for a later publishing workflow;
it does not indicate any remote channel is live.
