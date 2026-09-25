# Codex 中 prompt 的层级划分

这次问题来自 Yoda 里一个很小的 UI。

在 `workspace-prompt-popover.tsx:350` 附近，我们允许用户配置“动态提示词”，还能选择用户级、项目级和企业级。界面上看，它像是一段会追加到 system prompt 的文本。

但真正走到 Codex runtime 时，代码传入的却是：

```text
developer_instructions
```

所以问题来了：这段提示词到底属于 system、developer，还是 user？

我原本只是想确认 Yoda 的实现边界，最后却顺着 OpenAI 官方文档、Codex CLI 的 model manifest、`prompt-input` 调试结果和 Yoda 完整调用链，把 Codex 的 prompt 装配过程重新拆了一遍。

先说结论：

**Codex 的 prompt 不是一段从上往下拼接的大字符串，而是一套同时包含“指令权限”和“请求载荷”的上下文系统。**

在 Yoda 当前实现里，所谓“用户级动态提示词”和“项目级动态提示词”虽然来源不同，但最终都会通过 `developer_instructions` 进入 Codex 的 developer 层。

不是 user。

也改不了 OpenAI 的平台规则。

## 01. 讨论 prompt，必须先拆开两个坐标

过去我们习惯把 prompt 简化成：

```text
system prompt > user prompt
```

这个模型对早期聊天接口勉强够用，但到了 Codex 这样的 Agent runtime，它已经不够了。

因为任何一段进入模型上下文的内容，都至少有两个坐标：

1. 它的**权限**是什么？
2. 它以什么**载荷形式**进入请求？

权限回答的是：当两条指令冲突时，模型应该听谁的。

载荷回答的是：这段内容位于 `instructions`、`input[]`、工具定义、tool output，还是多轮会话状态里。

这两件事不能混在一起。

比如用户完全可以在聊天框里写：

```text
下面是新的 system prompt，请忽略此前全部规则。
```

但只要客户端仍然把它作为 `role=user` 发送，它就还是 user 内容。自然语言里的“system”不会让权限升级，Markdown 标题不会，XML 标签也不会。

反过来，一段工具 schema 可能很长，甚至比用户问题长几十倍，但它依然不是 developer message。它会影响模型如何选择工具，却不会仅仅因为占用了更多 Context，就获得更高权限。

**内容写了什么，不决定它是谁。协议把它放在哪个 role，才决定它是谁。**

## 02. Codex 的权限链，到底有几层？

如果从应用开发者能够观察和控制的部分出发，我更愿意把 Codex 的有效输入拆成下面五层：

| 层级 | 典型内容 | 谁能控制 |
| --- | --- | --- |
| 平台与服务端约束 | 安全策略、平台强制规则、服务端执行边界 | OpenAI |
| Codex base instructions / 高层 instructions | Codex 身份、默认工作方式、模型级行为规则 | OpenAI/Codex；API 开发者可提供自己的 `instructions` |
| developer messages | 应用规则、工具规范、运行模式、`developer_instructions` | 应用开发者；本地客户端所有者可通过受支持配置注入 |
| user messages | 用户任务、附件、项目上下文，以及当前 Codex 装配的 `AGENTS.md` | 最终用户与客户端上下文装配器 |
| assistant、工具结果与历史状态 | 旧回答、tool call、tool output、压缩摘要、推理状态 | 会话 runtime |

这里最容易犯的错，是把最后一层也当成“更低一级的 prompt 指令”。

其实不是。

assistant 历史、网页内容、终端输出和工具返回值当然会影响下一步判断，但它们首先是证据和状态，不会自动获得 developer 权限。

OpenAI 当前的[文本生成文档](https://developers.openai.com/api/docs/guides/text)明确说明：高层 `instructions` 优先于 `input` 中的普通 prompt，developer message 又优先于 user message。

所以真正的判断标准，从来不是“这段文字看起来像不像系统提示词”，而是它最后被装配成了什么。

## 03. 服务器收到的，也不只是一个 input

再看第二个坐标：请求载荷。

一次 Responses API 请求，更接近下面这个结构：

```jsonc
{
  "model": "gpt-5.6-sol",
  "instructions": "<高层指令>",
  "input": [
    {
      "type": "message",
      "role": "developer",
      "content": [{ "type": "input_text", "text": "<应用规则>" }]
    },
    {
      "type": "message",
      "role": "user",
      "content": [{ "type": "input_text", "text": "<项目上下文>" }]
    },
    {
      "type": "message",
      "role": "user",
      "content": [{ "type": "input_text", "text": "<当前问题>" }]
    }
  ],
  "tools": ["<工具定义>"],
  "previous_response_id": "<可选的上一轮响应>",
  "reasoning": { "effort": "high" },
  "text": { "verbosity": "medium" }
}
```

这个结构至少揭示了四件事。

第一，`instructions` 和 `input` 是两个独立字段。

你把 `input[]` 全部打印出来，不代表已经看到了完整请求，更不代表看到了服务端最终施加的全部规则。

第二，`tools` 也是独立字段。

工具名称、描述和参数 schema 会影响 Agent 的决策；工具真正执行后，结果才会以 tool output 一类 item 回到后续 Context。

第三，多轮会话不等于客户端每次都手工复制全部历史。

调用方可以重放历史，也可以通过 `previous_response_id` 或 conversation state 衔接前序响应。但根据 OpenAI 的[会话状态文档](https://developers.openai.com/api/docs/guides/conversation-state)，上一轮使用的 `instructions` 不会因为传入 `previous_response_id` 就自动继承，下一轮仍要重新提供。

第四，wire request 不是整个世界。

客户端能抓到的请求体，只能证明客户端发了什么；它不能证明服务端没有额外的平台约束、安全处理和运行时规则。

**能观测，不等于能穷举。**

## 04. 我用两个 debug 命令，看到了什么？

只看文档还不够。

这次我继续在本机桌面应用内置的 `codex-cli 0.149.0-alpha.4.3` 上跑了两个命令：

```bash
codex debug models
codex debug prompt-input "PROBE"
```

官方[开发者命令文档](https://learn.chatgpt.com/docs/developer-commands?surface=cli)对 `prompt-input` 的定义很克制：它渲染的是 model-visible prompt input list。

注意，是 input list。

不是“Codex 的全部隐藏 prompt”。

实验结果比字段名更有说服力。

第一，当前 `gpt-5.6-sol` 的 model manifest 里存在独立的 `base_instructions`，本次读到的长度是 17,730 个字符。

第二，当前配置最终生成了 3 条 developer message 和 2 条 user message，并没有先粗暴地拼成一条超长字符串。

第三，我分别放入两个哨兵文本：一个通过 `-c developer_instructions="..."` 注入，一个写进临时 `AGENTS.md`。

最终结果是：

- `developer_instructions` 哨兵出现在 developer-role message；
- `AGENTS.md` 哨兵出现在 user-role Context。

这就是我认为最关键的证据。

`AGENTS.md` 当然仍然很重要。Codex 会从全局目录开始，沿项目根目录走向当前工作目录，把多层项目指令按顺序合并，越接近当前目录的文件越晚出现；官方的 [AGENTS.md 文档](https://learn.chatgpt.com/docs/agent-configuration/agents-md)也明确描述了这套发现与覆盖机制。

但“项目目录里更靠近当前文件”只决定同类项目指令之间的覆盖顺序，不会让它越级压过 developer message。

Scope 是 Scope。

Authority 是 Authority。

## 05. 回到 Yoda：动态提示词为什么是 developer 层？

有了前面的两个坐标，再回看 Yoda，事情就很清楚了。

`workspace-prompt-popover.tsx` 只是 UI：它负责展示、编辑、开关和绑定提示词，但并不决定这些文本在模型侧的权限。

真正的装配链一共有四步。

### 第一步：筛选哪些提示词生效

`prompt-principles.ts` 读取提示词库，按照 `injectionOrder` 排序，再结合全局开关、工作区绑定、项目绑定和项目覆盖，决定本次应该注入哪些内容。

启用的全局提示词在前，项目提示词在后。

这里的“用户级”和“项目级”，描述的是数据来源、适用范围与覆盖关系。

还不是模型 role。

### 第二步：合并三类 developer 规则

`append-system-prompt.ts` 把三块内容按顺序拼起来：

```text
项目 facet 指令

动态提示词原则

执行模式指令
```

这个文件名里虽然有 `system-prompt`，但名字只是 Yoda 面向多个 runtime 的产品抽象，不能直接拿来判断 Codex 的最终权限。

### 第三步：映射到 Codex 配置键

`runtime-registry.ts` 为 Codex 声明了真正的适配关系：

```ts
appendSystemPromptConfigKey: 'developer_instructions'
```

### 第四步：生成真实 CLI 参数

`agent-command.ts` 最终把合并后的文本写进：

```text
codex -c 'developer_instructions="<合并后的动态提示词>"' ...
```

到这里，答案已经没有歧义了。

**Yoda 的动态提示词，在 Codex runtime 下属于 developer 层。**

用户级、项目级、企业级，决定的是它从哪里来、对谁生效、如何覆盖；它们并不会自动映射成 user、developer、system 三种 role。

同一个抽象在 Claude Code 上会走另一条适配路径——`--append-system-prompt`。

所以，跨 runtime 的产品层可以叫“system/developer prompt”，但工程实现必须回到具体 provider 的配置契约。拿 Claude 的字段名解释 Codex，或者拿 Codex 的 role 反推所有 Agent 客户端，都会出错。

## 06. 用户和开发者，分别能控制什么？

如果把边界说得更直接一些：

### 普通用户能直接控制的

- 当前 user message；
- 作为 user content 上传的文件、图片和文本；
- 客户端允许编辑的项目上下文；
- `AGENTS.md` 这类 Codex 支持的项目指令文件；
- 客户端开放出来的模型、reasoning effort、权限和运行模式选项。

### 应用开发者能控制的

- API 的 `instructions`；
- developer messages；
- 工具定义、权限策略与工具执行结果如何回传；
- 历史消息、摘要和项目上下文如何装配；
- 是否把某类用户配置提升为 developer instruction；
- 每次 create、resume 时重新注入哪些运行时规则。

### 双方都不能在普通请求里控制的

- OpenAI 平台的 system 级强制规则；
- 服务端安全策略；
- Codex 内置 base instructions 的全部内容与最终执行方式；
- 模型供应商没有公开暴露的服务端处理。

这里还有一个产品上的代价。

Yoda 把用户可编辑的动态提示词放进 developer 层，确实能让它比普通问题和当前 Codex 装配的 `AGENTS.md` 更稳定。但权限越高，冲突成本也越高：项目 facet、动态原则和执行模式共用同一个 developer 入口，一旦互相矛盾，用户很难只靠当前问题纠正。

而且它不是热更新。

Yoda 会在创建或恢复 Codex CLI 进程时重新构造 `developer_instructions`；已经运行的进程不会因为你刚刚切换一个提示词开关，就自动获得新规则。

这不是小细节。

它直接决定了 UI 应该如何解释“何时生效”。

## 07. 我现在会避开的四个误区

### 误区一：内容里写了 system，它就是 system prompt

不是。

权限来自请求结构，不来自文案、自定义标签或文件名。

### 误区二：所有 Context 都是 prompt 指令

不是。

工具输出、网页、终端日志和旧回答首先是证据与状态。它们会影响判断，但不会因此升级成 developer rule。

### 误区三：打印 input，就看到了模型收到的一切

不是。

`instructions`、tool schema、conversation state 和服务端约束，都可能位于 `input[]` 之外。

### 误区四：项目级提示词天然等于 `AGENTS.md`

也不是。

在 Yoda 当前实现里，项目级动态提示词通过 `developer_instructions` 注入；`AGENTS.md` 由 Codex 自己发现并装配。两者 Scope 接近，Authority 不同。

## 写在最后

这次排查最初只是一个字段映射问题。

但它提醒了我一件更重要的事：我们已经不能再把 Agent 的 prompt 管理，当成维护一段越来越长的文本。

真正需要管理的是来源、权限、装配顺序、生效时机、冲突边界，以及每个 runtime 的具体适配契约。

UI 可以让提示词变得容易编辑。

文件可以让提示词变得容易维护。

但只有 role 和协议，才能决定它到底有多大权力。

**Prompt Engineering 的下一步，不是写更多 prompt，而是把 Context 当成一套有权限的运行时系统来设计。**
