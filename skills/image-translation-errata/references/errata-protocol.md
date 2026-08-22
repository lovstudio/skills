# In-image Translation Errata Protocol

## Translation error taxonomy

Classify only what affects the reader's understanding or the editorial point.

| Type | What failed | Markup target |
|---|---|---|
| Domain term | A product, legal, technical, medical, or cultural term was translated by its common dictionary sense | The smallest phrase that exposes the wrong sense |
| Scope or actor | The translation changes who receives, performs, or qualifies for an action | The decisive noun phrase or quantifier |
| Time or modality | Words such as by, before, may, must, should, or can lose their boundary or force | The full time or modal phrase |
| Pragmatics | Humor, understatement, irony, invitation, or implied advice becomes a literal instruction | The complete pragmatic clause |
| Register | Meaning survives but the translation is stiff, bureaucratic, offensive, or wrong for the audience | Mark only when register is part of the user's point |
| Omission or addition | Material meaning disappears or unsupported meaning is introduced | The smallest span that restores the source contract |

Do not mark ordinary stylistic alternatives merely to make the page look busy.

## Evidence levels

1. **Direct**: official UI string, product documentation, standard, glossary,
   source author explanation, or parallel text from the same product.
2. **Contextual**: surrounding sentences, product behavior, or repeated usage
   strongly determines the sense.
3. **Editorial inference**: the correction best preserves tone or naturalness,
   but no source dictates one exact wording.

The rendered image can use an editorially inferred natural phrase, but the
internal correction map must not present it as the only possible translation.

## Default visual grammar

- Wrong fragment: original wording, black or neutral gray, one thin red
  strikethrough, still legible.
- Replacement: immediately adjacent, dark red, no underline, no badge.
- Unchanged target text: original black.
- Source-language text and all non-translation UI: unchanged.
- Labels: none by default. A label is justified only when the strikethrough
  could be mistaken for source styling or the user explicitly requests one.

Avoid proofreader arrows, speech bubbles, emoji, stickers, footers, legends, or
explanation panels unless the user asks for a more didactic graphic.

## Fit fallback order

When inline track changes exceed the original text area, apply these in order:

1. Tighten only the target-language line-height within readable limits.
2. Reduce only the target-language type by a small amount.
3. Strike the shortest old fragment that still proves the error.
4. Use a compact margin callout inside existing whitespace.
5. Ask before expanding the canvas or redesigning the image.

Never shrink the whole screenshot, alter source-language type, move interaction
controls, or cover faces and identity elements to make the correction fit.

## Rendering brief checklist

Before editing, the brief contains:

- exact source strings;
- exact old strings that remain visible;
- exact replacement strings;
- every repeated location of each translation;
- immutable pixels and structural constraints;
- target-language-only typography allowances;
- prohibited additions, including labels when the default is unlabeled;
- output crop and aspect ratio.

## Acceptance checklist

- The translation is defensible from source evidence.
- The old mistake is readable and visibly rejected.
- The corrected reading works when struck text is skipped.
- Repeated quoted or duplicated text is corrected consistently.
- CJK characters, punctuation, product names, and numerals are exact.
- Faces, source text, badges, handles, timestamps, counters, icons, and borders
  match the original.
- The result reads as a corrected screenshot, not a redesigned poster.
