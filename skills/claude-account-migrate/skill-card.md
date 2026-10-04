# Claude 换号搬家 · Claude Account Mover · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note.

## Description

After a user signs in to the Claude desktop app with a different account, the
Skill copies the old account's Code-tab and Cowork sessions into the current
account so they appear in the sidebar and can be resumed. It flags title-only
sessions whose transcripts were already cleaned up, and raises transcript
retention so migrated Cowork sessions are not deleted by the 30-day default.

## Owner

LovStudio Skill contributors; maintained by the local source maintainers.

## License / Terms

MIT. Use, modify, and redistribute under the included [LICENSE](LICENSE).

## Use Case

Claude desktop users who retired an old account and want its local sessions
under the new account without signing back in. Tasks: scan accounts, plan and
apply an additive copy, skip orphans, protect Cowork transcripts.

## Deployment Geography

Global; runs only on the user's own machine. Verified with the macOS desktop app.

## Requirements / Dependencies

No credentials. Python 3.9+ standard library and access to the local Claude
desktop data directory.

## Known Risks and Mitigations

- Undocumented storage layout may change: plan mode by default, additive copy,
  source never modified.
- Some migrated Cowork sessions still write to the source folder: reported, and
  the user is told to keep that folder.
- Title-only sessions: detected by transcript presence and skipped by default.
- 30-day transcript cleanup: warned for the CLI, fixed inside copied Cowork sessions.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Claude desktop session storage](references/desktop-storage.md)

## Skill Output

Copied session entries and folders under the target account, plus a plain-text
or JSON report. Accepted when a second plan reports nothing left to copy, target
files are unchanged, the source is untouched, and the app lists a migrated session.

## Skill Version

0.1.0

## Ethical Considerations

Works only on the local user's own files. Never reads or moves credentials,
tokens, or Keychain items and never sends data off the machine. Emails are shown
only when they can be attributed to one account unambiguously.

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json): two retired accounts, 231 Code and 77
Cowork sessions copied, 108 orphans identified, retention fixed on 77 sessions.

### Dimension Map

Safe copy, sessions usable after switching, and transcript protection, each with
fixture or real-run evidence in `skill-card.yaml`.

### Pricing Basis

Free. See [`pricing-card.yaml`](pricing-card.yaml).

### Distribution

Paid channels `workbuddy` and `skillpay`: not planned. Free channels: `github`
not published, `lovstudio` local only.
