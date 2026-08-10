# Simplified Chinese Subtitle Handoff

Media Fetch owns the exact-release match and the final media report. The companion
`lov-subtitle-freedom-skill` is a subtitle operation, not a release identity oracle.
Use this boundary when the selected media has English subtitles but no `zh-Hans` track.

## Handoff contract

1. Match the subtitle to the exact release using file identity, runtime, frame rate,
   scene boundaries, or several synchronized cues. A language label alone is weak
   evidence.
2. Keep the original video and embedded tracks untouched. Save an external subtitle
   beside the media with a player-compatible name such as `TITLE.zh-Hans.srt`.
3. Preserve cue order, timestamps, and UTF-8 encoding. Validate that timestamps are
   monotonic, cues have text, and the subtitle duration is compatible with the media.
4. The default output is SRT. Learning glosses, character cards, and ASS styling remain
   opt-in operations from `lov-subtitle-freedom-skill`; they are not silently generated
   as a substitute for Simplified Chinese.
5. Report `subtitle_status` as `embedded`, `external_matched`, `missing`, or
   `generated_pending_review`. Keep it independent of the media's technical verdict.

## Evidence to retain

Record the source label, release match method, cue count, encoding, duration delta, and
validation result in the verification report. If an English track is extracted for a
subtitle operation, use a temporary UTF-8 SRT and never overwrite the source media.
