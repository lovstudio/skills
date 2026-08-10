# Skill Publisher Local Skill Source Standard

This standard covers creation, validation, and local installation. Publication
and channel packaging belong to `lov-skill-publisher`.

## Naming and source

- Local source directory: `<name>-skill`.
- Frontmatter and installed directory: `lov-<name>`.
- Names use lowercase letters, numbers, and single hyphens.
- Source top-level fields are `name`, `description`, `license`, `allowed-tools`,
  and `metadata`; version, compatibility, tags, and dependencies live in
  `metadata`.

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
