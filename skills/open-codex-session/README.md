# lov-open-codex-session

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

用稳定的 Codex thread ID 或 deeplink，把当前 Codex 主窗口直接切换到目标任务。

## 安装

从 LovStudio 统一 Skill 目录安装：

```bash
npx skills add lovstudio/skills -s open-codex-session -g -y
```

也可以直接从源码仓库安装：

```bash
npx skills add lovstudio/open-codex-session-skill -g -y
```

源码开发安装遵循三层链接：真源目录 → `~/.agents/skills/lov-open-codex-session` → 各宿主 Skill 目录的相对链接。

## 使用

已知 ID 时直接打开：

```text
打开 codex://threads/00000000-0000-0000-0000-000000000000
```

输入是 deeplink，输出是 Codex 主窗口切换到对应任务，并以宿主返回的 `navigated: true` 验收。

也可以承接 `lov-search-chat` 的检索结果：

```text
打开刚才找到的微信读书投稿 session
```

输入是当前对话里已经确认的唯一 `sessionId`，输出是打开对应 Codex 任务；不会取消归档或发送新消息。

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`，每次运行读取共享用户、品牌、工作区、偏好与本 Skill 的长期记录。thread ID、标题和转录内容不会写入 Profile。详见 [`references/user-profile.md`](references/user-profile.md)。

## 原子组合

[`references/skill-composition.md`](references/skill-composition.md) 记录相邻 Skill 的输入输出边界。`lov-search-chat` 只负责提供稳定 ID，本 Skill 独立拥有“打开并验证导航成功”的结果。

## 可信度卡与真实案例

- [`skill-card.yaml`](skill-card.yaml) / [`skill-card.md`](skill-card.md)：用途、风险、输出和维度证据。
- [`cases/cases.json`](cases/cases.json)：真实的“微信读书投稿会话 → 成功导航”案例。
- [`pricing-card.yaml`](pricing-card.yaml)：免费边界与复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
```

真实运行验收还必须在 Codex desktop 中得到 `navigated: true`。

## 依赖

- Codex desktop 的 `navigate_to_codex_page` 能力或语义等价工具
- Python 3.8+（共享 Profile）
- 可选：`lov-search-chat`（仅在没有明确 thread ID 时定位会话）

## License

MIT
