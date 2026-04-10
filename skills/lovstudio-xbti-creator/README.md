# lovstudio:xbti-creator

Create complete custom BTI personality test websites from a theme and preferences. Based on the [XBTI](https://github.com/lovstudio/XBTI) engine.

Part of [lovstudio/skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
# Install xbti-creator + image-creator dependency together
npx skills add lovstudio/skills --skill lovstudio:xbti-creator lovstudio:image-creator
```

Requires: Node.js 18+, Python 3.8+, `ZENMUX_API_KEY` ([get one free](https://zenmux.ai/invite/K6KT2X))

## What It Does

```
User Input                    Output
─────────────                 ──────
"LBTI" + "龙虾人格"    →    Complete deployable website
                              ├── 15 custom dimensions
                              ├── 30 themed questions
                              ├── 20+ personality types
                              ├── AI-generated avatar images
                              └── Ready to run locally
```

## Usage

Invoke in Claude Code:

```
/lovstudio-xbti-creator
```

Or describe what you want:

```
创建一个LBTI（龙虾人格测试）
Make a FBTI for founder personality types
```

## Flow

1. Provide BTI name + theme + tone preference
2. AI generates dimension system, questions, personality types
3. Clone XBTI template from GitHub, replace data files
4. Auto-generate avatar images via `lovstudio:image-creator` (preview one first, then batch)
5. Launch dev server and test

## Dependencies

| Dependency | Install | Purpose |
|-----------|---------|---------|
| `lovstudio:image-creator` | `npx skills add lovstudio/skills --skill lovstudio:image-creator` | Avatar generation |
| `ZENMUX_API_KEY` | [zenmux.ai/invite/K6KT2X](https://zenmux.ai/invite/K6KT2X) | API access for image gen |
| `google-genai` + `Pillow` | `pip install google-genai Pillow` | Python deps (auto-installed) |

## License

MIT
