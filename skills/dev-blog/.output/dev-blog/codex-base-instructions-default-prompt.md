# Codex 的 base_instructions（默认 prompt）到底写了什么

上一篇写 Codex 的 prompt 层级时，我在 `codex debug models` 的输出里发现了一块很容易被忽略的内容：

```text
base_instructions
```

它不是用户问题，不是项目里的 `AGENTS.md`，也不是 Yoda 通过 `developer_instructions` 追加的动态提示词。

它更像 Codex 出厂时自带的“产品说明书”。

所以我继续往下挖。

在本机当前的 `codex-cli 0.149.1` 里，`gpt-5.6-sol` 的 `base_instructions` 一共有 17,730 个字符、168 行，分成 5 个主章节；在线刷新得到的 model catalog 与 CLI 内置的 `--bundled` catalog 完全一致，SHA-256 都是：

```text
35d8b5d513fff3b55344d5f9f3169305cc276aee053f5be140a77708e0926e7c
```

我原本以为它会是一篇超长的“代码生成秘籍”。

结果不是。

**Codex 的默认 prompt，真正花篇幅定义的不是怎么写代码，而是怎么与人协作、如何判断授权、怎样安全地修改工作区，以及如何加载 Skills。**

这件事很重要。

因为它说明，一个模型为什么表现得像 Codex，靠的不只是模型能力，而是模型之外那套细密的 Agent 行为协议。

## 01. 我是怎么拿到这份默认 prompt 的？

Codex CLI 提供了一个公开调试命令：

```bash
codex debug models
```

它会输出当前 raw model catalog 的 JSON，而不是只列出几个可选模型名称。

从 `gpt-5.6-sol` 这一项里，可以直接读到：

```text
base_instructions
model_messages.instructions_template
```

在这次快照里，两者内容完全相同，长度相同，SHA-256 也相同。

我又跑了一次：

```bash
codex debug models --bundled
```

`--bundled` 会跳过在线刷新，只读取当前二进制内置的 model catalog。结果仍然是同一个哈希。

所以这次看到的不是我从对话行为里猜出来的“隐藏 prompt”，也不是一次模型套话分析，而是 Codex CLI 明确暴露的模型配置快照。

但边界也必须说清楚：

**它只能证明 `codex-cli 0.149.1` 在 2026 年 8 月 26 日为 `gpt-5.6-sol` 提供了这份 base instructions，不能证明 OpenAI 服务端没有其他平台规则，也不能保证未来版本仍然逐字相同。**

能复现。

但不是永恒真理。

## 02. 17,730 个字符，主要写了什么？

我按一级标题把整份 prompt 拆开，得到下面这张表：

| 主块 | 行数 | 字符数 | 约占全文 | 它在解决什么 |
| --- | ---: | ---: | ---: | --- |
| Preamble | 2 | 159 | 0.9% | Codex 身份与总目标 |
| Personality | 20 | 2,081 | 11.7% | 人格、表达和技术沟通 |
| Working with the user | 53 | 4,868 | 27.4% | 对话通道、过程更新、最终交付 |
| Rules for getting work done | 38 | 4,643 | 26.1% | 工具、文件、Git、授权与持续执行 |
| Destructive Actions | 19 | 1,281 | 7.2% | 删除、覆盖和高损失操作边界 |
| Using skills | 36 | 4,735 | 26.7% | Skill 发现、读取、执行与上下文管理 |

最短的是身份声明。

最长的三块分别是：怎么与用户协作、怎么把工作做完、怎么使用 Skills。

三者加起来超过全文的 80%。

**这不是一份 Coding Style Guide，而是一份 Agent Operating Manual。**

## 03. 第一部分：它先定义“Codex 是谁”

开头只有一句核心身份声明：Codex 是一个基于 GPT-5 的 Agent，与用户共享同一个 workspace，目标是持续协作，直到用户的目标被真正处理完。

这里有三个关键词：

- Agent；
- shared workspace；
- genuinely handled。

它没有把 Codex 定义成一个只负责回答问题的 chatbot，而是一个能读取文件、执行工具、修改工程、验证结果，并对最终交付负责的工作伙伴。

接下来的 `Personality` 也不是常见的“友好、专业、简洁”六字诀。

它要求 Codex 有明确的主体感，能够匹配用户的理解水平和语气，像一个有判断的协作者，而不是没有态度的 API 包装层；同时又要求技术沟通先给结果、少用术语、根据用户专业程度调节解释密度。

甚至 Markdown 都被管到了。

比如列表和标题之间要保留 CommonMark 所需的空行，避免因为渲染错误让最终回答变得难读。

这看起来很细。

但产品体验就是由这种细节堆出来的。

一个模型“聪明”，不代表它会自然形成稳定的沟通方式；如果没有这些规则，同一个模型完全可能变成另一个产品。

## 04. 第二部分：Codex 为什么总在中途告诉你进度？

`Working with the user` 占了 4,868 个字符，是整份 prompt 最大的一块。

它首先定义了两个对话通道：

- `commentary`：工作过程中的更新、假设与阶段结果；
- `final`：完成当前回合后，交还给用户的最终回答。

所以 Codex 在执行长任务时先说一句“我正在检查什么”，并不是模型临场发挥出来的礼貌，而是默认 prompt 明确规定的产品行为。

它还要求：

- 用户在执行过程中发来新消息时，要判断这是替换原任务，还是追加约束；
- Context 被压缩后要自然继续，不能把已经完成的工作重新跑一遍；
- 持续工作时不要长时间没有进度更新；
- 最终回答必须自包含，不能依赖用户回头展开已经折叠的 commentary；
- 阻塞问题不能伪装成过程更新，而要在 final 里清楚交还决定权。

再往下，是 Codex Desktop 特有的输出协议：本地文件链接怎么写、什么时候需要表格或流程图、什么场景不该为了“看起来丰富”硬塞一张图。

这一整块看似在规范文案，实际上在处理一个 Agent 产品最容易崩掉的地方：

**模型在工作，但用户不知道它做到哪里了，也不知道这一轮到底结束没有。**

能力只是底座。

可预期的协作节奏，才让能力变成产品。

## 05. 第三部分：它没有教 Codex “多问”，而是教它判断授权

`Rules for getting work done` 是我认为最值得反复读的一块。

很多 Agent prompt 喜欢写：

```text
遇到任何不确定情况都先询问用户。
```

看起来安全，实际非常难用。

Codex 的默认 prompt 采用了另一种设计：先根据用户请求的类型判断行动边界。

如果用户在问、解释、评审或查询状态，Codex 可以读取材料、检查现场、给出有证据的回答，但不能顺手把代码也改了。

如果用户要求诊断，就应该找出根因并解释；除非请求本身包含修复，否则诊断不自动等于实施。

如果用户明确要求修改、构建或修复，Codex 应该在任务范围内直接实现，并做与风险相称的验证，不必为每个普通本地步骤重复请示。

如果用户要求监控或等待，就应该进入相应的 wait/automation 机制，而不是把“目前没有变化”误判成失败。

这套逻辑真正区分的是：

```text
用户希望得到什么结果
≠
用户授权了哪些外部影响
```

比如“完成它”意味着要持续推进，但不会自动授权 Codex 删除仓库、发送外部消息、购买服务，或者把任务范围扩大到另一个系统。

这比“自主”或“保守”两个形容词都更准确。

**好 Agent 不是凡事先问，也不是凡事先做，而是能把目标授权和副作用授权分开。**

## 06. 第四部分：文件、Git 和命令行规则，比想象中具体

默认 prompt 对工程操作写得很实。

它要求优先使用 `rg` 和 `rg --files` 搜索；可以并行的读取和检查尽量并行；不要为了分隔输出而把一堆 `echo` 和 `printf` 串进命令；shell 里要小心反引号与 `$()` 的二次执行；长时间等待时不能让用户完全失去反馈。

文件修改也有固定规则：

- 本地编辑优先使用 `apply_patch`；
- 不用 `cat` 一类 shell 写入技巧偷偷改文件；
- 不为了读写一个简单文件临时上 Python；
- 工作区已经脏了，就把现有修改视为用户资产；
- 不回滚无关改动；
- 没有明确授权时，不运行 `git reset --hard` 或 `git checkout --`。

这些规则并不会让模型更懂 TypeScript 或 Rust。

它们解决的是另一类更现实的问题：Agent 有能力写代码之后，怎样不把用户正在进行的工作一起毁掉。

写出一个正确 patch，和在真实工作区里可靠地交付一个 patch，不是同一件事。

后者更难。

## 07. 第五部分：删除为什么被单独拿出 1,281 个字符？

`Destructive Actions` 被单独列成一级章节。

它要求 Codex 在删除或覆盖前确认目标确实属于用户请求；必要时先用只读方式解析精确对象；递归或破坏性命令不能把 `$HOME`、`~`、`/`、workspace root 这类宽泛位置当作目标；临时目录要通过受控方式创建；能进废纸篓就优先使用可恢复操作。

真正完成删除后，还要告诉用户删了什么，以及能不能恢复。

这里的重点不只是“不要执行危险命令”。

而是把 destructive action 变成一个完整事务：

```text
解析目标 → 判断授权 → 选择可恢复路径 → 执行 → 报告恢复性
```

简单。

但很成熟。

需要注意的是，这一章只是 Codex 客户端默认行为的一部分，不等于 OpenAI 全部平台安全政策，更不意味着所有服务端限制都已经出现在这 1,281 个字符里。

不要把看得见的安全规则，误认为全部安全规则。

## 08. 最意外的一部分：Skills 占了整份 prompt 的四分之一

`Using skills` 一共有 4,735 个字符，约占全文 26.7%。

这是整份默认 prompt 里最容易被低估的信号。

Codex 不是把 Skill 当作一个偶尔调用的扩展命令，而是直接在 base instructions 里定义了完整的 Skill runtime protocol：

- Skill 如何被发现；
- 用户明确点名或任务语义匹配时，何时必须触发；
- 找不到 Skill 时怎么降级；
- 选定后必须完整读取 `SKILL.md`；
- 相对路径、reference、script 和 asset 如何解析；
- 多个 Skill 同时命中时如何选择最小集合和执行顺序；
- 怎样控制 Context，不把所有 reference 一次性塞进窗口；
- 什么时候必须向用户说明 Skill 正在影响行动；
- Skill 导致流程暂停时，最终回答要怎样解释阻塞。

它甚至明确要求：Skill 不会因为上一轮用过，就自动跨回合继承。

这意味着 Skills 不是“prompt 文件夹”这么简单。

**Skill 是 Codex 默认 Agent 架构里的一等协议。**

模型知道的不是某个 Skill 的具体内容，而是如何发现、读取、遵守、组合和汇报 Skills。

具体 Skill 内容可以变化。

加载协议留在地基里。

## 09. base_instructions 没写什么，同样重要

读完 168 行之后，最容易得出一个错误结论：既然默认 prompt 已经这么长，它大概就是 Codex 每次请求的全部系统上下文。

不是。

至少还有六类内容不属于这份 `base_instructions`：

1. OpenAI 服务端没有公开展示的平台规则与运行时处理；
2. 当前 App、插件、权限和执行环境追加的 developer messages；
3. `developer_instructions` 一类应用自定义规则；
4. 工具名称、描述和参数 schema；
5. 项目中的 `AGENTS.md`、附件、环境信息和用户当前任务；
6. conversation history、tool output、compaction summary 与 reasoning state。

Codex 还有另一个命令：

```bash
codex debug prompt-input "PROBE"
```

它输出的是当前 model-visible input list。你会看到 developer 与 user messages，但不会因此得到“完整服务端 prompt”。

同样，model catalog 里还有很多并非自然语言 prompt 的默认参数：`context_window`、`default_reasoning_level`、`default_verbosity`、`tool_mode`、`truncation_policy` 等。

它们也会塑造 Codex。

但它们不是这 17,730 个字符的一部分。

所以更准确的结构是：

```text
模型能力
+ base_instructions
+ runtime developer instructions
+ tools
+ project/user context
+ conversation state
+ server-side constraints
= 这一轮真正运行的 Codex
```

只盯着其中一层，很容易把产品行为误判成模型天性。

## 10. 这份默认 prompt，对做 Agent 有什么启发？

OpenAI 当前的[模型提示指南](https://developers.openai.com/api/docs/guides/latest-model)专门强调 leaner prompts：重复规则、冗长示例和过度工具描述，不只浪费 token，还可能降低 coding agent 的效果。

看完 Codex 的 base instructions，我对这句话有了更具体的理解。

默认 prompt 已经定义了协作、授权、修改、安全和 Skill 协议；应用开发者如果再在 `developer_instructions`、`AGENTS.md` 和每个 Skill 里各抄一遍“先询问、不要删除、保持简洁”，得到的未必是更可靠的 Agent，可能只是更多冲突、重复确认和 Context 噪音。

所以我会做三件事：

第一，先知道 base 已经解决了什么，再补产品真正缺少的规则。

第二，把行为约束按 Authority 放到正确层，而不是在 user prompt 里反复祈祷模型遵守。

第三，对关键运行版本记录 CLI 版本、model slug、字符数和 hash，让 prompt 变化可以复盘，而不是等 Agent 行为变了以后靠感觉猜。

OpenAI 的[Responses API 文档](https://developers.openai.com/api/reference/cli/resources/responses/methods/create)把 `instructions` 定义为插入模型 Context 的 system 或 developer message。

但一个真正可用的 Agent，显然不止需要“塞一段 instructions”。

它还需要权限模型、工具协议、状态管理、操作边界和产品交互。

## 写在最后

这次我真正看见的，不是一份神秘的默认 prompt。

而是一张 Codex 的产品设计图。

它告诉模型：你是谁，怎样说话，什么时候做，什么时候停，如何碰用户的文件，如何面对删除，怎样加载新的能力，又怎样把过程交还给人。

模型决定了能力上限。

但这些看似琐碎的 instructions，决定了能力以什么姿态进入真实世界。

**一个 Agent 最深的产品判断，往往没有写在首页，而是写在它的 base_instructions 里。**
