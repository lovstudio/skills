# 宿主接入位置

`init` 模块按宿主类型定位指令文件与技能目录；无法识别时用 `--prompt-target`
和 `--skills-dir` 显式指定。

| 宿主 | `--host` | 指令文件 | 技能目录 |
| --- | --- | --- | --- |
| Codex | `codex` | `~/.codex/AGENTS.md` | `~/.codex/skills/` |
| Claude Code | `claude` | `~/.claude/CLAUDE.md` | `~/.claude/skills/` |
| Cursor | `cursor` | `.cursor/rules/feedback-loop.mdc` | 无固定目录 |
| OpenClaw | `openclaw` | `~/.openclaw/workspace/AGENTS.md` | `~/.openclaw/workspace/skills/` |
| 通用 | `generic` | `./AGENTS.md` | `~/.agents/skills/` |

## 规则

- 共享层优先：`~/.agents/skills/` 是跨宿主共享入口，各宿主目录用相对软链指回。
- 项目级与用户级都要时分别安装；项目级块不进版本库以外的地方。
- 托管块只写指令文件的一块区域，块外内容不动。
- 写入前备份为 `<文件>.bak-<时间戳>`；dry-run 时不写任何文件。

## 校验

```bash
readlink -f ~/.agents/skills/lov-feedback-loop
readlink -f ~/.codex/skills/lov-feedback-loop
grep -c "feedback-loop:begin" ~/.codex/AGENTS.md
```

安装完成后回读：软链解析到真源、托管块存在且校验和与片段一致、
账本 `events.jsonl` 可写。
