# 知识卡片工坊 · Knowledge Card Studio

![Version](https://img.shields.io/badge/version-0.2.1-CC785C)

![version](https://img.shields.io/badge/version-0.2.0-black)
![license](https://img.shields.io/badge/license-MIT-blue)

Generate a copyable DOM editorial card from structured JSON and one local
visual. The bundled `art-system-card` preset outputs a self-contained HTML
master and an audited high-resolution PNG.

Cards support one to five editorial rating dimensions. Comparison series should
reuse the same labels and ordering across every card.

```bash
python3 scripts/render_card.py cases/bauhaus-card.json \
  --out cases/output --name bauhaus-card --format both --scale 2
```

See [SKILL.md](SKILL.md) for routing and workflow, and
[references/input-schema.md](references/input-schema.md) for the JSON contract.

Status: local installation verified; no remote distribution channel is claimed.