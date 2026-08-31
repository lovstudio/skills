---
name: lov-repost-wechat-article
description: >
  定位并完整保留合作方微信公众号原文，在明确来源、禁止原创声明和隔离私密语境的前提下加入发布方开场、判断与品牌收尾，生成并远端核验转载草稿。Use for“转发这篇推文”“转载合作方文章”或“repost this WeChat article”。
license: MIT
compatibility: "Python 3.9+ and beautifulsoup4；远端草稿交付需要 lov-publish-wechat-article；无显式 URL 时可选用 lov-wdb-cli 定位来源。"
depends_on:
  - lov-branding-consistency
  - lov-publish-wechat-article
metadata:
  author: lovstudio
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: authored-prose
  tags:
    - wechat-official-account
    - repost
    - source-fidelity
    - draft-verification
---

# 转发微信公众号文章

把合作方或外部公众号文章转换成一份“原文主体可核验、发布方增量清楚、来源与权利关系诚实”的转载稿；默认止于远端草稿，不把转载写成原创，也不把内部沟通直接公开。

## Triggers

### Activate when

- “转发一下合作方这篇推文，尽量保持原汁原味。”
- “把这篇公众号文章转载到我们的账号，加一段自己的开场和收尾。”
- “从微信记录里找到对方刚发的文章，整理成转载草稿。”
- “Repost this WeChat article with our own short introduction.”

### Do not activate when

- 用户只要把自己的 Markdown 同步到公众号；直接使用 `lov-publish-wechat-article`。
- 用户只要读取或修改已经存在的公众号草稿；使用 `lov-wechat-article-operator`。
- 用户要重写、评论或二次创作一篇文章，而不要求保留原文主体；使用文章写作或品牌化能力。
- 用户只要转发到微信聊天、群聊或朋友圈，而不是公众号文章草稿。

## User Profile

每次运行读取 `skill.yaml` 声明的 `user-profile/v1`，按当前请求、项目上下文、Skill 记录、共享 Preferences、品牌 Profile、安全默认值的顺序解析发布主体、品牌名称、官网、语气和工作目录。用户明确说“以后转载都……”时，才通过 `scripts/profile_store.py` 将该偏好写入 `skills.lov-repost-wechat-article.records`；推断值、微信凭据和私人聊天内容不得持久化。

## Required References

执行前按任务边界完整读取：

- [Skill 组合](references/skill-composition.md)：决定是否调用 WDB、品牌化、Operator 或发布器。
- [来源与保真](references/source-fidelity.md)：建立来源快照、正文冻结区和图像账本。
- [编辑增量](references/editorial-overlay.md)：加入发布方开场、判断、收尾和品牌区。
- [发布交接](references/publication-handoff.md)：把转载包交给发布器并回读远端。
- [作者性边界](references/authorship-integrity.md)：只约束新增原创段落，不改写冻结原文。

## Output Contract

一次完整运行产生可回读的转载包：

```text
repost-project/
├── source-page.html
├── source-content.html
├── source-text.txt
├── source-meta.json
├── source-assets/
├── article.md
├── edition-manifest.json
├── article.lovpen.wechat.html
├── cover/cover-composition.json
└── publication-receipt.json
```

`edition-manifest.json` 至少记录 `sourceUrl`、`sourceAccount`、`sourceVisibleTextSha256`、`sourceImageCount`、`copyrightMode: reprint`、新增区块、私密上下文排除项和当前状态。

## Workflow

### 1. 解释动作与授权

- “转发、转载、同步到公众号”默认目标是 `draft_created`；只有“正式发布、公开发表、立即发出”等明确指令才授权继续公开发布。
- 转载一律使用 `copyrightMode: reprint`。不得勾选原创，不得把合作关系推断成版权转让。
- 用户只想先看效果时止于本地 `prepared`，不得写入公众号。

### 2. 定位真实来源

1. 优先使用用户给出的公开微信文章 URL。
2. 只有标题、合作方或聊天语境时，可调用 `lov-wdb-cli` 做窄范围只读搜索；保留数据库、表和 rowid 作为内部稳定身份，但不得把这些路径、聊天正文或联系人标识写进公开文章。
3. 从命中的分享消息取得真实 URL，再读取公开文章；不要猜 URL、标题、账号或发布时间。
4. 记录转载邀请、允许范围与权利边界。缺少授权不等于可以声明原创。

### 3. 冻结原文

按 [来源与保真](references/source-fidelity.md) 保存来源页面、可见正文、原图和散列。只允许删除不参与可见内容的运行态节点、隐藏 SVG 动画或平台占位节点；清理前后可见文字和图片账本必须一致。

原文主体放入唯一节点：

```html
<section data-repost-source="true" data-source-account="SOURCE_ACCOUNT">
  <!-- source-faithful HTML -->
</section>
```

冻结区内不得润色、删段、改标题、替换观点或插入发布方评论。为平台兼容做结构净化时，必须用文字散列与图片数证明内容未变。

### 4. 区分公开事实与内部语境

建立四栏内部账本：`sourceTruth`、`publishableContext`、`privateContext`、`evidenceGap`。只有前两栏能进入成品；联系人身份、内部提案、未官宣议题和协商细节默认留在本地。

### 5. 加入发布方增量

按 [编辑增量](references/editorial-overlay.md) 在冻结区外加入最小必要内容：

```text
opening-hero -> publisher-intro -> source-attribution -> source-body
-> publisher-outro -> brand-endcap
```

- 开场回答“为什么此刻值得转发”，不复述摘要。
- 发布方判断应来自明确事实或用户立场，不编造亲历、合作承诺、主办方背书或未来结果。
- 收尾短于原文主体，不把合作方文章改写成发布方广告。
- 稳定品牌尾注读取 Profile；产品只有与原文直接相关或用户明确要求时才出现。
- 标题与作者字段符合转载身份。默认保留来源账号为作者，并在正文原位显示完整来源 URL。

### 6. 处理图像与封面

- 保留原图内容、顺序和来源，不让生成模型重绘合作方 Logo、海报或嘉宾照片。
- 可从权利清楚的原图确定性裁切正文首图或分享封面底图；官方发布方 Logo 必须后置合成。
- 正文首图与分享封面是独立资产。正文首图默认 `4:3`，分享封面由品牌封面合成能力生成并出具收据。
- 原图已有图注时不重复添加 Caption；只有证据、归属或解释确有必要时才装饰派生图。

### 7. 本地审计

```bash
python3 "$SKILL_DIR/scripts/audit_repost.py" \
  --source-text SOURCE_TEXT.txt \
  --edition-html ARTICLE_HTML \
  --source-account "SOURCE_ACCOUNT" \
  --source-url "SOURCE_URL" \
  --required-block '[data-repost-block="publisher-intro"]' \
  --required-block '[data-repost-block="source-attribution"]' \
  --required-block '[data-repost-block="publisher-outro"]' \
  --receipt REPOST_AUDIT.json
```

审计必须证明冻结原文可见文字一致、来源块唯一、来源 URL 可见、所有增量区块各一次、图片数符合账本、版权模式为转载。失败时先修正文，不进入 Lovpen 或远端草稿。

### 8. 交给公众号发布器

调用 `lov-publish-wechat-article`，让其依次消费 canonical Markdown、必要 Caption 收据、Lovpen 微信复制态 HTML、品牌封面及 `cover-composition.json`。本 Skill 不复制图片上传、网关、密钥、草稿创建或正式发布实现。

传给发布器时：

- `source-url` 使用真实原文 URL；
- 作者、摘要与推荐语必须回读一致；
- 不请求原创字段；
- 正常转载止于 `draft_created`；
- 远端 `draft/get` 后再次用 `audit_repost.py --remote-html` 核对冻结原文、图片和增量区块。

### 9. 防止重复草稿

若 `draft/add` 已取得 `mediaId`，但后续保真审计失败：立即保存 `mediaId`、远端正文和阶段，不得在不知道旧草稿身份时再次调用 `draft/add`。先诊断微信实际清洗的标签或样式；只有旧草稿可精确更新/删除，或用户确认接受新建时，才创建替代草稿。

### 10. 报告真实状态

- `prepared`：本地转载包和预检通过，未写入微信。
- `draft_created`：远端草稿、封面、图片、来源块和增量块已回读。
- `published`：仅在用户明确授权后提交，且平台回读到公开文章标识或 URL。

报告原文来源、保留范围、新增内容、权利模式、远端状态和任何重复草稿风险；不得用“已转发”掩盖草稿与公开发布的区别。

## Validation

```bash
python3 scripts/validate_skill.py .
python3 scripts/audit_repost.py --help
```

完成前还需验证至少一个中文激活句命中，一个“普通原创文章发布”非触发句不命中，并回读 `cases/cases.json` 中的真实案例证据。

## Dependencies

- 必需：`lov-branding-consistency`、`lov-publish-wechat-article`。
- 可选上游：`lov-wdb-cli`（缺少 URL 时定位微信分享消息）。
- Python 3.9+、beautifulsoup4。

