# lov-publish-event-onto-hdx

![Version](https://img.shields.io/badge/version-0.3.0-CC785C)

诊断活动行活动的分类与标签配置，找出分类页不可见的根因并给出修复建议。

## 本地安装

```bash
SKILL_SOURCE="$(pwd)"   # run from the publish-event-onto-hdx-skill directory
ln -s "$SKILL_SOURCE" ~/.agents/skills/lov-publish-event-onto-hdx
ln -s ../../.agents/skills/lov-publish-event-onto-hdx \
  ~/.claude/skills/lov-publish-event-onto-hdx
```

## 用户 Profile（跨 session）

读取 `user-profile/v1` 共享 Profile，从 `skills.lov-publish-event-onto-hdx.records`
取历史活动 URL 和标签记录。详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用示例

**示例 1：诊断活动找不到**

输入：`我在活动行发了一个 AI 活动，分类页找不到自己`
输出：读取 Category 字段，诊断为 0（未分类），指向主办方后台修复路径，建议标签替换清单。

**示例 2：修复后验证排名**

输入：`我刚把分类改好了，现在排名是多少`
输出：在热门点击排序下查找活动，给出页码和位置（如「热门点击第 4 位，最新发布第 13 位」）。

## 原子组合

见 [`references/skill-composition.md`](references/skill-composition.md)。本 Skill 是 Single Skill，
`lov-event-curator`（策划）和 `lov-event-poster`（海报）是可选上游，不依赖。

## 可信度卡与用户案例

- [`skill-card.yaml`](skill-card.yaml) / [`skill-card.md`](skill-card.md)
- [`cases/cases.json`](cases/cases.json)：手工川 AI 创造营第五期真实案例
- [`pricing-card.yaml`](pricing-card.yaml)

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- ego-browser
- Python 3.8+

## License

MIT
