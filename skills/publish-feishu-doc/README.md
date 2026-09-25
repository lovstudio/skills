# 飞书文档同步 · Feishu Doc Sync

![Version](https://img.shields.io/badge/version-0.1.1-CC785C)

将本地 Markdown 同步为指定飞书知识库文档，并以正文、节点位置和链接权限三项远端回读作为完成证据。

## 本地安装

将本目录作为真源，并分别建立到 Agent Skills 目录的软链接：

```bash
ln -s "/path/to/publish-feishu-doc-skill" "/path/to/agent-skills/lov-publish-feishu-doc"
```

## 使用示例

```text
把 proposal.md 同步到“项目资料”知识库，并允许互联网获得链接的人查看。
```

输出为目标 Wiki 文档链接、知识空间位置、正文回读结果和 `anyone_readable` 权限回读结果。

```text
Update the existing “Q3 Launch Plan” in our Lark Wiki, but keep link sharing closed.
```

同位置存在同名文档时更新原文档，保留远端快照并在写入后重新获取正文；权限保持 `closed`。

## 状态与边界

创建或更新成功只表示远端写入发生。只有正文、Wiki 位置和权限均重新读取且一致，状态才是 `ready`。本 Skill 不负责创作正文、整理整个知识库、管理知识空间成员或转移 owner。

## 用户 Profile

`skill.yaml` 声明 `user-profile/v1`。明确的长期默认 profile、知识空间或链接权限可写入 `skills.lov-publish-feishu-doc.records`；临时任务参数不自动持久化。

## 原子组合

`references/skill-composition.md` 记录与 `lark-doc`、`lark-wiki`、`lark-drive`、`feishu-doc`、`feishu-perm` 和微信公众号发布 Skill 的边界。

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 scripts/preflight_publish.py ./article.md --wiki-target "Project Wiki"
```

## License

MIT
