# 主流 Agent Harness 设计与实现 01：System Prompt

![文章首图](http://cdn.cs-magic.cn/picgo/2026/08/26/article-opening-vertical-af8bd2.jpg?imageslim%7CimageMogr2/format/jpeg/size-limit/1000k!)


同一个模型，放进不同的 Agent Harness，可能像换了一个人。

有的会先交代准备怎么做，过程中持续更新；

有的拿到任务就进仓库，改完、验证、用三句话结束；

有的几乎没有固定性格，你装什么模型、写什么项目规则，它就长成什么样；

还有的连“应该怎么使用 read 工具”都不是中央 prompt 说了算，而是由工具插件自己注册。

这些差异，不只是模型能力造成的。

**模型决定了 Agent 大致能做到什么，Harness 则在很大程度上决定了它会怎么做、做到哪里停、又以什么方式和你相处。**

而 System Prompt，是其中最容易暴露产品品味的一层。

## 1. Intro

### 1.1 什么是 Agent Harness

**Agent Harness，简单说，就是包在模型外面的那套运行系统**。

它负责组装上下文、暴露工具、管理权限、保存会话、压缩历史；也负责告诉模型当前目录在哪里、能不能改文件、什么时候应该继续、什么时候必须问用户，以及做完以后应该怎样汇报。

所以，一个 coding agent 从来不只是“某个模型加一段 prompt”。

模型、System Prompt、tool schema、Agent Loop、sandbox、permission、memory、Skills 和项目文档，共同构成了最后那个会读代码、跑命令、修改文件的 Agent。

我越来越愿意用 Harness 来理解今天的 Agent 产品，而不是只盯着模型名称。

因为模型可以被替换，Harness 才是产品真正积累工作方式的地方。

### 1.2 标的选取依据

这一期，我选了 Codex、Claude Code、Pi 和 DeepSeek Harness，也就是 DSH。

Codex 和 Claude Code，是目前最成功的两个 coding agent。

Pi 和 DSH，则是目前两个最开放的 Harness 样本。它们适合回答另一个问题：如果把这套设计一路拆到源码、插件和注册表，System Prompt 原本还可以怎么做？

前两个，代表成熟产品的取舍。

后两个，让我们看见这些取舍背后的自由度。

### 1.3 System Prompt 的定义与变迁

在模型 API 里，System Prompt 原本是一个很清楚的概念：应用在用户消息之前，给模型一组更高优先级的指令。

例如 OpenAI Responses API 会把 `instructions` 作为 system 或 developer message 插入上下文；在同一套指令层级中，system/developer 的优先级高于 user message。[OpenAI Responses API](https://developers.openai.com/api/reference/cli/resources/responses/methods/create)

但到了 Agent Harness 里，这个词已经开始失真。

模型默认指令被叫作 System Prompt。

项目里的 `AGENTS.md` 和 `CLAUDE.md` 也被叫作 System Prompt。

宿主应用追加的规则，还是 System Prompt。

可它们真正发给模型时，可能根本不在同一个 role，也不拥有相同的优先级、缓存方式和覆盖关系。有些内容甚至不在 prompt 里，而是由 tool schema、权限确认和代码级 sandbox 强制执行。

所以，本文说的 System Prompt，只能当作一个方便讨论的总称：

**它不是某一个字符串，而是 Harness 在用户任务之前和之上，为模型建立工作方式的整条装配链。**

这篇文章的检查时间是 2026 年 8 月 26 日。

| Agent | 检查版本 | 我实际能看到的东西 |
| --- | --- | --- |
| Codex | `codex-cli 0.149.1` | 模型目录下发的 `base_instructions` |
| Claude Code | 当前 CLI `2.1.233` | 当前官方接口 + `2.1.88` source map 泄露的历史源码快照 |
| Pi | `@mariozechner/pi-coding-agent 0.73.1` | `buildSystemPrompt()` 及完整资源加载源码 |
| DSH | `0.1.0-rc.8` | `ctx.systemPrompt` 注册表和各插件的 prompt sections |

这里最麻烦的是 Claude Code。

Anthropic 官方明确表示，Claude Code 当前的内部 System Prompt 不公开。但 2026 年 3 月 31 日，`2.1.88` 的 npm 包曾经带出一份完整 source map。我本地保存了这份 TypeScript 快照，因此能够对照 `getSystemPrompt()`、`buildEffectiveSystemPrompt()`、section cache、`getUserContext()` 和最终 API input 的合并链路。

但历史源码不等于当前源码。

下面涉及 Claude Code 默认正文的分析，来自这份历史快照；涉及今天还能使用哪些控制入口，则以当前 `2.1.233` CLI 和官方文档为准。

这一次，我不准备只给你看我的转述。

本文使用的四份材料已经和正文一起放进 GitHub，并固定到同一次提交：

- [Codex `gpt-5.6-sol` base instructions](prompts/codex-gpt-5.6-sol-base-instructions.txt)
- [Claude Code `2.1.88` System Prompt Builder](prompts/claude-code-2.1.88-system-prompt-builder.ts)
- [Pi `0.73.1` `buildSystemPrompt()`](prompts/pi-0.73.1-system-prompt-builder.ts)
- [DSH `0.1.0-rc.8` rendered System Prompt](prompts/dsh-0.1.0-rc.8-rendered-system-prompt.md)

你可以在 [LovStudio Prompt Review](https://lovstudio.ai/prompts?source=agent-harness-book) 里直接查看、搜索和复制全文，也可以回到 [GitHub 仓库](https://github.com/lovstudio/agent-harness-design-and-implementation/tree/main/chapter-01-system-prompt) 对照版本、来源与文章本身。

这很重要。System Prompt 更新得太快，截图和二手转述很容易失去上下文。把原始材料、版本说明和文章放在一起，读者才能判断我到底是在复述事实，还是借事实表达自己的判断。

## 2. Design & Implementation

### 2.1 Codex：一位有主体感的同事

![Codex：一位有主体感的同事](http://cdn.cs-magic.cn/picgo/2026/08/26/codex-e2ed3b.jpg?imageslim%7CimageMogr2/format/jpeg/size-limit/1000k!)

在 `codex-cli 0.149.1` 里执行 `codex debug models`，可以读到模型目录下发的原始 JSON。

我当时使用的 `gpt-5.6-sol`，`base_instructions` 与 `model_messages.instructions_template` 完全相同：17,730 个 JavaScript 字符，168 行。

它不是一段简短的“你是一名编程助手”。

我按标题拆下来，大致有六块：Preamble、Personality、Working with the user、Rules for getting work done、Destructive Actions 和 Using skills。

真正让我意外的，是它对“人格”的执着。

Codex 要求 Agent 拥有“curious, rich personality”，像老朋友一样自然交流；用户应该感觉自己面对的是“another subjectivity”，对话则要像和一位“collaborative thought partner”共同工作。

它不满足于工具调用正确。

它希望模型理解用户处在什么水平，预判用户接下来可能会问什么，在陌生任务里主动补齐陷阱和预期，并让整个合作过程拥有连续的人格。

后面的具体规则，也都在服务这套关系：先讲结果，再讲过程；少用行话；工具调用前先交代准备做什么；长任务中持续更新；用户中途插话时，判断是在追加要求还是替换原任务；上下文压缩之后，也不能像失忆一样从头再来。

但 Codex 并没有因此把主动性无限放大。

它把任务分成回答、诊断、修改、构建和监控等类型：回答和诊断不自动获得修改权限，修复和构建才意味着实施；可逆的本地动作可以继续，涉及外部系统、额外授权或破坏性操作，则要停下来确认。最后，它甚至拿出完整一章规定 Skill 应该如何发现、读取和执行。

所以 Codex 的 `base_instructions`，与其说是一份编程规范，不如说是一份完整的 Agent 产品体验稿：人格、沟通、工作流、安全和扩展协议，全写进同一份“员工手册”。

在实现上，这份 base prompt 仍然不是最终 input 的全部。

运行时还会叠加 developer instructions、项目文档、用户消息、会话历史、工具定义、权限环境、Skills 和宿主应用上下文。常规扩展入口是 `developer_instructions`；如果真要完整覆盖默认底座，则可以使用 `model_instructions_file`。OpenAI 在公开 schema 里同时警告，这会让模型偏离与 Codex 配套的默认指令，因此不建议常规使用。[Codex config schema](https://github.com/openai/codex/blob/main/codex-rs/core/config.schema.json)

这套设计的好处是，换一个任务，Agent 仍然很像 Codex。

代价也一样明显：house style 很重，prompt 更长，规则之间更容易重叠；模型可以自由发挥的，不再是“怎么成为一个 Agent”，而是这套人格与工作方式之内的局部判断。

**Codex 最用力调的，是关系。**

### 2.2 Claude Code：一名严谨的工程师

![Claude Code：一名严谨的工程师](http://cdn.cs-magic.cn/picgo/2026/08/26/claude-code-364165.jpg?imageslim%7CimageMogr2/format/jpeg/size-limit/1000k!)

Claude Code 的历史 prompt，几乎走向另一个方向。

它当时的 System Prompt 至少分成两大块。

第一块是静态内容：身份与基本系统规则、任务执行方式、actions、工具使用原则、语气和输出效率。

第二块是动态内容：会话指引与 Skills、auto-memory、当前模型和运行环境、语言、output style、MCP server instructions、scratchpad，以及 tool result clearing 等模型特定规则。

静态与动态之间还有一条明确的 cache boundary。前面稳定的大段内容尽可能复用，后面与当前会话有关的内容单独更新。MCP 连接状态可能在 turn 之间变化，因此又走一条专门的非缓存路径。

这已经不只是 prompt writing。

这是 prompt engineering 里真正的 engineering。

源码还暴露了一个很容易被忽略的细节：`CLAUDE.md` 当时并不在这组 system sections 里。`getUserContext()` 先读取它，`prependUserContext()` 再把它包进一条带 `<system-reminder>` 标记的 user-role message；Git 状态等 `systemContext`，才会追加到 System Prompt 数组。

当前官方接口则保留了两种非常不同的操作：`--append-system-prompt` 在默认内容之后追加，`--system-prompt` 直接替换；文件版本也分别存在。[Claude Code CLI reference](https://code.claude.com/docs/en/cli-usage) Agent SDK 还把最小默认 prompt、`claude_code` preset 和完整自定义字符串明确区分开来。[Modifying system prompts](https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts)

但 Claude Code 最有辨识度的，不是这些 API。

是它对工程范围近乎偏执的控制。

历史正文要求：收到含糊的代码请求，不要只在聊天里给答案，要去当前仓库里完成它；修改前先读代码；非必要不新建文件；第一次方案失败后先诊断，不要盲目重试，也不要一次失败就放弃原本可行的路线。

最能说明品味的，是那段 anti-overengineering 规则。

不要顺手加功能，不要借修 bug 清理周边代码，不要为不可能发生的内部场景增加 fallback 和 validation，不要为一次性操作造 helper，也不要为假想的未来需求设计抽象。历史源码甚至直接写道：三行相似代码，可能比一次过早抽象更好。

这不是一般意义上的“保持简洁”。

这是在主动对抗大模型最常见的一种讨好行为：为了显得做得多，把一个局部任务扩成一场重构。

它对输出也同样克制：没有用户要求就不用 emoji，不做工期估算，先给答案或动作，不复述问题，不逐步播报所有例行操作；“一句话能说完，就不要写三句”。到了动作安全部分，它关心的关键词也不是亲和力，而是 reversibility、blast radius 和授权范围——一次允许 push，不代表以后所有 push 都被允许。

更有意思的是，历史源码里还留着模型调教本身的痕迹。

有些规则旁边直接标着 model launch counterweight：模型爱写过多注释，就追加“默认不要写注释”；模型容易把没验证的结果说成完成，就追加真实回报和完成前验证；模型过于顺从，就提醒它发现用户误解和相邻 bug 时应该指出来。这些条款还被放进条件分支，准备经过 A/B 验证后再决定是否普遍下发。

这说明 Claude Code 的 System Prompt 不只是一份价值观。

它还是一组针对具体模型行为不断打补丁的校准层。

这种调法的优势是 scope 很稳：少做、做准、验证完再说。代价是默认人格更像 terminal operator，复杂背景和设计取舍有时会被压得过短。这份历史版本同时提供 Explanatory 和 Learning output style，某种程度上就是给默认的克制留出两个显式出口。

**Claude Code 最用力调的，是克制。**

### 2.3 Pi：请叫我没有感情的杀手

![Pi：请叫我没有感情的杀手](http://cdn.cs-magic.cn/picgo/2026/08/26/pi-614908.jpg?imageslim%7CimageMogr2/format/jpeg/size-limit/1000k!)

Pi 的核心，不是一份藏在安装包里的长文本，而是一个公开的 TypeScript 函数：[`buildSystemPrompt()`](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/src/core/system-prompt.ts)。

这个函数接收自定义基础 prompt、当前启用的工具和简介、工具贡献的 guidelines、追加 prompt、当前工作目录、项目 context files 和 Skills，然后在每次会话启动时组出最终结果。

我用四个最小工具简介、空项目上下文、空 Skills 和固定工作目录做了一次受控构造，得到 1,662 个字符、24 行。

它的默认正文短得近乎固执。

开头只有一个朴素身份：你是在 Pi 这个 coding agent harness 里工作的 expert coding assistant。接下来列出这一轮真正可用的工具，再根据工具组合决定要不要提醒“文件探索优先使用 grep、find、ls，而不是 Bash”。无论工具怎么组合，固定保留的通用行为只有两条：回复简洁，处理文件时把路径写清楚。

剩下篇幅最多的，反而是 Pi 自己的文档入口：只有当用户询问 Pi、SDK、扩展、主题、Skills 或 TUI 时，才去读哪些文档，并沿着 Markdown 引用继续读完。

没有长篇人格。

没有通用的自主权哲学。

也没有把代码审美、安全边界和沟通节奏全都预写进去。

Pi 不是没有设计，而是拒绝替所有模型预设同一种人格。

它的默认 prompt 更像 bootloader：告诉模型自己在哪里、手里有哪些接口、项目又追加了什么；至于 Agent 应该拥有怎样的性格和工作哲学，交给底层模型、项目 context、扩展和用户自己的 `SYSTEM.md`。

Pi 也支持追加与替换：`.pi/APPEND_SYSTEM.md` 或 `--append-system-prompt` 保留默认骨架并追加；`.pi/SYSTEM.md` 或 `--system-prompt` 替换默认身份与规则。整个发现过程都能在公开的 [`resource-loader.ts`](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/src/core/resource-loader.ts) 里追完。

但替换并不等于清空 Harness 提供的一切。

在我检查的 `0.73.1` 里，即使传入 `customPrompt`，Pi 仍会继续追加项目 context files、Skills、当前日期和工作目录。你换掉的是默认骨架，不是所有运行时上下文。

好处是透明、轻、容易替换，也很少拿一套产品人格去干扰不同模型。代价是换一个模型，Pi 的“性格”可能跟着明显变化；项目没有补充规则时，一致性和护栏更多依赖模型原本的训练。

**Pi 最用力调的，是边界。**

### 2.4 DSH：您自个儿爱咋滴咋滴

![DSH：您自个儿爱咋滴咋滴](http://cdn.cs-magic.cn/picgo/2026/08/26/dsh-cea363.jpg?imageslim%7CimageMogr2/format/jpeg/size-limit/1000k!)

DSH 走得比 Pi 更远。

它目前仍然是 developer preview，所以我不会拿它的成熟度去和 Codex、Claude Code 比。我把它放进来，是因为它把“everything is a plugin”做得足够彻底：model adapter、tool registry、session log、agent loop 是插件，System Prompt 也是。[DeepSeek Harness architecture](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md)

DSH 提供了一项 `ctx.systemPrompt` 注册表服务。

每个插件可以只为自己负责的部分注册一个 `PromptSection`：`name` 决定稳定身份，`order` 决定组装顺序，`text` 可以是静态文本，也可以按当前 Agent 动态求值，`complete` 则表示这一段要成为唯一的完整 System Prompt。

它还预留了明确的顺序带：`-100` 放 Harness identity，`0` 放 deployment persona，`100–199` 留给工具 guidance。[DSH System Prompt Assembly](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/system-prompt.md)

最前面的固定 identity，其实只有一句：

> You are an AI agent powered by DeepSeek Harness.

真正具体的内容，分散在插件自己的 section 里。

- `read` 插件要求用 read 而不是 shell 里的 `cat`，大文件用 offset 和 limit 续读；
- `write` 插件提醒完整写入会覆盖现有文件，应该先读，并优先用 edit 做局部修改；
- `grep` 插件要求搜索内容时不要调用 shell grep 或 `rg`；
- Bash 插件要求每次检查 exit code，失败后先调查；
- Jobs 插件要求记住所有后台任务 ID，不要 busy-poll，也不要在任务还跑着时重复做同一份工作；
- 连 Web 端如何把最终文件引用渲染成可点击链接，都由 UI 插件追加自己的 prompt。

这些句子没有统一的人格腔调，更像一组贴着实现写的局部协议。

谁实现能力，谁就负责告诉模型这项能力应该怎么用。插件卸载，工具和对应 guidance 一起消失；插件改变语义，也不需要去中央 prompt 里寻找一段可能早已失配的旧说明。

每次 Agent Loop 开始之前，`assemble()` 会把当前 scope 可见的 sections、动态 contexts、tool schemas 和 prompt variables 重新组起来。Agent 级 section 可以遮蔽同名全局 section；某个 section 如果声明 `complete: true`，它就会压掉其他内容，独自成为这一轮的 System Prompt。[`dsh-system-prompt` README](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/core/system-prompt/README.md)

但 DSH 没有把所有动态信息都塞进 system role。

`ctx.systemPrompt.context()` 注册的 runtime context，会在默认 Agent Loop 里转成可持久化的 user-role snapshot；项目里的 `AGENTS.md` 和 `CLAUDE.md`，也由独立插件加载为 durable user message，而不是 system section。

DSH 只是拒绝让一个中心作者替所有工具预写行为，选择把调教权交给最了解实现的人。它开放的不是某一份默认 prompt 全文，而是 prompt 的组装权：谁可以提供规则，谁在前、谁在后，哪一层可以遮蔽，什么情况下可以完整接管。

这种设计更透明，也更需要工程能力。当 prompt 被拆给整个插件系统，调试就不再是打开一个文件，而是要追查 scope、order、shadow、context snapshot 和当前插件组合。

**DSH 最用力调的，是协议。**

### 汇总表

把四家压缩到一张表，大概是这样：

| Harness | 设计中心 | 最有辨识度的具体内容 | 最终塑造的 Agent | 主要代价 |
| --- | --- | --- | --- | --- |
| Codex | 模型目录下发底座，再叠加运行时规则 | rich personality、持续沟通、任务权限分类、完整 Skill 协议 | 有主体感的协作同事 | house style 重，规则长且可能重叠 |
| Claude Code | 静态与动态 sections 分层，并围绕 cache 组装 | 不扩大 scope、不做过早抽象、先读再改、验证后如实回报 | 克制而可靠的工程师 | 可能显得冷、短，对教学和架构讨论不够主动 |
| Pi | 一个公开函数按工具与上下文动态生成 | 当前工具清单、两条通用 guideline、Pi 文档路由 | 由模型和项目自行定义的轻量助手 | 一致性和护栏更依赖底层模型与外部配置 |
| DSH | 插件注册有序 sections，并允许 scope shadow | 每个工具各自贡献使用协议，后台任务和 UI 也拥有 section | 由插件协议共同构成的 Agent | 整体人格不统一，组合质量取决于插件作者 |

### 五维雷达图

为了不让评价标准跟着产品走，四家统一按下面五个维度打分：

- **默认人格**：Harness 预设了多强的关系感与主体性。
- **行为约束**：默认规则对 scope、验证、安全和工具行为规定得多细。
- **用户定制**：用户能否方便地追加、替换和维护自己的规则。
- **Prompt 组合**：Prompt 是否被拆成可排序、可替换、可遮蔽的 sections 或插件。
- **跨任务一致**：换任务或换项目后，默认工作方式是否仍然稳定。

![四种 Agent Harness 的 System Prompt 五维雷达图](http://cdn.cs-magic.cn/picgo/2026/08/26/agent-harness-radar-c540b5.png?imageslim%7CimageMogr2/format/jpeg/size-limit/1000k!)

这里的“向外”只代表某项特征更强，不是综合质量，更不是越大越好。Pi 的默认人格只有 1 分，恰恰是它对某些用户最有吸引力的地方。

如果用户只说一句“修掉这个 bug”，四家因此会走出不同的默认姿势。

Codex 会把它当成一次需要持续沟通、实施和验证的协作；Claude Code 会紧盯任务边界，用最小改动解决，不顺手装修周边；Pi 主要把工具和项目规则准备好，具体姿势留给当前模型；DSH 则要看这一轮装了哪些插件，由搜索、文件、Shell、Job 和 UI 各自的协议共同拼出行为。

System Prompt 并不只是教模型“做对”。

它还在定义，什么叫这家产品眼里的“对”。

## 3. Conclusion

### 3.1 对于 Agent Harness 研究员

如果你在研究 Agent Harness，最容易掉进去的坑，就是下载四份 prompt，然后开始比长度、数规则、找金句。

Codex 的 `base_instructions` 有 17,730 个字符，而 Pi 的受控骨架只有 1,662 个字符。看起来差了一个数量级，但这两个数字根本不在同一个口径里。

Codex 统计的是模型目录中的完整 base template；Pi 统计的是没有项目上下文和 Skills 的最小受控构造；Claude Code 的长度会随工具、环境、memory、MCP 和运行模式变化，我们又看不到当前完整正文；DSH 更不存在一份脱离插件组合仍然成立的唯一 prompt。

长，不代表完整。

短，也不代表先进。

真正应该比较的，至少有五件事：

1. **Content**：它具体在纠正模型的什么行为？
2. **Role**：规则最终进入 system、developer 还是 user？
3. **Lifecycle**：它何时生成、何时缓存、何时重算？
4. **Ownership**：是模型厂商、Harness、插件、项目还是用户拥有它？
5. **Enforcement**：它只是一句自然语言，还是有 tool schema、sandbox 和权限系统托底？

同一份项目指令，在四家甚至拥有不同的“宪法地位”：

| Harness | 默认底座 | 项目指令常见位置 | 追加与覆盖 |
| --- | --- | --- | --- |
| Codex | 模型目录下发 `base_instructions` | developer 或项目运行时 input | `developer_instructions` 追加；`model_instructions_file` 覆盖 |
| Claude Code | 静态 sections + 动态 sections | `CLAUDE.md` 进入 user context | append 保留默认；system-prompt 完整替换 |
| Pi | `buildSystemPrompt()` 动态生成 | System Prompt 中的 `Project Context` | `APPEND_SYSTEM.md` 追加；`SYSTEM.md` 替换骨架 |
| DSH | 插件注册有序 sections | durable user-role message | section 追加、scope shadow 或 `complete` 接管 |

内容相同，位置不同，它们就不是同一条规则。

OpenAI 的模型指南甚至明确建议使用 leaner prompt：删掉重复指令，缩短工具描述，再用真实 eval 判断效果。[OpenAI Model guidance](https://developers.openai.com/api/docs/guides/latest-model)

所以，别研究“哪一家的神秘咒语更强”。

研究它如何被生产、装配、执行和验证。

### 3.2 对于应用开发者

如果你是在现有 Agent 之上做应用，最重要的不是复制一份 base prompt，而是先分清自己正在增加哪一种信息。

稳定的人格和通用工作原则，是一层。

应用自己的业务规则和授权边界，是一层。

仓库里的项目约定，是一层。

当前用户、目录、时间、选中对象和运行状态，又是另一层。

把这些东西揉成一个巨型字符串，短期最省事，长期一定最难调。

我的建议是：能追加，就不要为了一个局部需求完整替换厂商底座；稳定政策和动态上下文分开；需要每轮变化的信息，不要污染本来可以缓存的前缀；子 Agent 是否继承项目规则，也必须成为显式设计，而不是碰运气。

更重要的是，不要把 prompt 当权限系统。

“不要删除用户文件”写在 prompt 里，是一条由模型理解的自然语言规则；文件 sandbox、操作确认和可逆工作流，才是 Harness 能够强制执行的机制。

应用开发者真正要设计的，不是一段更聪明的 prompt。

而是一套即使模型偶尔没听懂，也不会立刻出大事的系统。

### 3.3 对于 C 端用户

如果你只想选一个 Agent 把代码写完，我的建议反而最简单：看你最不想反复纠正什么。

这不是四款产品的总排名。模型能力、工具质量、权限系统、上下文压缩、速度、价格和稳定性，都会改变最终体验。

但 System Prompt 决定了一组非常顽固的默认值。你可以每一轮都提醒 Agent 少说一点、不要顺手重构、记得汇报进度；也可以直接选一套本来就更接近你工作习惯的 Harness。

| 你最常面对的情况 | 更适合先试 | 为什么 | 需要接受的代价 |
| --- | --- | --- | --- |
| 需求还不完全清楚，希望 Agent 边做边解释、主动补齐风险 | Codex | 默认把沟通、进度和协作关系放得很重 | 交互存在感更强，喜欢完全安静执行的人可能不适应 |
| 仓库成熟、任务明确，最在意最小改动和不扩大 scope | Claude Code | 默认强压过度设计、无关重构和冗长输出 | 想听完整背景或架构推演时，往往要主动要求 |
| 想自由更换模型，并愿意亲自维护 prompt、Skills 和扩展 | Pi | 默认骨架很薄，行为主要由模型和项目配置决定 | 开箱一致性弱，规则缺口需要自己补 |
| 正在研究或搭建自己的 Agent Harness | DSH | System Prompt 本身就是可组合、可遮蔽的插件基础设施 | 仍是 developer preview，组合与调试成本不适合多数普通用户 |

对大多数只想把代码写好的开发者，真正的日常选择仍然是 Codex 和 Claude Code。

如果你的任务经常从一句模糊想法开始，需要 Agent 和你一起把问题讲明白，我会先试 Codex；如果你的需求通常已经足够明确，最烦 Agent 顺手加戏、扩大 diff，我会先试 Claude Code。

Pi 和 DSH 不是这两款产品的“开源平替”。

它们更适合另一类人：你不只想使用 Agent，还想拥有 Agent 的定义权。Pi 给你一张足够干净的白纸；DSH 则把纸、段落、顺序和覆盖关系都做成了可编程接口。

**不要问谁的 System Prompt 最强，问你最不愿意每一轮重新纠正 Agent 的是什么。**

## 4. End

### 4.1 关于《主流 Agent Harness 设计与实现》系列

这是《主流 Agent Harness 设计与实现》的第一期。

这个系列不准备停在“谁更好用”的体验对比，也不会只搬运一份网上流传的 prompt。我的方法会保持一致：先回到源码、运行时 input 和真实控制接口，再讨论设计选择、产品品味，以及这些选择最终怎样落到用户身上。

这一期最初来自 Yoda 里的一个小问题：工作区动态提示词，最后到底会进入 Codex 的哪一层？

我沿着调用链追到最后，答案是 `developer_instructions`，不是 `base_instructions`。这个实现背景并不复杂，却让我意识到，我们经常把“写了什么”和“写在哪里”混成同一个问题。

把四套 Harness 拆完之后，我的判断反而更简单了：Codex 在调关系，Claude Code 在调克制，Pi 在调边界，DSH 在调协议。

base instructions 不是 Agent 的灵魂，却可能是 Harness 作者写得最诚实的一份产品说明书。

### 4.2 代码、原始 Prompt 和在线版

如果你是在公众号里读到这里，这篇文章负责的是把判断讲清楚。

但它没必要把 17,730 个字符的 Codex base instructions、Claude Code 的历史 TypeScript、Pi 的 Prompt Builder 和 DSH 的渲染结果，全部塞进正文里。

所以，我把文章之外的材料拆成了三层：

1. **GitHub 是源头。** 每一期对应一个独立 Chapter，正文、图片、版本说明和原始材料都放在同一个目录；后面的 Chapter 02、03，也会沿着这套结构继续写下去。
2. **在线博客负责阅读。** 网站直接读取 GitHub 的固定 commit。文章更新到了哪一版，页面就明确显示哪一个 commit，不另外维护一份悄悄漂移的副本。
3. **Prompt Review 负责核对。** 四份材料可以打开全文、搜索、复制，也可以跳回对应的固定版本。你不需要相信我的转述，可以自己看原文。

- [在线阅读《主流 Agent Harness 的设计与实现》](https://lovstudio.ai/research/agent-harness)
- [GitHub：lovstudio/agent-harness-design-and-implementation](https://github.com/lovstudio/agent-harness-design-and-implementation)
- [Review 本期四份 System Prompt](https://lovstudio.ai/prompts?source=agent-harness-book)

发布到公众号时，文末的「阅读原文」应当指向本期在线版。那里不是这篇文章的重复发布，而是继续往源码、版本和后续章节走的入口。

### 4.3 关于手工川工作室（[lovstudio.ai](https://lovstudio.ai)）

手工川工作室，官网：Lovstudio.ai，是一个长期实践 AI Coding、Agent Harness 和个人超级生产力的独立工作室。

我们一边做 Yoda 这样的 Agent Workspace，一边把真实开发中追过的调用链、踩过的坑和形成的判断写下来。

工具一直会换。

我们真正关心的是：普通人能不能理解它、控制它，并最终把它变成自己的生产力。

[lovstudio.ai](https://lovstudio.ai)
