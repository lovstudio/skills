# sgc-skill-distiller

![Version](https://img.shields.io/badge/version-0.3.1-CC785C)

将已经验证过的项目经验蒸馏成可实现的 Agent Skill 蓝图，而不是停留在复盘或机会清单。

## 本地安装

```bash
ln -s "$(pwd)/skill-distiller-skill" \
  "$HOME/.codex/skills/sgc-skill-distiller"
```

## 使用

- “把 Yoda 的增量更新经验蒸馏成一个 Skill 蓝图。”
- “从这次重启机制的复盘中，提炼稳定流程、验收与边界。”
- “Distill this project workflow into a reusable skill.”

如需先收集仓库线索：

```bash
python3 scripts/collect-source-evidence.py /path/to/project \
  --output skill-distillation-evidence.md
```

输出的蓝图经确认后，使用 `sgc-skill-creator` 实现并本地安装。

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 scripts/collect-source-evidence.py . --output /tmp/skill-distillation-evidence.md
```

## 依赖

- Python 3.8+
- Git（可选）

## License

MIT
