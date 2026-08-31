# lov-search-chat

![Version](https://img.shields.io/badge/version-0.2.0-CC785C)

从本机 Ataru 记忆索引里召回过去的 AI 会话上下文，返回可定位的命中与原文片段。

## 安装

从 LovStudio 统一 Skill 目录安装：

```bash
npx skills add lovstudio/skills -s search-chat -g -y
```

也可以直接从源码仓库安装：

```bash
npx skills add lovstudio/search-chat-skill -g -y
```

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`。长期记录有两项：`records.ataru_bin`（本机可用的
Ataru 可执行文件路径）与 `records.default_level`（偏好的检索粒度），由
`scripts/profile_store.py` 写回。检索词与项目 ID 是一次性输入，不写入 Profile。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

```bash
# 先确认索引可用
python3 scripts/ataru_recall.py index-status

# 按消息粒度召回
python3 scripts/ataru_recall.py search "会话恢复方案" --level turn --limit 10

# 限定项目（项目 ID 以短横线开头，用等号形式传）
python3 scripts/ataru_recall.py search "索引没有更新" \
  --level session --project-id=-Users-me-projects-app

# 围绕某个命中读原文
python3 scripts/ataru_recall.py read \
  --project-id=-Users-me-projects-app \
  --session-id=SESSION_UUID --around=MESSAGE_UUID --window 6
```

`search` 会先确认索引；未就绪时以 `ATARU_INDEX_NOT_READY` 或 `ATARU_INDEX_BUILDING`
失败并指向 `lov-ataru-indexing`，而不是返回零结果。命中里的 `projectId` /
`sessionId` / `messageId` / `lineNumber` 是稳定标识，可直接用于 `read`。

命令行检索只走关键词模式，语义与 hybrid 排序目前只服务桌面端。在万级会话的真实
语料上，一次 turn 级检索是数十秒量级。

## 原子组合

见 [`references/skill-composition.md`](references/skill-composition.md)。本源码是
独立 Single Skill；索引构建由 `lov-ataru-indexing` 负责。

## 可信度卡与用户案例

- [`skill-card.yaml`](skill-card.yaml) / [`skill-card.md`](skill-card.md)
- [`cases/cases.json`](cases/cases.json)
- [`pricing-card.yaml`](pricing-card.yaml)

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.8+（仅标准库）
- 本机安装的 Ataru 0.41.3 或更新版本，且索引已就绪

## License

MIT
