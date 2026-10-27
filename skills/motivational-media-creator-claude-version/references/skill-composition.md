# Skill Group Composition

This record is required for every generated Skill. It prevents adjacent Skills
from becoming accidental duplicates or hidden dependencies.

## Nearby Skills Inspected

Inspected 2026-10-25 from the installed catalog by routing description and
actual input/output contract.

| Skill | Classification | Decision |
| --- | --- | --- |
| `lov-motivational-media-creator` | overlap (same outcome) | Built from the same 8 reference videos. It delivers an original production package (script, storyboard, sound design, rights ledger) and stops before rendering. Kept separate on the user's explicit request for a parallel Claude version to compare; the two must not be mixed in one run. |
| `lov-media-crawler` | optional upstream atom | Downloads reference videos or permitted footage from a link. Hands over local media files; this Skill measures them. |
| `lov-voice2srt` | optional upstream atom | Produces timed SRT/JSON transcripts. Hands over the transcript that `study_reference.py --transcript` reads. |
| `lov-fact-check` | optional upstream atom | Verifies a claim before it enters the claims ledger as `verified`. |
| `lov-media-creator` | optional downstream atom | Render and edit executor (Remotion, continuous music bed, subtitles, horizontal/vertical). Receives `timeline.json`, narration script, and the rhythm-and-sound handoff list; owns the rendered file. |
| `lov-logo-sting` | optional downstream atom | Brand outro animation when the user asks for one. |
| `lov-channels-cover` | optional downstream atom | Cover pair for WeChat Channels after the film is approved. |
| `lov-media-publisher` | optional downstream atom | Publishes an approved render; owns platform state. |
| `lov-interview-media-creator` | not composed | Turns one interview into a vertical short with question cards; different film type. |
| `lov-motion-media-creator`, `lov-3d-motion-media-creator` | not composed | No live footage; chapter cards and HUD. Different visual grammar. |
| `lov-branding-consistency` | declared dependency | Gate for audience-visible copy: narration, subtitles, titles, end card. |

## Atomic Handoffs

```text
optional: lov-media-crawler / lov-voice2srt / lov-fact-check
  reference media, timed transcript, verified claims
                |
                v
lov-motivational-media-creator-claude-version
  evidence ledger -> beat sheet (user approves) -> narration script
  -> timeline.json (check_timeline.py valid) -> handoff list
                |
                v
optional: lov-media-creator or the user's Remotion project
  rendered film
                |
                v
lov-motivational-media-creator-claude-version
  render re-measure (study_reference.py --envelope) and status report
                |
                v
optional: lov-channels-cover, lov-media-publisher
```

Acceptance owners: this Skill owns the beat sheet, script, timeline check and
the render re-measure; the executor owns the rendered file; the publisher owns
platform state. A machine re-measure never stands in for a human viewing.

## Overlap Decisions

- `lov-motivational-media-creator` owns the same user-visible outcome. The user
  asked for this second version explicitly, so it is kept as a parallel Skill,
  not merged. Differences: rules here come from per-video measurement and ship
  with runnable measurement and timeline-check scripts; this version covers the
  render re-measure; it does not ship a production-package JSON schema. Which
  version survives, or whether they merge, is the user's decision.
- Reference download, transcription and rendering are reused from the upstream
  and downstream Skills above instead of being re-implemented.

## Composition Decision

**Single Skill.** Study, make and check share one context (the reference
envelope, the archetype rules and the timeline format) and one outcome: a
motivational film whose rhythm is measured against references. The three
scripts are deterministic support for that outcome, not independently useful
stages. All sibling Skills stay optional and artifact-based.
