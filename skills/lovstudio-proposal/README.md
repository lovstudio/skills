# lovstudio:proposal

![Version](https://img.shields.io/badge/version-1.0.0-CC785C)

Client requirements to complete business proposal — technical architecture, budget, timeline, risk analysis, branded PDF. One command, full pipeline.

Part of [lovstudio/skills](https://github.com/lovstudio/skills) &mdash; by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx skills add lovstudio/skills --skill lovstudio:proposal
```

Requires: `lovstudio:illustrate`, `lovstudio:any2pdf`, `pandoc` (for .docx input)

## Usage

```
/lovstudio:proposal path/to/requirements.docx
```

Or without a document:

```
/lovstudio:proposal 客户是建筑行业国企，需要AI智能化方案
```

## Pipeline

```
Client Requirements → Parse → Generate Markdown → Illustrate → PDF
```

## Output

| File | Description |
|------|-------------|
| `手工川-{client}-{topic}-{date}-v0.1.md` | Source markdown |
| `手工川-{client}-{topic}-{date}-v0.1-illustrated.md` | With images |
| `手工川-{client}-{topic}-{date}-v0.1.pdf` | Final branded PDF |

## Proposal Structure

10 chapters + appendix: Background, Requirements Analysis, Architecture, Implementation, Timeline, Budget, Management, Risks, Commitments, About Us.

## License

MIT
