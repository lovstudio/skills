# Quality and Edition Policy

The default `balanced` mode maximizes useful viewing quality under a size guardrail.

## Decision order

1. Correct title, year, season, and episode.
2. Edition identity and runtime evidence.
3. Source/master credibility and absence of obvious corruption markers.
4. Useful picture quality and efficient codec.
5. Original audio plus requested additional tracks.
6. Verified Simplified Chinese and English subtitles.
7. Current source health and sustained acquisition prospects.
8. Size and storage fit.
9. Evidence quality: advertised health is provisional; observed speed and final
   stream inspection decide whether the release is actually ready.

## Edition rules

- A director's cut is a creative variant, not automatically a superset.
- Extended, uncut, complete, theatrical, restored, and regional cuts may differ in
  scenes, pacing, grading, dubbing, or censorship.
- Prefer the user's named edition. Without a named choice, prefer an evidenced
  director's/extended/uncut/complete release only when it is broadly a fuller version
  and does not replace a materially different creative decision.
- When two cuts are both credible and differ materially, require a user choice.
- Runtime within two minutes of a reliable release record is strong evidence; allow a
  larger tolerance only for frame-rate or logo/credits differences that are explained.

## Picture and size rules

Balanced movie defaults:

- Prefer credible 2160p HEVC/AV1 up to 24 GiB when it materially improves the source.
- Otherwise prefer 1080p HEVC/AV1, commonly 5–14 GiB for feature films.
- H.264 remains viable when source health or compatibility outweighs the size penalty.
- Remux/raw-disc files lose balanced-mode rank unless explicitly requested.
- A very small “4K” file receives a credibility penalty; resolution alone does not
  prove detail, bitrate, dynamic range, or source quality.
- HDR is valuable only when the display path and release metadata support it. Dolby
  Vision without a compatible fallback receives a compatibility warning.

For episodic content, apply the configured per-episode cap and then compute the pack's
aggregate size before storage preflight.

## Audio and subtitle rules

- Prefer original-language audio; additional Chinese or English audio is a bonus.
- Prefer embedded `zh-Hans` and `en` subtitles.
- `中字`, `双语`, `CHS`, or `ENG` in a filename is discovery evidence only.
- External subtitles should match exact release timing or be checked against duration
  and several scene boundaries before final acceptance.
- A missing `zh-Hans` stream is a warning on the media verdict until an exact-release
  SRT is matched and validated. Keep `subtitle_status` separate from `verification_status`.
- Image-based subtitles satisfy language coverage when the target player supports them;
  text subtitles are more portable and searchable.

## Automatic decision boundary

Require user choice when any of these remain after research:

- two plausible works share the title;
- top candidates represent materially different cuts and no preference resolves them;
- the first two candidates are within eight ranking points but trade resolution against
  edition, subtitles, or more than 35% size;
- the preferred edition has no runtime or release evidence;
- the only high-ranked candidate exceeds the explicit cap.

Otherwise auto-select and continue.
