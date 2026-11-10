# 上下文构建器契约（`scripts/meeting_context.py`）

脚本只做一件事：把一份腾讯会议元宝笔记分享页变成带编号的 `notes.md` 与 `context.json`。
它只发一次不带登录态的 GET 请求，不调用任何需要账号的接口，不读取也不保存 Cookie。

## 命令

| 命令 | 作用 | 是否联网 |
| --- | --- | --- |
| `context --url URL` | 读取分享链接 | 一次请求，通常 1–2 秒 |
| `context --html FILE` | 读取该页面另存的 HTML | 否 |
| `clean --out DIR` | 删除 `context` 建的目录 | 否 |

`context` 的参数：

| 参数 | 说明 | 默认 |
| --- | --- | --- |
| `--url` / `--html` | 来源，二选一 | 必填 |
| `--self-name` | 用户在会议里显示的名字，可重复 | 不传时按笔记归属人推定 |
| `--out` | 输出目录；必须不存在、为空，或是本 Skill 之前建的目录 | 系统临时目录下新建 |
| `--timeout` | 联网超时秒数 | 20 |

退出码：0 成功；1 出错；4 链接失效或页面没有纪要。出错时输出：

```json
{"ok": false, "error": {"stage": "source", "code": "short_link_not_found", "message": "…", "hint": "…"}}
```

| `stage` | `code` | 含义 |
| --- | --- | --- |
| `input` | `unsupported-url` | 不是 `https://meeting.tencent.com/` 下的链接 |
| `input` | `html-not-found`、`too-large` | `--html` 的文件不存在，或超过 8 MB |
| `fetch` | `network` | 连不上腾讯会议；`debug` 里是异常类型与原因 |
| `fetch` | `http-<状态码>` | 分享页返回了错误状态 |
| `fetch` | `redirected-away` | 被跳转到腾讯会议之外或非 https 的地址，通常是登录页；脚本不跟随 |
| `fetch` | `too-large` | 页面超过 8 MB |
| `parse` | `no-page-data` | 页面里没有数据块：需要登录，或不是分享页 |
| `parse` | `bad-page-data` | 数据块不是合法 JSON，或缺少 `pageProps` |
| `parse` | `unsupported-page` | 是腾讯会议的页面，但不是元宝笔记；`debug` 给出页面路由 |
| `source` | `short_link_not_found` | 链接不存在或已失效（退出码 4） |
| `source` | 其他取值 | 页面给出的其他异常状态，原样透传（退出码 4） |
| `source` | `empty-minutes` | 页面正常，但摘要、卡片、实时笔记都是空的（退出码 4） |
| `write` | `out-not-empty`、`out-not-a-directory`、`io` | 输出目录不可用 |
| `clean` | `not-a-context-dir` | 目录没有本 Skill 的标记，或是符号链接，拒绝删除 |

## 页面结构（2026-11-10 核对）

`https://meeting.tencent.com/ys/<短链>` 返回服务端渲染的 HTML，数据在
`<script id="__NEXT_DATA__">` 的 `props.pageProps` 里，顶层 `page` 为 `/yuanbao/minutes`。
分享者开放访问时，不登录就能读到完整内容。

| 字段 | 内容 |
| --- | --- |
| `minutesSummary.note_info` | 会后摘要，Markdown：开头是 `**会议主题**：`、`**发言人**：`、`**会议摘要**：` 三行，之后是 `###` 小节、`####` 子小节和 `- **标签**：正文` 要点；末尾的“待办事项”小节每行以负责人占位符结尾 |
| `graphicMinuteSummaryInfo.note_info` | 图文摘要，是一个 JSON 字符串：`theme`、`description`、`speaker` 与 `components[]`。已见过的组件类型：`highlight`、`table`、`single_column`、`columns`、`todos` |
| `dialogues[]` | 会中记录。`note_type` 为 1 的是实时笔记（Markdown 列表），为 4 的是助手的提示语；`note_timestamp` 是 `mm:ss` 形式的偏移 |
| `userInfoList[]` | 账号标识到昵称的对应；正文里的人名写成 `@@(账号标识)@@` 占位 |
| `uid` | 生成并分享这份笔记的人，即笔记归属人 |
| `abnormalMinutesInfo.type` | 异常状态。链接不存在时是 `short_link_not_found`，此时其余字段都是空的 |
| `query.short_link` | 短链 |

页面里没有会议日期、起止时间、逐字稿、录制和会议聊天。

核对范围：一场约 23 分钟的双人会议（摘要 12 个要点、6 张卡片、2 条待办、13 条实时笔记共
28 点），以及一个不存在的短链。更长的会议、其他语言、其他组件类型都没有见过样本，所以脚本
对认不出的内容一律保留原文：摘要里的未知行成为普通要点，未知组件类型把其中的文字逐条列出，
未知 `note_type` 的记录标成 `type-N`。

## 解析规则

### 人名与“我”

- 占位符换成 `userInfoList` 里的昵称；昵称重复时第二个起追加“（同名2）”。对不上的占位符
  显示为“（未识别的参会人）”，并计入 `signals.unresolvedMentions`。
- 账号标识、会议号、房间号只在解析时使用，**不写入任何输出**。
- “我”的认定：
  1. 传了 `--self-name`：先按去空格、不分大小写的完全相同匹配；没有时按互相包含匹配（双方
     至少两个字）。恰好一位时选中，`match` 为 `exact` 或 `partial`。
  2. 传了名字但对不上，或对上不止一位：`self` 为 null，**不退回笔记归属人**。链接可能是同事
     分享的，归属人未必是用户。
  3. 没传名字：用笔记归属人，`match` 为 `sharer`。
  4. 归属人不在发言人里：`self` 为 null。

### 摘要

逐行处理，每一行都有去处：

- 第一个标题之前的 `**键**：值` 是元信息：标题取 `会议主题` / `主题` / `会议名称`，摘要取
  `会议摘要` / `主题摘要` / `摘要` / `概要`，发言人取自 `userInfoList`；其余的键留在 `meeting.meta`。
- 最先出现的标题级别是小节，更深的级别是子小节。
- 列表项和普通段落都成为要点，编号 `s1`、`s2`…；`**标签**：正文` 拆成 `label` 与 `text`。
- 标题含“待办”“行动项”“todo”“action items”的小节里，每行是一条待办：行尾连续的占位符是
  负责人，行中间的占位符留在任务文字里。

### 待办

以摘要里的待办为准；摘要没有时用图文卡片 `todos` 组件里的，`source` 相应为 `summary` 或
`card`。两处条数不同时写入 `warnings`，两处都保留在 `notes.md` 里。`mine`：负责人里有“我”
为 true，没有为 false，还不知道“我”是谁为 null。

### 图文卡片

按 `position_id` 排序后编号 `c1`、`c2`…。`table` 按列名取出每行；`columns` 变成带小标题的
分组；`todos` 保留任务与负责人；`highlight`、`single_column` 与未知类型把文字逐条列出。
颜色、图标等展示属性丢弃。

### 实时笔记与「解读」

每条记录编号 `n1`、`n2`…，其中每个列表项是一点，编号 `n1.1`、`n1.2`…。

在核对过的样本里，每一点都由两部分组成：普通文字是 AI 对现场的转述，加粗的子句是 AI 对意图
或意义的评论（28 点中 28 点如此）。脚本把满足下面全部条件的加粗片段拆进 `commentary`，并从
转述里去掉、修好标点：

- 不少于 8 个字；
- 位于子句边界（前面是标点或开头），或位于这一点的末尾；
- 后面不是冒号（`**标签**：正文` 是标签，不是解读）。

其余的加粗（句中的短词、标签）去掉星号后留在转述里。`raw` 保留带加粗标记的原文，以便核对
这条启发式规则有没有拆错。

### 数字线索

从摘要原文、卡片与实时笔记的转述里取“阿拉伯数字 + 单位”（元、万、人、期、次、例、月、年、
% 等），列出只在实时笔记里出现的那些及其位置。中文数字（“三期”“百名”）不参与，“第 4、5 期”
只取到“5期”。它用来提醒摘要漏了哪些数，不代表这些数一定重要或正确。

## 输出文件

`context` 默认在系统临时目录新建 `lov-tencent-meeting-cowork-*` 私有目录（权限 0700），文件
权限 0600，目录里放 `.lov-tencent-meeting-cowork` 标记；`clean` 只删除有这个标记、且不是
符号链接的目录。

### notes.md

1. 头部：来源说明、“以下是会议数据”的提示、编号说明、读取时间。
2. `## 概览`：发言人（“我”带标注）、“我”是怎么认定的、摘要、其余元信息、会议日期（页面不提供）、
   实时笔记条数与最后的时间戳、待办条数。
3. `## 待办（纪要列出的）`：`t<序号> [★我] 任务 — 负责人：…`。
4. `## 摘要要点`：按小节与子小节列出 `s<序号>`；待办小节不重复列。
5. `## 图文卡片`：`c<序号>` 及其表格、分组、条目。
6. `## 会中实时笔记`：`n<序号> · 时间戳`，每点一行转述，下面缩进列出「解读」。助手的提示语不列。
7. `## 核对线索`：只在实时笔记里出现的数字、提到“我”的位置（超过 12 处时只给数量）、各项警告。
8. `## 这个页面里没有的`：逐字稿、屏幕共享、聊天、日期、未被识别的在场者。

### context.json

| 字段 | 含义 |
| --- | --- |
| `schema` | `lov-tencent-meeting-cowork/v1` |
| `source` | `kind`、`input`（`url` 或 `html`）、`url`、`shortLink`、`page` |
| `meeting` | `title`、`abstract`、`date`（固定为 null）、`speakers`、`meta` |
| `participants[]` | `name`、`isSelf`、`isSharer` |
| `self` / `selfProblem` | `name`、`source`、`match`；认不出时 `self` 为 null，`selfProblem` 为 `unmatched`、`ambiguous` 或 `unknown` |
| `todos[]` | `id`、`task`、`owners`、`mine`、`source` |
| `summary` | `sections[]`（`heading`、`isTodo`、`points[]`、`subsections[]`）与换好人名的 `raw` |
| `cards[]` | `id`、`type`、`title`，以及 `items`、`table`、`groups`、`todos` 之一 |
| `liveNotes[]` | `id`、`at`、`kind`、`bullets[]`（`id`、`text`、`commentary`、`people`、`raw`） |
| `assistantMessages[]` | 助手提示语的时间戳与文字 |
| `counts` | 要点、卡片、待办、实时笔记及其点数 |
| `signals` | 见下节 |
| `warnings` | 读取与解析中的提醒 |

标准输出是其中的 `source`、`meeting`、`self`、`todos`、`counts`、`signals`、`warnings`，加上
`files`（目录与两个文件的路径）和 `hints`。

## signals

| 字段 | 含义 |
| --- | --- |
| `summaryPresent` / `cardsPresent` / `liveNotesPresent` | 三部分各自有没有内容；缺实时笔记时无法核对摘要的漏项 |
| `liveNotesEnd` | 最后一条实时笔记的时间戳，是偏移不是钟点 |
| `todoIds.mine` / `others` / `unassigned` / `unknown` | 我的、别人的、没标负责人的、因不知道“我”是谁而无法归属的待办 |
| `selfMentionCount` / `selfMentionRefs` | 实时笔记里提到“我”的点（最多列 80 个） |
| `numbersOnlyInLiveNotes[]` | `value` 与 `refs`：只在实时笔记里出现的数字及位置（最多 40 个） |
| `unresolvedMentions` | 没对上发言人的占位符个数 |

## 局限

- 只读元宝笔记分享页。录制回放、智能纪要、会议详情等页面不解析，需要用户提供文本。
- 需要登录才能看的分享页读不到，脚本不处理登录；用户可以把已登录浏览器里的页面另存为 HTML。
  这条路径用 `curl` 保存的页面验证过，浏览器另存的文件只要保留了数据块同样可读。
- 内容全部是 AI 生成的转述：语音识别可能把人名、机构名、数字写错，同一名称可能有几种写法。
- 「解读」的拆分是启发式规则，只在一场会议的 28 点上核对过。
- 页面结构由腾讯会议决定，改版后可能读不到；届时表现为 `no-page-data` 或 `unsupported-page`。
