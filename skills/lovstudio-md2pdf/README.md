# lovstudio:md2pdf

Convert Markdown files to PDF using pandoc + xelatex with CJK support.

Part of [lovstudio/skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx skills add lovstudio/skills --skill lovstudio:md2pdf
```

Requires: `brew install pandoc basictex`

## Usage

```bash
bash md2pdf.sh input.md              # → input.pdf
bash md2pdf.sh a.md b.md c.md        # batch mode
```

## vs lovstudio:any2pdf

| | md2pdf | any2pdf |
|---|---|---|
| Engine | pandoc + xelatex | Python reportlab |
| Cover page | No | Yes |
| TOC | No | Yes |
| Themes | No | 6 built-in |
| CJK | PingFang SC | Songti SC |
| Speed | Fast | Fast |
| Use case | Quick & simple | Professional reports |

## Also Available As

- **Finder Quick Action**: Right-click any `.md` → "MD to PDF". See [lovstudio/mac-md2pdf](https://github.com/lovstudio/mac-md2pdf).

## License

MIT
