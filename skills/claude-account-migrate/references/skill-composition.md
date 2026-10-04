# Skill Group Composition

## Nearby Skills Inspected

| Skill or tool | Routing contract | Classification | Decision |
| --- | --- | --- | --- |
| `lov-cc-mv` | Moves or renames a project folder and migrates its Claude Code transcripts, prompt history and running-session records by path. | not composed | Works on the shared `projects/` store keyed by path. This Skill works on the account-scoped desktop index and never changes paths. Run `lov-cc-mv` separately when a project folder also moved. |
| `lov-claude-session-stat` | Summarizes one Claude Code session from local transcripts and desktop metadata. | optional downstream atom | Can read a migrated session afterwards; no handoff is required. |
| `lov-search-chat`, `session-logs` | Recall or search past conversations from local indexes or logs. | not composed | Read-only search; they do not depend on which account owns the sidebar entry. |
| `lov-clean-mac` | Plans storage cleanup and archiving. | not composed (risk note) | A cleanup must not delete a source account folder that migrated Cowork sessions still write to; this Skill reports that condition. |
| CC Switch (external app) | Switches API providers and writes Claude Code settings or a Claude Desktop third-party profile. | not composed | Provider switching never touches account-scoped session folders, so it cannot carry sessions between accounts. |

## Atomic Handoffs

```text
lov-claude-account-migrate
  input: two accounts in the local Claude desktop store
  output: target account folders containing copied session entries
          + Cowork retention settings + a plan/apply report
                |
                v
optional: lov-claude-session-stat (inspect a migrated session)
```

There is no upstream atom. The core outcome — old sessions visible and resumable
under the current account — is owned and accepted here.

## Overlap Decisions

No existing Skill owns account-to-account session migration. `lov-cc-mv` is the
nearest neighbour, but its unit is a filesystem path, not an account; extending
it would mix two unrelated storage models.

## Composition Decision

Single Skill. Scanning, planning, copying and retention protection are one
outcome served by one deterministic CLI.
