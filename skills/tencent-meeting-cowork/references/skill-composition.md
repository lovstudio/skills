# Skill Group Composition

## Nearby Skills Inspected

| Skill | 路由合同 | 分类 | 结论 |
| --- | --- | --- | --- |
| `lov-wdb-cowork`（微信工作搭子） | 给定联系人或群名，读本机微信会话，起草回复、追进度、整理待办 | adjacent，optional downstream | 同一系列、不同数据源。会后跟进常在微信里发生：用户想对照自己在该会话里的语气，或确认材料是否已经发过时，把跟进草稿与对象名交给它。两者没有共享代码 |
| `lark-vc` / `lark-minutes` | 飞书会议记录、纪要、妙记的查询与编辑 | not composed | 平台不同，数据通道是飞书开放接口；用户给的是飞书链接时转交 |
| `lark-workflow-meeting-summary` | 把一段时间内的飞书会议纪要汇总成报告 | not composed | 面向多场会议的周期汇总；本 Skill 面向单场会议的会后行动 |
| `lark-vc-agent` | 机器人加入进行中的飞书会议并读取会中事件 | not composed | 会中能力；本 Skill 只处理会后的纪要 |
| `lov-voice2srt` | 把录音、视频转成 SRT、JSON 与纯文本 | optional upstream | 用户只有录音、没有纪要时，先由它产出文字，再作为粘贴文本走本 Skill 的降级路径 |
| `lov-writing-style` / `lov-human-writing` | 按用户文风写长文 / 改进稿件的作者性 | optional downstream | work 模式的成果是长文（方案正文、课程介绍）时，把需求单与依据交给它们；短消息由本 Skill 自己起草 |
| `lov-any2docx` / `lov-any2pdf` | Markdown 转 Word / PDF | optional downstream | 成果要以文件发给对方时转换格式 |
| `lov-proposal` | 根据客户需求生成完整商务方案 | optional downstream | 会上对方要的是一份完整方案时，把需求单（含对方的顾虑与已定条件）作为它的输入 |
| `lov-add-task` / `lark-task` | 往当前任务清单 / 飞书任务里加事项 | optional downstream | 用户要把行动项放进任务工具时交接清单文本；写入由用户确认 |
| `lov-fact-check` | 用公开资料校验事实命题 | not composed | 纪要里的专名与数字要向用户本人核对，公开资料检索回答不了 |
| `lov-interview-media-creator` / `lov-media-creator` | 把采访或会议录像剪成短片 | not composed | 输入是视频素材，产出是成片，与会后行动无关 |
| `lov-branding-consistency` | 读者可见文本的品牌与语境门禁 | declared dependency | 只约束本 Skill 新写的对外文字；纪要转述与用户原话保持原样 |

检查范围：本机已安装的全部 Skill 与本地源码目录。检索“腾讯会议”“元宝笔记”后，没有发现读取腾讯
会议纪要的现成能力；唯一提到腾讯会议的是采访短片 Skill 里对会议录像画面的处理说明。

## Atomic Handoffs

```text
腾讯会议元宝笔记分享链接（或该页面另存的 HTML）
   │  一次不带登录态的读取
   ▼
meeting_context.py → notes.md + context.json（私有临时目录）
   │
   ▼
Agent：brief / catch-up / work / follow-up
   │  行动简报、会议速览、工作成果、跟进消息草稿（未发送）
   ▼
可选下游：lov-writing-style（长文）、lov-any2docx / lov-any2pdf（文件）、
          lov-proposal（完整方案）、lov-wdb-cowork（微信里的语气与发送状态）

可选上游：lov-voice2srt（只有录音时先转成文字）
```

- 本 Skill 的产物合同：`references/context-contract.md`（`lov-tencent-meeting-cowork/v1`）。
- 下游交接物是文本或 Markdown 文件，附带需求单与依据编号；交接时不传 `context.json`，也不传分享链接。
- 上游交接物是纯文本：没有编号，也不区分摘要与实时笔记，按粘贴文本的降级路径处理。
- 最终验收归本 Skill：每条结论有编号或用户确认作依据，待核对与待确认项已标明，覆盖范围说清，
  没有发送任何消息。

## Overlap Decisions

- 与 `lov-wdb-cowork` 的边界：它读微信会话，本 Skill 读会议纪要。两者都做“起草、追进度、把活
  做出来”，但证据的性质不同：微信消息是当事人的原话，会议纪要是 AI 的转述。所以本 Skill 多出
  “三处对齐”“解读不外发”“专名与数字先核对”三条规则。没有合并成一个 Skill，是因为数据通道、
  上下文契约与可信度假设都不同，合并只会让两边的规则互相稀释。
- 与飞书会议系列的边界：按平台分。本 Skill 不使用腾讯会议开放平台的凭据，只读分享页；预约
  会议、查询录制、读取逐字稿都不在这里做。
- 没有复用通用的网页抓取能力：分享页的数据在页面内嵌的数据块里，人名用占位符表示，实时笔记
  把转述和评论写在同一句里，需要专门解析才能得到带编号、可回溯的上下文。

## Composition Decision

**Single Skill。** 取数解析、四种协作模式与交付规则服务同一个用户结果：针对一场会，把会后的事
办了。上下文构建器不是可以独立使用的阶段，它的产物只对本 Skill 的规则有意义，拆成 Kit 不会
产生可复用的中间产物。所有相邻 Skill 都是可选交接，不写进 `depends_on`；唯一声明的依赖是
`lov-branding-consistency`。
