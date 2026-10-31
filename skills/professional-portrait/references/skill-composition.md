# Skill Group Composition

## Nearby Skills Inspected

| Skill | Routing contract | Classification | Decision |
| --- | --- | --- | --- |
| `lov-spectacular-ps` | Retouches a travel or outdoor photo into a cinematic environmental portrait that keeps the person's features, with WeChat avatar cropping | overlapping atom | See Overlap Decisions |
| `lov-riso-portrait` | Redraws a single-person photo as an identity-faithful Riso print avatar | adjacent atom | Stylized redraws go there; this Skill stays photographic |
| `lov-image-creator` | Generates images, designed graphics, or image prompts for a stated use | not composed | This Skill only edits the user's own photo; it never creates a person |
| `lov-nano-banana-pro` | Turns an image request into a structured generation or edit prompt | not composed | Edit prompts come from `references/prompts.md`, which carries the identity invariants |
| `lov-image-decorator` | Adds a caption bar and brand logo to an existing image | optional downstream atom | Only on a separate request, on a copy: Step 8 never bakes labels or marketing text into the portrait |

## Atomic Handoffs

```text
lov-professional-portrait
  input: one single-person source photo (the edit target) and the user's brief
  steps: inspect -> smallest sufficient brief -> planned passes ->
         edit prompt from references/prompts.md -> native image edit ->
         full-image and face-crop gate from references/quality-gate.md
  output: a new-file portrait, a list of intentional changes, what was preserved,
          and an optional before/after or progressive comparison
                |
                v
optional, separate request: lov-image-decorator on a copy of the delivered image
```

This Skill owns acceptance of the portrait: identity match at first glance and
every check in `references/quality-gate.md`, with the original file untouched.

## Overlap Decisions

`lov-spectacular-ps` also preserves identity while retouching one person, but its
outcome is a dramatic environmental image with a scene-driven look. This Skill
locks clothing, background, framing, and scene by default and aims for a clean
professional headshot or profile photo, so a request for a cinematic look or a
travel scene goes there.

## Composition Decision

Single Skill. Inspection, brief, pass planning, prompt, edit, and quality gate act
on one edit target under one set of identity invariants; every extra hand-off
would add another generative pass that can drift identity, so a Kit adds nothing.
