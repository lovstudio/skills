---
name: lovstudio:translation-review
description: >
  Review Chinese-to-English translations for accuracy, grammar, terminology,
  and consistency. Produces a structured review report with prioritized issues.
  Trigger when: user provides a Chinese document and its English translation
  for review/checking/proofreading, or mentions "翻译检查", "翻译审校",
  "translation review", "translation check", "proofread translation".
license: MIT
compatibility: >
  No external dependencies. Supports .docx (via pandoc), .md, and .txt input files.
  Requires pandoc for docx conversion (`brew install pandoc`).
metadata:
  author: lovstudio
  version: "1.0.0"
  tags: translation, review, chinese, english, proofreading
---

# translation-review — Chinese-English Translation Review

Systematically compare a Chinese source document against its English translation,
identify issues across 6 dimensions, and produce a prioritized review report.

## When to Use

- User provides a Chinese original + English translation pair for review
- User asks to check/proofread an English translation from Chinese
- User mentions "翻译检查", "审校", "translation review"

## Workflow (MANDATORY)

**You MUST follow these steps in order:**

### Step 1: Collect Input

**Use `AskUserQuestion` to confirm before starting:**

Ask the user:
1. **Document type** — academic paper (SCI/EI), technical docs, business docs, general
2. **Domain** — medicine, CS, law, finance, general (affects terminology checking)
3. **Focus areas** — terminology accuracy, grammar, style, references, all (multi-select)

If the user has already provided context (e.g., "SCI 4区医学论文"), skip the obvious questions.

### Step 2: Read Both Documents

Read the Chinese source and English translation. For `.docx` files:

```bash
pandoc "<chinese_file>.docx" -t plain --wrap=none
pandoc "<english_file>.docx" -t plain --wrap=none
```

For `.md` or `.txt` files, read directly.

If files are large, read in sections (offset/limit) to stay within context.

### Step 3: Systematic Review

Compare the two documents across **6 dimensions**, in this order:

#### D1: Mistranslation (meaning changed)
- Words/phrases translated to a different meaning
- Omissions (content in Chinese missing from English)
- Additions (content in English not in Chinese)
- Pay special attention to domain-specific terms that have been incorrectly generalized or specialized

#### D2: Terminology Accuracy
- Domain-specific terms: check against standard English terminology
- Abbreviation consistency: first occurrence should have full form + abbreviation
- Proper nouns: names, institutions, gene/protein names, drug names
- Units and measurements

#### D3: Grammar & Syntax
- Subject-verb agreement
- Tense consistency (especially in Methods vs Results)
- Article usage (a/an/the) — common error in Chinese-to-English
- Dangling modifiers, run-on sentences
- Passive voice overuse

#### D4: Consistency
- Same Chinese term translated differently in different places
- Formatting inconsistencies (capitalization, hyphenation, number style)
- Heading style consistency

#### D5: References & Citations (academic papers only)
- Citation numbers match between Chinese and English versions
- Reference format consistency (author names, journal abbreviations)
- Missing author information in reference entries
- In-text citation correctness

#### D6: Style & Register
- Academic register appropriate for target journal
- Overly verbose or literary phrasing
- Chinese-influenced sentence structure (e.g., "through...method" patterns)
- Paragraph length and structure

### Step 4: Source Document Issues

While reviewing, also note issues in the **Chinese source** that the English faithfully translates but are themselves incorrect. Flag these separately.

### Step 5: Generate Report

Output a structured review report with the following format:

```markdown
# 翻译审校报告 / Translation Review Report

**Document**: [title]
**Reviewer**: 手工川 (AI-assisted)
**Date**: [YYYY-MM-DD]
**Domain**: [domain]
**Document type**: [type]

---

## Summary

[2-3 sentence overall assessment]

---

## A-Level Issues (Must Fix)

### A1. [Issue title]
**Location**: [section/paragraph]
**Original (CN)**: "..."
**Translation (EN)**: "..."
**Problem**: [explanation]
**Suggested fix**: → "..."

---

## B-Level Issues (Recommended)

### B1. [Issue title]
...

---

## Source Document Issues

### C1. [Issue title]
...

---

## Priority Summary

| Priority | # | Issue | Impact |
|----------|---|-------|--------|
| Must fix | A1 | ... | ... |
| ... | | | |

---

## Conclusion

[Overall quality assessment + recommended next steps]
```

### Step 6: Save Report

Save the report to the same directory as the input files:

**Filename**: `手工川-translation-review-{YYYY-MM-DD}-v0.1.md`

If a file with this name exists, increment the version.

## Issue Severity Classification

| Level | Criteria | Examples |
|-------|----------|---------|
| **A (Must fix)** | Meaning changed, factual error, or would cause rejection | Mistranslation, wrong terminology, reference number mismatch |
| **B (Recommended)** | Awkward but understandable, or non-standard usage | Verbose phrasing, minor grammar, style inconsistency |
| **C (Source issue)** | Error in Chinese original, faithfully translated | Wrong terminology in Chinese, factual inaccuracy |

## Domain-Specific Checklists

### Academic / SCI Papers
- [ ] Abstract: structured, matches body content
- [ ] Keywords: standard MeSH or domain terms
- [ ] Reference numbers: sequential, match between CN/EN versions
- [ ] Figure/table captions: translated and consistent
- [ ] Statistical reporting: p-values, CI format

### Medical / Biomedical
- [ ] Disease names: ICD/MeSH standard
- [ ] Gene/protein names: HUGO/UniProt standard (italics for genes)
- [ ] Drug names: INN (International Nonproprietary Names)
- [ ] Anatomical terms: Terminologia Anatomica standard

### Technical Documentation
- [ ] UI strings: consistent with product localization
- [ ] Code snippets: untranslated, syntax preserved
- [ ] API terms: match official documentation
