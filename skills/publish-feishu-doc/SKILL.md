---
name: lov-publish-feishu-doc
description: 将本地 Markdown 忠实同步为指定飞书知识库文档，处理新建或更新、链接可见范围，并回读正文、节点位置与权限。Use when asked to publish or sync Markdown to a Feishu/Lark Wiki document.
license: MIT
compatibility: Python 3.8+；需要 lark-cli 及可访问目标知识库的飞书 user 身份。
depends_on:
  - lov-branding-consistency
metadata:
  author: lovstudio
  version: "0.1.1"
  card_standard: lovstudio/skill-card/v1
  content_class: verbatim
  tags:
    - feishu
    - lark
    - wiki
    - document-publishing
    - remote-verification
---

# 飞书文档同步 · Feishu Doc Sync

把本地 Markdown 同步成指定飞书知识库中的在线文档，并以远端正文、知识库节点和公开权限三项回读作为完成证据。默认保持源文档内容，不借同步之名改写正文。

## Triggers

### Activate when

- 用户要求“把这份 Markdown 同步到飞书知识库”“发布为飞书文档”或“更新知识库里的同名文档”。
- 用户同时指定链接查看范围、组织内查看或互联网公开查看。
- English triggers include “Publish this Markdown to our Feishu Wiki” and “Sync this file to a Lark knowledge base and verify sharing”.

### Do not activate when

- 只需创作或修改本地正文，不要求写入飞书；使用相应写作能力。
- 只需读取、摘要或局部编辑既有飞书文档；使用 `lark-doc`。
- 只需整理知识库层级、移动节点或管理空间成员；使用 `lark-wiki`。
- 只需审计或修改既有资源权限，不涉及内容同步；使用 `lark-drive`。

## 输入契约

执行前从当前请求与上下文解析：

- `source`：本地 Markdown 文件，必填；
- `title`：显式标题优先，否则取首个一级标题；
- `wiki_target`：知识空间精确名称、`space_id`、知识库 URL 或父节点 token；
- `conflict`：同位置同名节点存在时选择 `update`、`create-copy` 或 `fail`；“同步/更新”默认 `update`，“新建/发布一篇”默认 `fail`，不得静默制造重复文档；
- `link_access`：`closed`、`tenant_readable`、`tenant_editable`、`anyone_readable` 或 `anyone_editable`；
- `profile`：可选的 `lark-cli --profile` 名称，未提供时使用当前已验证身份。

“所有获得链接的人查看”“互联网上获得链接的人可查看”精确映射为 `anyone_readable`。只说“开放一下”或“共享给大家”不足以确定公开档位，必须先让用户选择。

只向飞书写入面向读者的正文。内部背景、密钥、完整本机路径和调试信息不得进入在线文档。

## 状态语义

```text
prepared
  -> target_resolved
  -> document_creating | document_updating
  -> document_created | document_updated
  -> content_verified
  -> permission_applying
  -> ready | verification_failed
```

- `document_created` / `document_updated`：远端写操作已返回节点或文档标识，但尚未完成验收；
- `content_verified`：重新获取远端正文，标题、章节、表格、链接及关键文本与准备稿一致；
- `ready`：正文回读、知识库位置回读和目标权限回读均通过；
- `verification_failed`：任何一项无法观察或不一致。保留远端标识和错误，不把它描述为已完成同步。

## User Profile

每次运行读取 `skill.yaml` 声明的 `user-profile/v1` 上下文。当前请求优先于环境变量、Skill 记录和共享 Profile。用户明确声明长期默认的飞书 profile、知识空间或链接权限时，使用 `scripts/profile_store.py record ... --confirm` 写入 `skills.lov-publish-feishu-doc.records`，并报告保存路径；本次任务中的临时目标不自动持久化。

## Skill Group Composition

开始前阅读 `references/skill-composition.md`。本 Skill 拥有从本地 Markdown 到已核验 Wiki 文档的最终验收；`lark-doc`、`lark-wiki` 和 `lark-drive` 是运行时原子能力，不是隐藏在源码中的嵌入模块。

## 工作流

### 1. 预检源文档

运行：

```bash
python3 <skill-dir>/scripts/preflight_publish.py SOURCE \
  --title "TITLE" \
  --wiki-target "SPACE_NAME_OR_ID" \
  --link-access anyone_readable
```

退出非零时先处理 `errors`。脚本输出源文件 SHA-256、标题、章节/表格/链接数量、建议权限 patch，以及在线标题 H1 的准备动作。

当前 Docs v2 创建链从 Markdown 的首个 H1 生成在线标题，因此准备稿必须保留、替换或补入 `# TITLE`，不能先删除 H1。脚本不改动源文件，可通过以下命令把准备稿写入 stdout：

```bash
python3 <skill-dir>/scripts/preflight_publish.py SOURCE \
  --title "TITLE" --emit-prepared
```

### 2. 验证身份与解析知识空间

1. 先执行 `lark-cli [--profile PROFILE] auth status --verify`，必须观察到 `identity=user` 与 `verified=true`。
2. 用 `lark-cli [--profile PROFILE] wiki +space-list --page-all --page-limit 0` 获取完整空间列表。
3. 名称目标默认只接受唯一精确匹配。没有精确匹配时可展示唯一明显候选，但未经用户确认不得把多个近似空间任选其一。
4. 目标为父节点时，用 `wiki +node-get` 解析真实 `space_id` 与 `node_token`。
5. 列出目标位置的节点，检查同名文档。需要递归时逐层使用 `wiki +node-list`，不能只看第一页或根节点。

当前 CLI 若缺少文档中列出的 shortcut，先用 `lark-cli schema` 读取等价接口，再使用原生命令：节点读取回退到 `wiki spaces get_node`，权限读取回退到 `drive permission.public get`。只允许这种同接口语义的降级，不得因 shortcut 缺失而跳过回读。

### 3. 创建或更新文档

创建新文档时先创建含完整正文的 Docx，再迁入已解析的知识空间。当前已验证的 `lark-cli docs +create --wiki-space` 可能忽略 Wiki 目标，因此不能把创建成功当成节点已入库。长内容通过 stdin 传输，避免命令行转义和绝对路径限制：

```bash
python3 <skill-dir>/scripts/preflight_publish.py SOURCE \
  --title "TITLE" --emit-prepared |
lark-cli [--profile PROFILE] docs +create \
  --api-version v2 --title "TITLE" \
  --content - --doc-format markdown --as user
```

创建返回 `document_id` 后迁入 Wiki：

```bash
lark-cli [--profile PROFILE] wiki +move \
  --obj-type docx --obj-token "DOCUMENT_ID" \
  --target-space-id "SPACE_ID" \
  [--target-parent-token "PARENT_NODE_TOKEN"] --as user
```

迁移可能异步；只有 `ready=true` 并返回 `node_token` 才进入 `document_created`。如返回 `next_command`，继续查询任务状态，不重复创建文档。

更新既有文档时，先用 `docs +fetch --api-version v2 --detail full` 保存当前远端快照，再按 `lark-doc` 的更新规范使用 `docs +update --command overwrite --doc-format markdown`。覆盖属于高影响写入；只有当前请求明确要求同步/更新这个具体文档时才能执行。

写入成功后记录 `node_token`、`obj_token`、`obj_type`、标题、空间 ID 和 canonical URL。一次命令退出成功不等于交付完成。

### 4. 回读正文与知识库位置

1. 用 `wiki +node-get --node-token NODE_TOKEN` 回读节点，核对 `space_id`、父节点、标题、`obj_token` 和 `obj_type=docx`。
2. 用 `docs +fetch --api-version v2 --doc WIKI_URL --doc-format markdown` 获取整篇正文。
3. 对照预检结果核对标题、章节、表格、链接和关键文本。允许飞书规范化空行和列表编号；不得丢失正文段落、评价引文、公开网址或附录证据。本地相对链接若未同步其目标文件，应明确记录为被降级成纯文本，不得伪称仍可点击。
4. 不一致时先定向修复并重新回读；无法一致则进入 `verification_failed`。

### 5. 设置并回读链接权限

公开权限是高风险写入。只有目标 `obj_token`、`obj_type`、当前设置、目标档位和字段变更都已明确，且用户已明确确认该具体档位时才执行。

1. 对 Wiki 节点关联的 `docx obj_token` 读取 `drive +permission-get-setting --type docx`；不要对 `wiki node_token` 设置 `anyone_readable`，飞书 API 不支持该组合。
2. 运行 `drive permission.members auth` 检查 `manage_public`；`auth_result=false` 时停止。
3. 运行 `lark-cli schema drive.permission.public.patch`，只使用当前 schema 支持的字段。
4. `anyone_readable` 对应以下精确变更：

```json
{"external_access":true,"link_share_entity":"anyone_readable"}
```

5. 用户已明确确认后执行：

```bash
lark-cli [--profile PROFILE] drive permission.public patch \
  --params '{"token":"OBJ_TOKEN","type":"docx"}' \
  --data '{"external_access":true,"link_share_entity":"anyone_readable"}' \
  --as user --yes --format json
```

6. 再次执行 `drive +permission-get-setting`，必须回读 `external_access=true` 与 `link_share_entity=anyone_readable` 才能进入 `ready`。

`anyone_readable` 是飞书 API 对“互联网上获得链接的任何人可阅读”的权限语义。若用户进一步要求“无需飞书登录即可匿名访问”，还必须在无登录态浏览器中打开链接验证；命令行 HTTP 跟随到登录页时只能报告匿名访问尚未证实，不能推翻或夸大 API 回读结果。

遇到 `91009`—`91012` 时按 `lark-drive` 的权限指南报告租户或密级阻塞，不重复相同请求，也不降级到较宽或较窄的其他档位。

### 6. 输出收据

交付时至少报告：

- 状态：`ready`、`verification_failed` 或具体中间状态；
- 源文件名与源 SHA-256；
- 知识空间名称与 `space_id`；
- 文档标题、Wiki URL、`node_token` 与 `obj_token`；
- 正文回读结果；
- 权限回读结果；
- 创建或更新动作、完成时间与剩余限制。

收据只保存必要标识，不包含 access token、Cookie、完整私人路径或原始认证配置。

## 完成前检查

1. 预检无错误，源文件与标题来自本次输入。
2. 目标空间精确解析，同名冲突策略明确，没有静默创建重复文档。
3. 远端节点确实位于目标知识空间或父节点下。
4. 远端正文已重新获取，关键章节、表格、链接、引文和附录均保留。
5. 权限针对底层 `docx obj_token` 设置，并由新的读取结果验证。
6. 只有三项回读全部通过才报告 `ready`。
7. `skill-card.yaml`、`cases/cases.json` 与 `pricing-card.yaml` 通过本地验证。

## Dependencies

- `lark-cli`：飞书身份、Docs、Wiki 与 Drive 权限操作；
- Python 3.8+：本地 Markdown 预检；
- 运行时参考 `lark-doc`、`lark-wiki`、`lark-drive` 与 `lark-shared` 的当前接口规范。
