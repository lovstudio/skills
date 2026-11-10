# 腾讯会议工作搭子 · Tencent Meeting Cowork

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

给一个腾讯会议「元宝笔记」的分享链接，AI 读懂这场会：哪些是你的事、对方答应了什么、哪些要求
没进待办清单，然后把会后的活做出来。只起草，不发送。

```text
"目标协同：https://meeting.tencent.com/ys/…"
      │
      ▼
meeting_context.py（一次不带登录态的读取）
      │  notes.md：带编号的摘要要点、图文卡片、待办、会中实时笔记；
      │  AI 的转述与「解读」分开；只在实时笔记里出现的数字
      ▼
Agent：brief / catch-up / work / follow-up
      │
      ▼
行动简报 · 会议速览 · 你答应的材料 · 跟进消息草稿（未发送）
```

## 为什么不直接看纪要

元宝笔记页面上的摘要是 AI 对会议的再概括。在第一个真实案例里，它漏掉了三样东西：

- **口头提的要求**：对方在会上要求补充的数据，没有进“待办事项”。
- **具体数字**：实时笔记里有，摘要里没有，或者被合并成了另一种说法。
- **会议后段才定下来的结论**：摘要按主题归纳，最后拍板的方向没有写进去。

另外，会中实时笔记每一点末尾的加粗句是 AI 对意图的评论，不是任何人说的话。本 Skill 把它单独
标成「解读」，不让它混进你发给对方的文字里。

## 能做什么

| 模式 | 你说 | 你得到 |
| --- | --- | --- |
| brief | 只给链接；“这场会后我要做什么” | 会后行动简报：我的事、对方的事、没进待办的要求、悬而未决的条件、要核对的专名与数字 |
| catch-up | “帮我过一下这场会”“我没参会” | 定下来的、没定的、与我有关的，以及摘要没写的要点 |
| work | “把我答应给对方的大纲整理出来” | 需求单（带编号）+ 成果本身；没有依据的地方标【待确认】 |
| follow-up | “起草一条会后跟进” | 只写双方确认过的共识的跟进消息，放在代码块里，注明未发送 |

每条结论都带编号（`t2`、`s7`、`c2`、`n9.2`），可以回到纪要里核对。

## 前提

- Python 3.9+，只用标准库。
- 能访问 `meeting.tencent.com`。
- 一个不登录就能打开的元宝笔记分享链接；需要登录才能看的，先在浏览器里把页面另存为 HTML。

## 安装

```bash
npx lovstudio skills add tencent-meeting-cowork
```

免费 Skill，不需要登录。

## 使用

在 Agent 里直接说：

- “目标协同：<元宝笔记分享链接>”
- “这场会后我要做什么？<链接>”
- “根据这场会，把我答应给对方的大纲搭出来，再起草一条跟进消息”
- “我没参加这个会，帮我过一下，哪些要我表态”

也可以手动运行上下文构建器：

```bash
python3 scripts/meeting_context.py context --url "https://meeting.tencent.com/ys/<短链>" --self-name "你的会议昵称"
python3 scripts/meeting_context.py context --html saved-page.html
python3 scripts/meeting_context.py clean --out "<context 输出的 files.dir>"
```

### context 参数

| 参数 | 说明 | 默认 |
| --- | --- | --- |
| `--url` | 元宝笔记分享链接，只接受 `https://meeting.tencent.com/` 下的地址 | 与 `--html` 二选一 |
| `--html` | 该分享页另存的 HTML 文件 | — |
| `--self-name` | 你在会议里显示的名字，可重复 | 按笔记归属人推定 |
| `--out` | 输出目录 | 系统临时目录下的私有目录 |
| `--timeout` | 联网超时秒数 | 20 |

退出码：0 成功，1 出错，4 链接失效或页面没有纪要。出错时 JSON 里有 `error.stage`、`error.code`
与下一步的 `error.hint`。

## 读不到链接时

| 情况 | 表现 | 怎么办 |
| --- | --- | --- |
| 链接失效 | `short_link_not_found` | 请分享者重新生成链接 |
| 读到的页面里没有纪要（可能需要登录，或纪要还没生成） | `no-page-data`、`redirected-away` 或 `empty-minutes` | 在已登录的浏览器里把页面另存为 HTML，用 `--html` 读取；或把纪要文本粘贴给 Agent |
| 不是元宝笔记（如录制回放） | `unsupported-page` | 把页面里的纪要或转写文本粘贴给 Agent |

脚本不处理登录，也不会索取账号、Cookie 或验证码。

## 用户 Profile（跨 session）

在 `skill.yaml` 中声明 `user-profile/v1`。你明确说要记住的偏好会写进
`skills.lov-tencent-meeting-cowork.records`：`self_names`（你在腾讯会议里的名字）、
`followup_style`（跟进消息的风格）、`followup_channel`（跟进发在哪里）、`counterpart_notes`
（某个对象的关系备注）。会议内容、分享链接、草稿和参会人名单从不写入。
详见 [`references/user-profile.md`](references/user-profile.md)。

## 隐私

- 只发一次不带登录态的请求读取分享页；不登录、不保存 Cookie、不调用需要账号的接口。
- 页面里的账号标识、会议号、房间号只在解析时使用，不写入任何输出。
- 上下文写在权限 0700 的私有临时目录；`clean` 只删除带本 Skill 标记的目录。
- 不发送任何消息，不修改会议与笔记。
- 脚本本身不上传任何内容；纪要会作为上下文交给你正在使用的 Agent 宿主处理，受该宿主的数据政策约束。
- 分享链接本身就是访问凭证，拿到链接的人都能看到纪要。不要把链接或上下文文件放进公开仓库
  或交付物。

## 局限

- 只读元宝笔记分享页；录制回放、逐字稿、会议聊天、屏幕共享都读不到，页面也不提供会议日期。
- 纪要全部是 AI 的转述：人名、机构名、数字可能被语音识别写错，对外使用前需要你核对。
- 页面结构由腾讯会议决定，改版后可能读不到。目前只在一场真实会议上核对过，细节见
  [`references/context-contract.md`](references/context-contract.md)。

## 原子组合

没有必需的上游。需要长文、格式转换、完整方案，或想对照微信里的语气时，可以把成果交给
`lov-writing-style`、`lov-any2docx` / `lov-any2pdf`、`lov-proposal`、`lov-wdb-cowork`。
详见 [`references/skill-composition.md`](references/skill-composition.md)。

## 可信度卡与用户案例

- [`skill-card.yaml`](skill-card.yaml) / [`skill-card.md`](skill-card.md)：用途、依赖、风险、输出与维度地图。
- [`cases/cases.json`](cases/cases.json)：真实案例（已脱敏）。
- [`pricing-card.yaml`](pricing-card.yaml)：价值锚点、交付边界和复评条件；免费入口，0 Credits。

## 质量门

```bash
python3 scripts/test_meeting_context.py
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.9+（运行脚本只用标准库）
- PyYAML（只在运行 `validate_skill.py` 时需要）

## License

MIT
