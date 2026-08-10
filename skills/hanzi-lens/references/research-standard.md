# Hanzi research standard

The goal is not to collect every dictionary sense. The goal is to build one
defensible explanation whose facts, disagreements, and interpretations remain
traceable.

## Source hierarchy

### Level 1 — standards and official dictionaries

Use for code point, glyph identity, readings, radical/stroke data, and current
dictionary senses.

- Unicode Standard Annex #38, Unicode Han Database:
  https://www.unicode.org/reports/tr38/
- Unicode Unihan lookup:
  https://www.unicode.org/charts/unihan.html
- Taiwan Ministry of Education dictionaries:
  https://dict.revised.moe.edu.tw/
- CNS11643 National Chinese Character Database:
  https://www.cns11643.gov.tw/

For mainland modern readings and dictionary senses, cite the exact dictionary
and edition when using a print or licensed source. If an online aggregation is
used, label it as an aggregation and corroborate material claims.

### Level 2 — historical lexicography

Use named works and keep their claims separate:

- 《说文解字》
- 《广韵》
- 《康熙字典》
- 《汉语大字典》

Quote the base text separately from later commentary. For example, “《说文》
原文” and “段玉裁注” are two evidence layers.

### Level 3 — primary textual usage

Use complete passages when context changes the sense.

- Chinese Text Project dictionary and corpus:
  https://ctext.org/dictionary.pl
- Chinese Text Project dictionary instructions:
  https://ctext.org/instructions/dictionary

Search-result snippets are discovery aids, not final evidence. Open the passage
and identify work, section, exact quote, and contextual gloss.

### Level 4 — secondary aggregation and scholarship

Sources such as 汉典 can be useful because they aggregate modern definitions,
historical dictionaries, and examples. Label the source type and trace decisive
claims back to the named dictionary or primary text when possible:

https://www.zdic.net/

## Required distinctions

| Evidence type | Required label |
|---|---|
| Current standard | jurisdiction / edition / database version |
| Historical dictionary | work title and exact entry |
| Commentary | commentator and work |
| Classical use | work, section, quote, contextual gloss |
| Modern synthesis | interpretation |
| Diagram or motion cue | visual metaphor |

## Research ledger

`research.json` requires:

- at least one sourced pronunciation;
- radical, positive stroke count, form analysis, and sources;
- etymology claim, sources, and caveat;
- one governing message and at least two semantic branches;
- at least two classical examples;
- at least two distinct sources with HTTP(S) URLs;
- one explicit interpretation boundary;
- at least one deliberate omission.

Every `source_ids` value must resolve to `sources[].id`.

## Conflict handling

- Show regional reading differences rather than voting on them.
- Show historical disagreement when it changes the explanation.
- Treat a phonetic component as phonetic unless evidence supports an additional
  semantic role.
- Treat intuitive decomposition as a mnemonic, not etymology.
- If early forms are unattested or disputed, omit the evolution timeline.

## Character-only default

The default scope is the character itself. Do not infer personality, fate,
romantic compatibility, or biographical facts from a name. A user may
explicitly request a separate naming analysis, but it must be labeled as a new
interpretive scope and must not overwrite the character explanation.
