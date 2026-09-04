# lov-publish-event-onto-hdx

![Version](https://img.shields.io/badge/version-0.4.0-CC785C)

诊断活动行活动的分类与标签配置，找出分类页不可见的根因；替换活动详情正文配图；
并在任何后台保存后守住「分类被静默清空」这一平台级陷阱。

## 安装

```bash
git clone https://github.com/lovstudio/publish-event-onto-hdx-skill \
  "${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}/lov-publish-event-onto-hdx"
```

从本地源码开发时改用软链接（`SKILLS_DIR` 未设置时回退到示例路径）：

```bash
SKILL_SOURCE="$(pwd)"   # run from the publish-event-onto-hdx-skill directory
ln -s "$SKILL_SOURCE" "${SKILLS_DIR:-$HOME/.agents/skills}/lov-publish-event-onto-hdx"
ln -s "${SKILLS_DIR:-$HOME/.agents/skills}/lov-publish-event-onto-hdx" \
  "${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}/lov-publish-event-onto-hdx"
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

**示例 3：换掉详情里的海报**

输入：`把活动行详情里那张海报换成新的`
输出：经 UEditor 上传接口换图并同步 `src` / `_src`，保存后自动补一次 editbase 提交，
回读公开页确认新图生效且 `Category` / `HdxTags` / `Organizers` 未被清空。

**示例 4：保存完分类不见了**

输入：`我就改了个图，分类怎么没了`
输出：定位到基本信息页 `SaveEvent` 的 payload 缺 `Setting.HdxTags`，说明这是平台行为而非误操作，
指向 `?view=editbase` 重设分类，并回读三个字段确认恢复。

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
