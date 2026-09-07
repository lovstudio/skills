# Slash command migration

Migrate raw command Markdown, nested command directories, aliases, and partially
wrapped SKILL.md files. A renamed command is not a completed portable Skill.

## Inventory and identity

Run `scripts/migrate_command.py inventory` with explicit `--command-root` roots
and optional `--source-root` roots. Repeat flags for active commands, archives,
and project commands. Reports are local audit data; keep them outside published
source. The scanner never executes command content or rewrites input files.

Read each command and its referenced scripts/assets before choosing a target.
Compare existing Skill input/output contracts. Upgrade the canonical source for
an existing capability; map obsolete names and aliases to it instead of creating
duplicates. Keep ambiguous matches unresolved. Record every input, target,
decision, validation result, local install, and requested channel independently.

## Prepare and upgrade

For a new capability, use `scripts/migrate_command.py prepare INPUT --output
WORK_AREA --name NAME --content-class CLASS`. This creates an isolated scaffold,
an exact original outside that scaffold, and a migration report. It does not
install or publish. An occupied output is rejected. Existing Skills are upgraded
in place after reviewing their dirty state; preserve unrelated edits and history.

Apply these semantic transformations, rather than copying the old prompt:

| Legacy feature | Portable behavior |
| --- | --- |
| Slash path and aliases | Natural Chinese/English triggers; record legacy names as migration history, never as required runtime dispatch. |
| Host invocation/model/agent flags | Remove source-only host switches; translate their intent into ordinary workflow boundaries. Never remove an approval boundary merely to enable automatic discovery. |
| Argument and positional substitutions | Define named inputs, defaults and required-value handling in prose or CLI flags. Never assume host interpolation. |
| Implicit file mentions | Explicitly read a project-relative path; resolve bundled resources from the Skill directory. |
| Inline shell expansion | Describe an explicit read-only command with purpose; inspect before execution. |
| Host-specific tools | State the operation and use the current host's actual file/search/CLI tools. Keep technical runtime dependencies explicit. |
| Private paths, user facts, invented domains | Use project discovery and the shared Profile. Preserve real public sources; never replace a missing URL with a fabricated homepage. |
| Hidden sibling commands | Prefer optional artifact handoffs; embed required stages in a Kit when they own one composite outcome. |

Preserve safeguards, licensing, source attribution, useful examples, scripts and
assets. Do not upload raw archived commands containing private context. Reuse
verified advanced Skills for old aliases rather than regressing them to old code.
Do not mutate a business system simply to demonstrate that a migrated Skill works.

## Acceptance and publication

Apply the normal creator gates: routing, Profile, dependencies, composition,
README/version/changelog, references, real case and source validation. A migration
or read-only preview case is evidence of that limited result, never evidence of
an external business write. Record untested runtime branches honestly.

Install through a shared canonical Skill directory and host adapters; verify
their resolved targets. Retain original commands unless removal is requested.
When the user requests website synchronization, hand each validated source and
the complete mapping to `lov-skill-publisher` within that authorization. Verify
the exact catalog version, public detail content and isolated installation for
every published capability. Unselected channels remain unselected. A broken item
must be visible in the batch report and must not erase successful results.

## Format sources

The [Agent Skills specification](https://agentskills.io/specification) defines the
portable base. LovStudio additionally requires its Profile, card and dependency
contracts; these extensions must not become a dependency on a particular host.
