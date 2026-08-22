# Skill Group Composition

This record documents the nearby capabilities inspected before creating
`lov-npm-publisher`.

## Nearby Skills Inspected

| Skill | Actual routing contract | Classification |
|---|---|---|
| `lov-npm-config-oidc` | Generated and validated an OIDC workflow for one existing npm package | Deprecated; folded into this Skill |
| `lov-release-via-cicd` | Owns generic versioned CI/CD, GitHub Release, Tauri signing, Changesets, and multi-platform release work | Downstream/adjacent atom |
| `lov-version-management` | Produces Changesets and version/CHANGELOG updates | Optional upstream atom |
| `lov-skill-publisher` | Publishes validated Agent Skills to Skill-specific channels | Not composed |

Inspection used the Skills' `SKILL.md` routing contracts and concrete outputs,
not names alone. `lov-npm-config-oidc` stopped at repository-side OIDC
configuration; its OIDC-workflow generation and registration guidance are now
owned here, alongside new-name bootstrap, bypass publishing, package payload
gates, release execution, and registry readback.

## Atomic Handoffs

- **Optional upstream — `lov-version-management`:** input is a package change;
  output is an approved version and CHANGELOG/Changeset. This Skill consumes the
  resolved version but owns npm release acceptance.
- **Optional downstream — `lov-release-via-cicd`:** input is the verified npm
  workflow plus broader release requirements; output is a general multi-target
  release pipeline. Its acceptance criterion does not replace npm version readback.
- **No handoff — `lov-skill-publisher`:** it publishes Agent Skill sources, not npm
  package tarballs.
- **Folded — `lov-npm-config-oidc`:** its OIDC-workflow generation and npm-side
  registration guidance are owned here; no separate handoff remains.

## Overlap Decisions

The former `lov-npm-config-oidc` overlap is resolved by folding: this Skill owns the
OIDC workflow generation, the `npm trust` registration guidance, and the bypass
publish path as equal modes. It ships its own conservative planner/writer so it
remains portable. Its distinct core outcome is the complete state machine from a
possibly nonexistent npm name through `verified-live`, including first-publish
bootstrap and immutable-version checks.

Generic versioning and CI remain outside the core. The Skill consumes their
artifacts when present and does not duplicate Tauri signing, GitHub Release assets,
or Agent Skill marketplace publication.

## Composition Decision

**Single Skill.** Bootstrap, OIDC setup, bypass publishing, release gating,
triggering, and readback are modes of one user-visible outcome: an npm package
version that can be published without repeated login and is independently verified
live. They share one package, repository, workflow, and acceptance boundary;
separate embedded modules would add ceremony without independent value.
