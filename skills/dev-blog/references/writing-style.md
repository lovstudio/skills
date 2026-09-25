# Writing Style Profiles

Use this reference whenever the user supplies a writing style profile or the
runtime resolves `user.style_profile_path`.

## Resolution and reading

Resolve the active style source in this order:

1. Explicit instructions or profile path in the current request.
2. Project-specific writing guidance.
3. Runtime preference `user.style_profile_path`.
4. Runtime profile field `brand.tone`.
5. The generic rules in `SKILL.md`.

Read the selected profile completely. Do not infer a profile from its filename,
quote large sections into the article, or copy its local path into public
metadata. When the path is unavailable, say that the configured style profile
could not be read and keep the article local until the mismatch is resolved.

## Build a style brief

Extract only actionable writing constraints:

- voice and author-reader relationship;
- first-, second-, or third-person perspective;
- sentence length, punctuation, and short-sentence cadence;
- paragraph length, whitespace, headings, and section progression;
- preferred technical vocabulary and words to avoid;
- expected evidence: personal experience, commands, data, cases, or citations;
- emotional arc and strength of judgment;
- recurring rhetorical structures such as contrast, definition, or questions;
- topic-specific variants and explicit prohibitions.

Translate statistics and examples into constraints instead of imitating the
reference literally. For example, a profile that observes frequent one-sentence
paragraphs should produce varied mobile-friendly pacing, not a rigid paragraph
counter.

## Authenticity boundary

A style profile is not a license to fabricate biography, experience, mistakes,
numbers, quotes, or emotions. First-person writing must be grounded in the
current conversation or supplied source material. When the evidence establishes
the investigation but not a personal anecdote, write "这次排查" instead of inventing
where the author was or how they felt.

Keep technical terms in their precise original language when translation would
blur the boundary. Strong judgments need nearby evidence. Catchphrases,
profanity, exaggerated remorse, and emotional peaks from a corpus are optional
topic-specific features, not a checklist.

## Pre-publish validation

Before saving the final draft, verify:

1. The opening uses the profile's preferred entry point and reaches the real
   conflict or result early.
2. The author has a visible position without unsupported first-person claims.
3. Definitions, adjacent concepts, and applicable boundaries are separated.
4. Every major section contains concrete evidence from the source context.
5. Sentence and paragraph rhythm resemble the profile without becoming a
   mechanical parody.
6. Preferred vocabulary and technical terms remain precise.
7. At least one cost, limitation, uncertainty, or changed judgment is stated
   when the source supports it.
8. Prohibited filler, publicity language, and generic conclusions are absent.
9. The ending follows the profile's closure pattern instead of repeating the
   section summary.

Revise failed checks before cover generation or publication. The publish dry
run validates payload shape; it does not validate writing voice.
