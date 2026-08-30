# Skill Group Composition

## Nearby Skills Inspected

- lov-style-clone：从一篇或多篇新样本提取八维文风画像，并可按该画像改写。它是
  可选上游；本 Skill 使用已经校准、版本化的个人画像，不在每次写作时重新分析。
- lov-human-writing：唯一的反 AI 写作规则真源。它在成文前提供作者性账本，并在
  文风稿完成后执行篇章与表层验收；它不拥有个人文风画像。
- lov-anti-wechat-ai-check：已弃用的旧命令兼容入口，只保留未校准的表层模式
  扫描；新任务统一路由到 lov-human-writing。
- lov-wechat-article-branding：为已完成文章添加目录、封面 Prompt、首屏和品牌
  内容。它消费正文，不决定文章观点和文风。
- lov-output-for-article：把最终正文保存为 Markdown、TXT、JSON 或 YAML 文件。
  它负责落盘，不改写内容。
- lov-personal-vocabulary：维护和同步语音输入术语。它可能改善上游素材准确性，
  但不参与成文。

## Atomic Handoffs

1. 可选上游：lov-style-clone 输出一份经用户批准的 UTF-8 Markdown 文风画像。
   上游验收样本覆盖与画像完整性；本 Skill 从版本化画像到正文开始。
2. 必需上游门：lov-human-writing 从事实材料建立作者性账本，本 Skill 以账本为
   事实与作者选择边界。
3. 核心：lov-writing-style 接收账本、事实、笔记、草稿或资料，输出按个人文风
   完成的正文或诊断。它拥有题材、声音、节奏和防戏仿验收。
4. 必需下游门：lov-human-writing 接收文风稿，完成篇章与表层验收。它必须保留
   本 Skill 已验收的事实、作者声音、情绪强度和题材特征。
5. 可选下游：lov-wechat-article-branding 接收已定稿 Markdown，负责视觉与发布
   前包装；lov-output-for-article 只负责文件格式和落盘路径。

## Overlap Decisions

- lov-style-clone 的“按任意画像改写”与本 Skill 的改写模式表面重叠；前者拥有
  新样本分析和临时画像，后者拥有这套版本化个人文风的持续写作与质量门，因此
  保持独立。
- lov-human-writing 是显式必需依赖，不在本 Skill 复制其作者性、因果、反例、
  收束、读者推理空间或表层阈值规则。它不能以降低指标为由抹掉第一人称证据、
  情绪强度或题材特征。
- lov-branding-consistency 只负责最终可见文案的媒介、受众、品牌角色与信息可见性，
  不拥有正文立场、个人文风或反 AI 验收。
- 公众号品牌化、文件输出和发布都发生在正文验收之后，不嵌入本 Skill。
- personal-vocabulary 与成文没有直接验收交接，归类为 not composed。

## Composition Decision

这是 Single Skill，但有两个显式横切依赖：`lov-human-writing` 负责作者性、篇章与
表层门禁，`lov-branding-consistency` 负责最终受众和品牌语境。本 Skill 只拥有个人
文风结果，不复制两者规则，也不把它们包装成新的公开子 Skill。
