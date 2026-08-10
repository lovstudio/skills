# Output contract

## Project structure

```text
hanzi-project/
├── project.json
├── hanzi.json
├── research.json
├── source.md
├── brief.md
├── font-report.json
├── hanzi-audit.json
└── exhibit/
    ├── source.md
    ├── brief.md
    ├── project.json
    ├── poster.html
    ├── poster.png
    └── audit.json
```

## `project.json`

```json
{
  "schema_version": 1,
  "character": "翕",
  "scope": "character-only",
  "locale": "both",
  "dependency": "lov-professional-infographic",
  "research": "research.json",
  "source": "source.md",
  "brief": "brief.md",
  "exhibit_dir": "exhibit"
}
```

## `research.json`

```json
{
  "schema_version": 1,
  "character": "翕",
  "pronunciations": [
    {
      "reading": "xī",
      "region": "Mainland Mandarin",
      "system": "Hanyu Pinyin",
      "source_ids": ["S1"]
    }
  ],
  "structure": {
    "radical": "羽",
    "strokes": 12,
    "form_analysis": "上合下羽；《说文》从羽、合声。",
    "source_ids": ["S1", "S2"]
  },
  "etymology": {
    "claim": "《说文》释为起也；段注以鸟将起前敛翼说明。",
    "source_ids": ["S1"],
    "caveat": "段注是后世解释，不是《说文》原文。"
  },
  "semantic_model": {
    "governing_message": "Source-supported action title",
    "relationship": "root meaning to semantic branches",
    "branches": [
      {
        "label": "收束",
        "claim": "静时内收",
        "source_ids": ["S2"]
      },
      {
        "label": "聚合",
        "claim": "把分散之物汇拢",
        "source_ids": ["S2"]
      }
    ]
  },
  "classical_examples": [
    {
      "quote": "Exact quote",
      "work": "Work and section",
      "gloss": "Contextual gloss",
      "source_ids": ["S2"]
    }
  ],
  "sources": [
    {
      "id": "S1",
      "title": "Source title",
      "url": "https://example.com",
      "type": "official standard | historical dictionary | primary text | aggregation"
    }
  ],
  "interpretation_boundary": "What is fact, commentary, synthesis, and metaphor.",
  "omissions": ["What was deliberately excluded and why."]
}
```

The strict audit validates shape, minimum counts, source linkage, scope leakage,
font coverage, Exhibit presence, delegated visual audit, and human review.

## Release conditions

- `font-report.json` passes for the exact character or IVS sequence;
- `research.json` passes all required fields and source links;
- `poster.html` contains the target character and no placeholder copy;
- character-only scope contains no person/name inference language;
- `poster.png` exists at the declared scale;
- the delegated professional infographic strict audit passes;
- `hanzi-audit.json` reports zero errors and zero warnings;
- full-size and thumbnail review evidence is recorded.
