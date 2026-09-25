# 知识卡片工坊 · Knowledge Card Studio · Skill Card

## Description

`lov-gen-card` turns structured content and one independent visual into a
polished, copyable editorial card. It delivers a self-contained HTML master and
a dimension-checked high-resolution PNG. The bundled `art-system-card` preset is
the first validated template.

## Owner

LovStudio · https://lovstudio.ai

## License / Terms

MIT. Users remain responsible for rights to supplied images, logos, copy, and
fonts. The bundled modern-screenshot runtime is used under its MIT license.

## Use Case

The Skill serves AI creators, editors, educators, researchers, and community
operators building visual-card series. It validates JSON, keeps copy and branding
in DOM, fits a fixed card surface, and exports HTML plus PNG.

## Deployment Geography

Global, local-first execution on macOS, Linux, or Windows.

## Requirements / Dependencies

- Python 3.9 or newer.
- A local visual image for each card.
- Chrome or Chromium only when automatic PNG export is requested.
- No account, API key, npm install, or network request.

## Known Risks and Mitigations

- Long content can overflow a fixed card. Guarded fitting runs before export and
  the exporter fails on remaining overflow.
- AI visuals can misrepresent historical work or contain unauthorized material.
  Keep them text-free, label them as visual studies, and review rights and facts.
- Editorial ratings can look objective. The card explicitly labels them as
  editor ratings and does not present them as population statistics.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Input contract](references/input-schema.md)
- [Composition record](references/skill-composition.md)

## Skill Output

The output is a 900×1350 CSS-pixel HTML card with selectable Prompt text, copy
and download actions, plus a PNG at one to four times scale. The default 2× PNG
is 1800×2700. Console evidence reports dimensions, bytes, visual status, fitted
font sizes, and horizontal or vertical overflow.

## Skill Version

0.1.0

## Ethical Considerations

Do not imply that an AI visual is a historical artwork. Avoid name-only
imitation of living artists, preserve attribution where required, and use only
authorized brand and image assets.

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json). The first case uses the real Bauhaus
entry from the Art System Card article workflow and records Input → Prompt →
Output.

### Dimension Map

- Render integrity: exact 1800×2700 output, zero DOM overflow, visual loaded.
- Editability and reuse: DOM copy, selectable Prompt, and built-in copy/download.
- Portability: one self-contained HTML and a standard-library Python renderer.
- Input and brand safety: invalid ratings and missing assets fail before export.

### Pricing Basis

See [`pricing-card.yaml`](pricing-card.yaml). Local rendering and the bundled
preset are free; visual creation, research, hosting, and publishing are outside
the boundary.

### Distribution

Local installation is verified. GitHub, LovStudio, WorkBuddy, and SkillPay have
not been published in this release.
