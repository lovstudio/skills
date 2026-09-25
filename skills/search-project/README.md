# 项目寻踪 · Project Finder

![Version](https://img.shields.io/badge/version-0.2.1-CC785C)

分层定位本机项目 / 源码目录：优先扫项目根目录，其次当前文件夹与 AI 聊天记录，
最后全盘兜底，返回候选路径与每层命中证据。

## 本地安装

```bash
# 真源 → 中间层（绝对）→ install（相对），readlink -f 应解析到真源
export SRC="$(pwd)/search-project-skill"
mkdir -p ~/.agents/skills ~/.claude/skills
ln -sfn "$SRC"                      ~/.agents/skills/lov-search-project
ln -sfn ../../.agents/skills/lov-search-project ~/.claude/skills/lov-search-project
readlink -f ~/.claude/skills/lov-search-project   # 应输出真源路径
```

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`。运行前读取共享 Profile 的用户、品牌、
工作区与本 Skill 长期记录；`workspace.projects` 会追加为默认搜索根。用户直接
说出的持久偏好由 `scripts/profile_store.py` 写回。详见
[`references/user-profile.md`](references/user-profile.md)。

## 使用

### 示例 1：找某个项目目录

```
我：找到 claude code 泄露源码的项目
AI：python3 "$SKILL_DIR/scripts/find_project.py" "claude code" --json
    → [chat] ~/lovstudio/research/agent-research/claude-code-source-code
      （提及于聊天记录）
```

### 示例 2：从聊天记录回忆项目位置

```
我：我之前在哪个目录研究过 xxx？
AI：roots 无命中 → --scope chat → 返回聊天记录里出现过的对应路径 + 证据文件
```

### 示例 3：全盘兜底

```
我：本机有没有 xyz 的源码？
AI：roots/chat 无命中 → --scope full → 全盘 Spotlight 扫描，标注「全盘兜底，
    可能存在同名无关目录」，请用户确认。
```

## 原子组合

`references/skill-composition.md` 记录了相邻 Skills 的检查结论：本 Skill 为
Single Skill，与 `lov-find-logo` / `lov-memory-search` / `lov-search-chat` /
`lov-finder-action` 无重叠；`lov-repo-takeover` 为可选下游交接。

## 可信度卡与用户案例

- `skill-card.yaml` / `skill-card.md`：用途、负责人、依赖、风险、输出与维度地图。
- `cases/cases.json`：真实的 Input → Prompt → Output 案例。
- `pricing-card.yaml`：免费 Skill 的价值锚点、交付边界与复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.8+
- ripgrep（可选，聊天记录层加速）
- macOS Spotlight `mdfind`（可选，全盘层）

## License

MIT
