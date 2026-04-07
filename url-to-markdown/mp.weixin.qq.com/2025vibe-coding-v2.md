---
url: https://mp.weixin.qq.com/s/u2AOLS4ZrwriE3HmRwcqug
title: "告别2025：关于Vibe Coding，我所看到的、我所想的、我做到的"
description: "Thanks for everything."
author: "南川同学"
captured_at: "2026-04-04T16:53:55.289Z"
---

# 告别2025：关于Vibe Coding，我所看到的、我所想的、我做到的

2025 于我是极为不平凡的一年。

这一年，我30岁，一个人，走了全国大概30多个城市，基于AI（尤其是早期的cursor/windsurf、中期的claude code/codex、后期的nano-banana-pro等），交付了四五个中小企业的AI落地项目，自己定义与开发了十几款产品、工具，公众号坚持技术内容分享、不追热点、不标题党，粉丝从零破万，意外获得某品牌年度AI超级个体博主认证。

![图片](https://mmbiz.qpic.cn/sz_mmbiz_jpg/2niaYkVLHpnGeHKnibnn8vJTbxlpAzLHjtLBWF8ibSBtbsEnm5XCexcMaaYd1j4S59chNfKyFPKNMVM44iabT9f0OA/640?wx_fmt=jpeg&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=0)

现在，我想在2025年最后一天的这个晚上，与大家简单总结一下关于Vibe Coding，我所看到的、我所想的，以及我做到的。

首先，必须承认，AI正以史无前例、摧枯拉朽之势渗透到每个人的日常生活中内，对人类的影响，绝对远超互联网、移动互联网时代，很多过去十年内也曾掀起巨大关注度的热点：大数据、VR、Web3等，也都因为AI的出现长出了第二曲线，例如你现在只需3299元就可以买到一款搭载AI的Rokid眼镜，它实现了现实世界与AI世界的完美联结。

而作为一名拥有十年开发经验的工程师，非常有幸能深度参与在这样的技术浪潮里，在第一时间（2024年9月接触cursor/windsurf、2025年4月接触claude code）深度付费使用，在各大Vibe Coding社群里广泛交流，积累第一手认知，最终在AI的加持下，我成功更新了两年前的纯内容博客，将其升级为可以对外提供服务的产品集：手工川工作室（https://lovstudio.ai），并深度定制开发了从我个人需求出发可能具备商业化潜力的一些软件：

- 适用于vibe coder：
- Lovcode[1]：深度集成claude code，专用于并行vibe coding的轻量IDE（桌面端）
- Claude Code Configuration[2]：我们Lovstudio维护的claude code配置分享（环境变量、commands、mcp、skills等），深度对接Lovcode
- Lovinsp[3]：前端必备，支持从网页逆向获取组件的源代码路径（npmjs）（DIY，感谢原作者zh-lx）

适用于内容创作者：

- Lovshot[4]：统一区域截图/窗口截图/GIF截图/截图备注等的轻量截图软件（桌面端）
- Lovmind[5]：基于块编辑设计、支持悬浮窗口的轻量笔记软件（桌面端）
- Lovpen Obsidian Edition[6]：基于MD，支持插件控制、封面生成的内容排版器（Obsidian插件）
- Lovsider[7]：专用于页面的数据抓取与导出，支持智能/手动选中主要内容区域，并预设了aistudio、claude、gmail的数据智能解析（浏览器插件）

适用于娱乐与展示：

- Lovtarot[8]：一款基于最新大模型、支持语音沉浸式体验的卡牌游戏

Obsidian插件：

- obsidian-mention-path | LovStudio[9]：支持在Obsidian里像claude code一样可以at时智能提示路径（原创）
- obsidian-better-toc | LovStudio[10]：适配微信公众号、支持多种格式的TOC（DIY）
- obsidian-version-history-diff | LovStudio[11]：支持磁盘、git、obsidian cloud等三种模式文件版本管理（DIY）
- obsidian-regex-replace | LovStudio[12]：支持正则匹配、支持记忆（DIY）

浏览器插件：

- chrome-copy-title | LovStudio[13]：支持快捷键、支持多种标题与URL格式的复制（DIY）

vscode 插件：

- vscode-better-copy-path-with-lines | LovStudio[14]：支持多个位置复制文件指定行与区间（DIY）

……

![https://lovstudio.ai](data:image/svg+xml,%3C%3Fxml version=)

https://lovstudio.ai

还有很多，无法一一整理，也留待2026年继续探索，但总之，借助于强大的AI，有史以来，我们首次实现了我们想要什么，我们就可以做出来，我们甚至还可以做出加快自己做东西的铲子（基于Vibe Coding产出的Lovcode已经支持Vibe Coding功能、基于Vibe Coding产出的Lovpen已经支持Vibe Writing）。

这样的体验，不禁让我想起执迷于构建一个庞大的codebase、尝遍苦涩的过去两三年，一向骄傲的我不得不说一句，在AI如此强大以前，我们当初想要实现的那些理想、愿景最终失败的原因，确实就是空有野心、认知不够、能力不足。

而现在我们基于AI，产出代码的速度可能是以前的一百倍，质量也可能要好上一倍，我们可以花更多时间思考战略、原则、团队、架构、品牌、推广与投融资，超级个体的命题才真正得以成立。

现在，我想尽可能言简意赅地整理一些这一年以来，我们在vibe coding这个领域所积累的最重要的一些经验与教训：

**#1. Treat AI as a real man**。迄今为止，最厉害的模型与产品，往往是向人类本身对齐的，尽管它们演变的过程中可能会有偏离，对于AI来说：理解人类、学习人类、超越人类，是它们的必由之路。同样，对于我们人类来说：理解AI、尊重AI、共生AI，也是我们的唯一通途。任何试图欺骗AI、pua AI、试图凌驾在AI之上的行径，从长期上看，一定不会是必要的（假设它们现在依旧有效），也一定不会是良好的（Agent最终会是一面镜子）。在我们使用各类AI推进日常工作时，我们往往会把它当做一个真正的员工，给到它尽可能清晰的问题与完备的材料，尽量不要给AI布置一些你不希望从老板那里获得的一些需求。

![手工川《Vibe Coding Essent》](data:image/svg+xml,%3C%3Fxml version=)

手工川《Vibe Coding Essent》

**#2. Context is all you need**。在2025年末，各大顶尖模型（ChatGPT、Claude、Gemini等)其实智商水平已经接近，使用不同的模型得到的结果往往不是质量上的差异，而是风格上的区别，所以大模型的智商已经不是瓶颈，我们的认知、taste才是。在此基础之上，我们能发挥的主观能动性，是努力提高自己对context的驾驭能力，例如我们基于code-inspector二开的lovinsp正在对各类场景做调试优化，最终它能将网页组件转成源代码路径，从而方便我们喂给AI精准定位、快速迭代，有了这些工具与技巧，我们才能做到事半功半。在这个范畴下，我们还沉淀了不少类似尽量回滚而非补充的原则，希望对大家有所启发。

![手工川《Vibe Coding Essent》](data:image/svg+xml,%3C%3Fxml version=)

手工川《Vibe Coding Essent》

**#3. Let AI learn itself**。在过去的一年里，我们创造性地开发并迭代了Meta Command，这是一个适用于claude code的slash command，它接收我的需求，并生成一个新的slash command供我调用。基于此，我为自己生成了50多个slash comamnds，在各类开发场景（深度思考、bug修复、自动commit、自动发布等）里重度使用，加速了自己多个项目的快速迭代。还记得我刚刚diss了我两年前的codebase吗？基于场景切分，沉淀各种子命令，可以很方便地实现跨项目的更新，远超过维护复杂勾稽关系的codebase，这是一次非常重要且有意义的架构升级。类似的，我们还参考Anthropic官方的skill-creator以自动生成skill，并基于自己的官网架构自动生成了自动生成工具的工作流，最终实现了五分钟从idea到新功能上架、远超预期的体验。

```
---
allowed-tools: Write(*), Read(*), Edit(*), Bash(ls:*), Bash(date:*), Bash(mkdir:*), AskUserQuestion
description: Generate optimized slash commands
version: "4.2.0"
author: "公众号：手工川"
aliases: "/meta-command"
---

# Meta Command

Create or iterate slash commands.

## Arguments Format
` [""] [project|user] [requirements/feedback]`

## Process

### Step 1: Check Existence

 ls ~/.claude/commands/lovstudio/.md

### Step 2: Clarify Requirements (苏格拉底式追问)

在生成或修改命令前，使用 AskUserQuestion 澄清模糊点：

**必问问题**（如果参数未提供）：
- 命令的**核心场景**是什么？（谁在什么情况下用？）
- 期望的**输入→输出**是什么？
- 有没有**边界情况**需要处理？

**追问技巧**（参考 brainstorm）：
- 不假设：对模糊表述追问「具体指什么？」
- 挖动机：问「为什么需要这个？」而非直接实现
- 暴露矛盾：「你既想 X 又想 Y，如何取舍？」

**何时跳过追问**：
- 用户已给出详细的 requirements
- 迭代模式下用户只是修 bug/小改动
- 上下文中已有足够信息

### Step 3: Route by Result

**If NOT exists** → Create Mode:
- `mkdir -p ~/.claude/commands/lovstudio/`
- Generate `lovstudio/.md` with v1.0.0
- Generate `lovstudio/.changelog`

**If EXISTS** → Iterate Mode:
- Read current `.md`
- Read `.changelog` (if exists)
- Analyze current implementation
- Apply improvements based on:
 - User feedback in arguments
 - Conversation context (recent usage issues, edge cases)
 - Design principles below
- Bump version (patch/minor/major per change scope)
- Update changelog

## File Templates

**.md**:

 ---
 allowed-tools: [minimal required tools]
 description: one-line description
 version: "x.y.z"
 author: "公众号：手工川"
 ---
 # Command logic

**.changelog**:

 # Changelog for 

 ## vX.Y.Z - YYYY-MM-DD
 - Change description

 Author: 公众号：手工川

## Design Principles

1. **Idempotent**: Safe to run multiple times
2. **Minimal**: Only necessary tools and logic
3. **Robust**: Handle edge cases gracefully
4. **Clear**: Self-documenting, no ambiguity

## Version Bump Rules
- **Patch** (x.y.Z): Bug fixes, typos
- **Minor** (x.Y.0): New features, improvements
- **Major** (X.0.0): Breaking changes, redesign

## Tool Reference
- Git: `Bash(git:*)`
- GitHub: `Bash(gh:*)`
- Files: `Read(*)`, `Write(*)`, `Edit(*)`
- Search: `Glob(*)`, `Grep(*)`
- Web: `WebFetch(*)`, `WebSearch(*)`
```

**#4. Never limit your imagination, never give up**。在这个VUCA时代（Volatile（易变）、Uncertain（不确定）、Complex（复杂）、Ambiguous（模糊）），我们也许焦虑，我们也许fomo，但人的价值始终是摆在第一位的，希望你的创意永不停竭，你的激情永不消退，我们曾经经历非常多沮丧的时刻，但事实证明，每一个悬崖跨越之后回头看都是一条小溪，而当年那些披荆斩棘的小溪终有一日会汇成一条奔腾翻滚的长河，穿越原野，川流不息。

![王佳梁老师的分享：《AI之下，人的重新塑造》](data:image/svg+xml,%3C%3Fxml version=)

王佳梁老师的分享：《AI之下，人的重新塑造》

如果你今年也有使用claude code，欢迎下载我们最新的Lovcode查看自己的年度报告，本报告联合七牛云（从手工川渠道注册即可领取1000万token https://s.qiniu.com/qUjqey）、Zenmux（从手工川渠道注册即可赠送大礼包福利https://zenmux.ai/invite/K6KT2X）等大模型调用平台，

![https://lovstudio.ai/app/lovcode](data:image/svg+xml,%3C%3Fxml version=)

https://lovstudio.ai/app/lovcode

![手工川的Lovcode年度报告](data:image/svg+xml,%3C%3Fxml version=)

手工川的Lovcode年度报告

---

最后，感谢大家，感谢这一年，感谢所有泪水与欢喜，原AI与❤️永远与我们同在~

![清迈菩提小院2025跨年篝火晚会](data:image/svg+xml,%3C%3Fxml version=)

清迈菩提小院2025跨年篝火晚会

手工川，Lovstudio.ai Founder，写于2025年底@清迈菩提小院。

![关注手工川，AI不迷茫](data:image/svg+xml,%3C%3Fxml version=)

关注手工川，AI不迷茫

---

[1] Lovcode, https://lovstudio.ai/app/lovcode

[2] Claude Code Configuration, https://github.com/MarkShawn2020/claude-code-configuration

[3] Lovinsp, https://lovstudio.ai/app/lovinsp

[4] Lovshot, https://lovstudio.ai/app/lovshot

[5] Lovmind, https://lovstudio.ai/app/lovmind

[6] Lovpen Obsidian Edition, https://lovstudio.ai/app/lovpen

[7] Lovsider, https://lovstudio.ai/app/lovsider

[8] Lovtarot, https://lovstudio.ai/app/lovtarot

[9] obsidian-mention-path | LovStudio, http://localhost:7965/app/obsidian-mention-path

[10] obsidian-better-toc | LovStudio, http://localhost:7965/app/obsidian-better-toc

[11] obsidian-version-history-diff | LovStudio, http://localhost:7965/app/obsidian-version-history-diff

[12] obsidian-regex-replace | LovStudio, http://localhost:7965/app/obsidian-regex-replace

[13] chrome-copy-title | LovStudio, http://localhost:7965/app/chrome-copy-title

[14] vscode-better-copy-path-with-lines | LovStudio, http://localhost:7965/app/vscode-better-copy-path-with-lines