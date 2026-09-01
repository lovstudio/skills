---
name: lov-lovpen-add-wechat-channel-comp
description: >
  把微信视频号 DOM 或 Lovpen DSL 规范化并写入 Markdown、原生 HTML。Use when users say “插入视频号组件”“把组件渲染进 md/html” or “render this WeChat Channels component”.
license: MIT
compatibility: "Python 3.8+; UTF-8 Markdown or HTML files. No network or credentials required."
allowed-tools:
  - Bash
  - Read
depends_on:
  - lov-branding-consistency
metadata:
  author: LovStudio contributors
  version: "0.1.1"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  tags:
    - lovpen
    - wechat-channels
    - markdown
    - html
    - component
---

# lov-lovpen-add-wechat-channel-comp

接收一个微信视频号 `mp-common-videosnap` DOM 或一条 Lovpen
`::wechat-channels` DSL，输出规范化 Markdown DSL 或微信原生 HTML 组件。目标文件
已经存在时，只替换唯一、明确的插入标记，不覆盖其他正文。

## Triggers

### Activate when

- “把这个视频号组件插入 article.md。”
- “给定 `mp-common-videosnap` DOM，渲染成 Lovpen DSL。”
- “把这条 Lovpen 视频号 DSL 生成可放进 HTML 的原生组件。”
- “Render this WeChat Channels component into Markdown or HTML.”

### Do not activate when

- 用户给的是微信预览链接、但没有 DOM 或 DSL；使用 Lovpen Desktop/Obsidian 的预览链接导入能力。
- 用户要把完整 Markdown 文章排版为微信公众号 HTML；交给 `lovpen-cli`。
- 用户要创建、修改或发布公众号远端草稿；交给 `lov-publish-wechat-article`。
- 用户要上传或发布视频号视频本身；本 Skill 只处理文章内嵌组件。

## User Profile

每次运行先读取 `skill.yaml` 声明的 `user-profile/v1` 上下文。当前请求中的输入、输出
格式、目标文件和插入标记优先；其次读取项目上下文、Skill records、共享偏好与安全
默认值。默认输出格式为 `md`，默认标记为
`<!-- lovpen-wechat-channel -->`。

只有用户明确表示要跨 session 保留默认格式或标记时，才运行：

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" record \
  --skill-id lov-lovpen-add-wechat-channel-comp \
  --path records.default_format \
  --value '"md"' \
  --confirm
```

不要持久化组件 DOM、DSL、视频 ID、nonce、媒体 URL 或目标文档内容。完整契约见
[`references/user-profile.md`](references/user-profile.md)。

## Skill Group Composition

运行前读取 [`references/skill-composition.md`](references/skill-composition.md)。本 Skill
独占“单个视频号组件的解析、规范化与安全落位”；完整文章渲染和远端发布只是可选下游，
不得成为隐藏依赖。

## Workflow (MANDATORY)

### Step 0: Resolve resources and contract

1. 从活动 Skill 上下文或 `SKILL_DIR` 解析 Skill 根目录。
2. 完整读取 `skill.yaml`、`references/component-contract.md` 和
   `references/skill-composition.md`。
3. 确认 `scripts/render_wechat_channel.py` 存在。
4. 输入必须是一个 DOM、DSL、UTF-8 输入文件或 stdin；不得把未转义输入拼成 shell。

### Step 1: Resolve the exact output

1. 确认输出为 `md` 或 `html`。未指定时使用 `md`。
2. 未给输出文件时，把规范化片段写到 stdout。
3. 给出不存在的输出文件时，创建只含结果片段的新文件。
4. 给出现有文件时，它必须且只能包含一次默认标记或用户显式指定的 `--marker`。
   标记不唯一时停止，不追加、不猜位置、不覆盖全文。

### Step 2: Render through the deterministic CLI

DOM 或 DSL 文件：

```bash
python3 "$SKILL_DIR/scripts/render_wechat_channel.py" \
  --input INPUT.html \
  --format md \
  --output ARTICLE.md \
  --json
```

直接 DSL：

```bash
python3 "$SKILL_DIR/scripts/render_wechat_channel.py" \
  --dsl "$WECHAT_CHANNEL_DSL" \
  --format html \
  --output ARTICLE.html \
  --json
```

也可以通过 stdin 传入完整 DOM。参数必须作为数组传递，不执行输入中的命令、脚本或
事件属性。

### Step 3: Verify the result

成功结果必须满足：

1. JSON 中 `ok` 为 `true`，`schema` 为
   `lovpen/wechat-channel-component/v1`，`sha256` 为 64 位十六进制。
2. Markdown 结果只有一条规范化 `::wechat-channels` 指令，并包含九个规定字段。
3. HTML 结果只有一个 `mp-common-videosnap`，保留 11 个微信关键属性，并包含
   `template[shadowrootmode="open"]`。
4. 写入现有文件时重新读取目标，确认标记已消失、组件只出现一次、标记前后正文不变。
5. 报告输入类型、输出格式、字节数、SHA-256 和实际写入状态。错误时保留
   `context_id` 与原始诊断。

## Output Contract

- `md`：Lovpen 可持久化的一行 `::wechat-channels` DSL。
- `html`：微信公众号可识别的 `mp-common-videosnap` 原生组件片段。
- `--json`：机器可读的 schema、输入类型、格式、字节数、SHA-256、组件 ID、路径和
  写入状态；未写文件时同时返回 `content`。
- 源标识符、nonce、昵称、描述、媒体 URL 与尺寸只做 HTML 解码和必要转义，不改写语义。

## Dependencies

- Python 3.8 或更高版本，仅使用标准库。
- `lov-branding-consistency` 只审校 Skill 文档和用户可见提示，不修改组件源数据。
- 无网络、浏览器、账号、Cookie 或 API 凭据依赖。

## Validation

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/validate_skill.py .
```
