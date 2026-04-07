---
name: lovstudio:image-gen
description: Generate images using Gemini via ZenMux
allowed-tools: [Bash, Read]
---

# Usage

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/image-gen/gen_image.py "PROMPT" [-o output.png] [-q low|medium|high] [--ascii]
```

Display result with `Read` tool after generation.
