---
name: lov-publish-wechat-article
description: 统一读取、局部编辑、创建、核验并发布微信公众号草稿；已有草稿坚持先读后写、最小修改和保存重载，新草稿强制消费品牌封面与微信复制态 HTML。Use when asked to read, edit, sync, draft, verify, or publish a WeChat article.
license: MIT
compatibility: Python 3.10+；图片 Caption 准备需要 lov-image-decorator 与 Pillow 9+；网关发布需要 beautifulsoup4 与 lov-env-management；常规草稿创建需要品牌封面收据与支持 `render --format wechat` 的 lovpen-cli；网页私有 API 补全需要 websockets 与已授权的 Chrome CDP 会话。
depends_on:
  - lov-wechat-branding-cover-composition
  - lov-image-decorator
  - lovpen-cli
  - lov-env-management
  - lov-branding-consistency
metadata:
  author: lovstudio
  version: "0.8.0"
  tags:
    - wechat-official-account
    - article-publishing
    - lovpen
    - draft-verification
---

# 发布微信公众号文章

把“准备内容”“写入远端草稿”“提交发布”“平台发布完成”建模为不同状态。所有微信公众号 API 请求默认经 `api.lovstudio.ai` 的统一网关发出，由后端固定出口与微信通信；本机无需进入微信 IP 白名单。

## Triggers

### Activate when

- 用户要求把 Markdown、HTML 或纯文本导入、同步或保存到微信公众号草稿箱。
- 用户要求为公众号草稿设置原创声明、推荐语、作者、阅读原文或品牌封面，并核验保存结果。
- 用户要求提交已有 `media_id` 正式发布，或查询既有 `publish_id` 的发布状态。
- 用户要求读取当前草稿、替换封面、插入或修改明确区块，并确认保存结果。
- English triggers include “Publish this article to WeChat”, “Save this as a WeChat Official Account draft”, “Read this existing draft”, and “Verify that this edit persisted”.

### Do not activate when

- 用户只要求设计封面、正文首图或统一品牌组件；使用对应的文章品牌或封面 Skill。
- 用户只要求生成本地文章内容，不要求写入微信公众号；使用文章创作或排版 Skill。
- 用户只要求分析本地 Markdown、但不读取公众号远端状态；使用文章创作或审计能力。

## 输入契约

收集并确认：

- 正文：一个 Markdown、HTML 或纯文本文件。用户只在会话中给出正文时，先保存为本次任务的临时 `.md` 或 `.txt` 文件。常规草稿创建必须先调用 `lovpen-cli`，并接收它通过 `--format wechat` 写出的微信复制态 HTML；不要接收 `--format standalone` 产物后再重建版式。`compact-markdown` 只保留给显式诊断旧链路。
- 内容质量交接：发布器消费已经完成内容校对的 canonical Markdown，不负责把论文式章节改成网感标题。文章含调研、评测、benchmark、排名、总分或雷达图时，预检必须看到位于结果之前的“测试方法”“Prompt”“评价指标”“评分方法”“评分示例”“复现方法”，并在结果之后看到“局限性”；`Prompt` 章节至少公开一份实际执行文本。缺失时在任何远端写入前失败关闭。
- 正文首图：常规发布的 Markdown 第一块内容必须是独立的 `4:3` 横向首图，位于导语之前，并与分享封面是两个不同文件。`3:4` 竖图、缺图、远程占位图或直接复用分享封面成品均不得通过预检。
- 正文图片 Caption：在 Lovpen 渲染前逐图判断读者是否需要补充证据、归属或解释。需要 Caption 的图片必须调用 `lov-image-decorator`，使用显式 Caption 生成不覆盖原图的派生文件与 JSON 收据，再把文章副本的图片引用改为派生文件；不需要 Caption 的图片保持原样，不使用 `Powered by ...` fallback 填充。
- 出版组件：每次读取当前公众号品牌 Profile。永久 `blocks.endcap` 必须包含已批准简介、链接与启用的个人卡片；`blocks.campaigns` 中仍开放、未满员且未过期的活动必须位于 endcap 之前。详细状态与字段见 [Profile 驱动的出版组件](references/editorial-components.md)。
- 标题：显式标题优先；Markdown 可从首个一级标题推断。最终不超过 32 字。
- 封面：常规草稿创建必须先调用 `lov-wechat-branding-cover-composition`，上传其 `cover-composition.json` 中 `shareCoverUpload` 指向的 JPG，并同时传入这份收据。发布器会核对 schema、官方 Logo SHA-256、`publisherLogoPresent` 与上传件路径；不得把无 Logo 艺术底图、旧封面或其他产品资产当成上传件。
- 原创声明：对当前发布账号自主创作的新文章默认为 `true`；有转载、编译、合作作者或权利不清时不得猜测勾选。
- 文章推荐语：默认写一句 8–24 个中文字符的简短推荐语，先给读者一个记忆点；不重复标题，不写“本文将”，不拿摘要充当推荐语。
- 其他可选字段：作者（16 字内）、摘要（120 字内）、阅读原文 URL、评论设置。用户说“其他默认”时，保留平台当前默认，不主动翻转未指定开关。
- 目标账号与动作：仅存草稿、立即公开发布，或查询既有 `publish_id`。

只把面向读者的正文交给平台。补充背景、人物关系、顾虑和其他 `privateContext` 留在本地。

先运行预检：

```bash
python3 <skill-dir>/scripts/preflight_article.py ARTICLE \
  --cover COVER \
  --cover-composition-receipt COVER_DIR/cover-composition.json \
  --lovpen-wechat-html ARTICLE.lovpen.wechat.html \
  --brand-profile BRAND_PROFILE \
  --title "TITLE" \
  --transport gateway \
  --json
```

`--allow-unverified-body-hero` 只用于显式诊断旧链路，不得用于正常交付。

省略可选参数时不要传空字符串。脚本退出非零时先修复 `errors`；`warnings` 需要在选择 transport 时处理。正文含本地或远程图片时，读取 [references/transport-routing.md](references/transport-routing.md)。

## 状态语义

始终使用以下状态，不用“发布”一词模糊带过：

```text
prepared
  -> draft_reading -> draft_read
  -> draft_editing -> draft_saved
  -> draft_creating
  -> draft_created
  -> draft_enriching
  -> draft_ready
  -> publish_submitted
  -> publishing
  -> published | publish_failed
```

- `draft_read`：已有草稿已取得可比快照，没有执行写入。
- `draft_saved`：已有草稿的授权修改已保存、重载，且 before/after 差异验证通过。
- `draft_created`：`draft/add` 已返回 `media_id`；文章仍在公众号草稿箱。
- `draft_enriching`：正在通过已登录编辑器的网页私有 API 保存并回读公开 OpenAPI 未覆盖的原创声明，或补齐其他显式字段。
- `draft_ready`：草稿已保存并重载，原创声明、推荐语、最终封面与其他用户指定字段均已回读。
- `publish_submitted`：`freepublish/submit` 已返回 `publish_id`；任务刚被接受。
- `publishing`：`freepublish/get` 返回状态 1、状态 0 但尚无文章标识，或等待窗口结束时任务仍在进行。
- `published`：状态查询返回 0，并回读到 `article_id` 或文章 URL。
- `publish_failed`：状态查询返回 2、3、4、5 或 6；保留状态码、失败文章编号与官方详情。

完整收据字段见 [references/result-contract.md](references/result-contract.md)。

## 工作流

### 1. 识别用户意图

- “同步、导入、存到草稿箱、生成草稿”止于 `draft_created`。
- “正式发布、公开发布、立即发表”继续提交并轮询到终态。
- 用户只给 `publish_id` 时直接查询状态，不重建草稿。
- 用户要求读取或修改当前已有文章时，使用本 Skill 的 `existing-draft` 流程；不重建文章包，也不创建重复草稿。
- 创建新草稿时先读取品牌 Profile，把永久 endcap 与当前生效活动写入 canonical Markdown；再调用 `lov-wechat-branding-cover-composition` 生成最终封面和收据，按 [图片 Caption 准备契约](references/image-caption-preparation.md) 调用 `lov-image-decorator` 处理需要说明的正文图片；最后调用 `lovpen-cli` 生成微信复制态 HTML，然后回到本流程。Caption 装饰只作用于明确需要说明的图片，不把所有图片机械套入统一底栏。

### 2. 读取或局部编辑已有草稿

完整读取 [已有草稿操作](references/existing-draft-operations.md) 与 [文章状态契约](references/article-state-contract.md)：

1. 用 `media_id`、`appmsgid` 或当前编辑页唯一定位目标，读取 before snapshot。
2. 读取任务止于 `draft_read`，不得因为“检查一下”执行保存。
3. 修改任务先声明允许变化与必须保持不变的字段，再执行最小修改。
4. 保存并重新加载同一草稿，记录 after snapshot。
5. 用 `scripts/verify_article_state.py` 验证差异；只有通过后报告 `draft_saved`。

已有草稿若需整体重写或品牌化，先由 `lov-article-creator` 生成本地 `prepared` 版本，再回到本流程执行明确替换。删除、覆盖整篇或改变权限仍需精确目标与明确授权。

### 3. 选择草稿 transport

按以下顺序选择，详细契约见 [references/transport-routing.md](references/transport-routing.md)：

1. 默认使用 LovStudio 统一网关：正文图片、封面、草稿创建、草稿回读、正式发布与状态查询均由后端调用微信。
2. 需要声明原创时，使用已登录编辑器会话调用 `mp.weixin.qq.com/cgi-bin/operate_appmsg`；需要可见排版或处理其他字段时，使用已登录浏览器。
3. 只有显式诊断旧链路时才使用 OneShot 直连或其他 direct transport；不得把它作为默认发布路径。

AppSecret 与网关 API Key 必须由 `lov-env-management` 的 locator 解析。不要把密钥复制到文章目录、命令参数、环境文件、日志、截图或收据。

### 4. 创建并核验草稿

统一网关路径：

1. 先核对 canonical Markdown 的内容交接：研究评测类方法链完整，正文第一块是独立的 `4:3` 横向首图；再用 `--brand-profile` 核对永久 endcap、个人卡片，以及仍开放且未满员的活动。任一项缺失、重复或错位时在远端写入前失败关闭。
2. 核对 Caption 准备结果：所有被选中图片都有 `lov-image-decorator` 收据，文章引用的是派生文件，未选中图片未被改写，Caption 没有与相邻正文或图注重复。
3. 用 `preflight_article.py --transport gateway` 核对标题、正文、Lovpen 微信复制态 HTML、品牌封面合成收据、图片和扩展字段。
4. 用 `publish_via_gateway.py` 传入 AppID、品牌 Profile 与两个受管密钥 locator；不要传密钥明文。
5. 脚本逐张经 `material/uploadimg` 上传正文图片，再调用 `draft/add`。
6. 脚本按渲染后的可见正文检查 20,000 字符，并按 UTF-8 HTML 检查 1,000,000 字节；不得把原始 HTML 字符数当作 20,000 字符限制。
7. 脚本立即调用 `draft/get`，核对远端标题、图片数、封面素材与正文长度。Lovpen 路径还要逐节点比较远端正文：允许微信移除外链 `<a>` 包装和 `position` 属性，但其余标签顺序、class、CSS 属性与可见文字必须保留。
8. 只有回读通过后才记录 `mediaId`，状态写为 `draft_created`。

先通过 `lovpen-cli` 的真实微信复制链渲染：

```bash
python3 <lovpen-skill-dir>/scripts/run_lovpen_cli.py \
  --project-root LOVPEN_PROJECT_ROOT \
  -- --json render ARTICLE.md \
  --output ARTICLE.lovpen.wechat.html \
  --format wechat \
  --template-kit typora-newsprint
```

只有 JSON 回执显示 `renderer_mode=wechat-browser-copy`、`clipboard_source` 指向 `extractWechatClipboardHTML`，且产物根节点为 `section.lovpen-renderer`、包含内联样式而不含 `<style>` 时，才交给发布脚本：

```bash
python3 <skill-dir>/scripts/publish_via_gateway.py ARTICLE.md \
  --lovpen-wechat-html ARTICLE.lovpen.wechat.html \
  --app-id APP_ID \
  --wechat-secret-locator WECHAT_SECRET_LOCATOR \
  --gateway-key-locator GATEWAY_KEY_LOCATOR \
  --brand-profile BRAND_PROFILE \
  --cover COVER_DIR/share-cover-wide-logo.jpg \
  --cover-composition-receipt COVER_DIR/cover-composition.json
```

脚本不解析重建正文，也不清除 `class`、`style`、`span` 或表格；只在原始 HTML 字符串中把本地 JPG/PNG 的 `src` 替换为上传占位符，再替换成微信 HTTPS 地址。上传前后必须核对内联样式、class、span、table 与 img 数量完全一致，并比较忽略图片 `src` 后的全文 SHA-256。`--lovpen-html` 保留为兼容别名，但输入契约同样只接受 `--format wechat` 产物。`--allow-compact-markdown` 和 `--allow-unverified-cover` 只用于显式诊断旧链路，不得用于正常交付。收据同时记录 Lovpen 产物和品牌封面合成证据。

浏览器或显式 direct transport 也必须返回远端 `media_id` 或提供草稿箱重载证据。一次按钮点击、进度结束或本地 HTML 生成都不是远端草稿证据。

### 5. 补齐并回读编辑器字段

当任务需要原创声明或其他当前公开 OpenAPI 不支持的字段时，`draft_created` 不是可交付终态。`digest` 是公开草稿 API 可写并能在后台回读的摘要/推荐语字段；不要因为原创字段缺失而重新改写已核验的 `digest`。

1. 使用本 Skill 的 existing-draft 内部流程，打开刚创建的 `media_id` 对应草稿并取得编辑页 `appmsgid`。写入前记录标题、推荐语、原创状态、封面和其他可见开关；未指定字段列入保持不变集合。
2. 不要向 `api.weixin.qq.com/cgi-bin/draft/add` 或 `draft/update` 塞入 `copyright_type`、`original_article_type` 等未公开字段；接口可能返回成功但静默丢弃。
3. 内容权利已由用户明确确认时，调用网页私有 API 脚本。脚本在已登录页面上下文中读取正文与封面，向 `operate_appmsg` 写入带序号字段，并且不把 Cookie 或 token 写入参数、日志或收据：

```bash
python3 <skill-dir>/scripts/enrich_via_wechat_web_api.py \
  --appmsg-id APPMSG_ID \
  --title "TITLE" \
  --author "AUTHOR" \
  --digest "RECOMMENDATION" \
  --source-url "SOURCE_URL" \
  --original-category "艺术文化" \
  --confirm-original-rights \
  --receipt RECEIPT.json
```

4. `--confirm-original-rights` 是必需的权利声明门，不得替用户猜测。私有接口无稳定性承诺；页面结构或字段漂移时立即停止，不得降级成“请求成功即完成”。
5. 保存后重新获取同一编辑页，必须观察到 `copyright_type=1` 与请求的 `original_article_type`；同时回读推荐语、封面素材和非目标字段。
6. 只有全部符合后才记录 `draft_ready`。`ret=0` 但原创状态不可观测时保留 `draft_enriching`，并将 `verificationPending=true`。

详细的混合链路见 [references/editor-enrichment.md](references/editor-enrichment.md)。

### 6. 正式发布既有草稿

用户已明确要求公开发布时，使用刚核验的 `media_id`。若任务要求编辑器字段，必须先达到 `draft_ready`：

```bash
python3 <skill-dir>/scripts/publish_existing_draft.py submit \
  --media-id MEDIA_ID \
  --app-id APP_ID \
  --wechat-secret-locator WECHAT_SECRET_LOCATOR \
  --gateway-key-locator GATEWAY_KEY_LOCATOR \
  --wait-seconds 300 \
  --receipt RECEIPT.json
```

脚本默认经统一网关执行，并从 `lov-env-management` 解析两项密钥。`--transport direct` 仅为诊断保留；脚本不输出 AppSecret、网关 Key 或 access token。

等待结束仍为 `publishing` 时，保留 `publish_id`，随后查询：

```bash
python3 <skill-dir>/scripts/publish_existing_draft.py status \
  --publish-id PUBLISH_ID \
  --app-id APP_ID \
  --wechat-secret-locator WECHAT_SECRET_LOCATOR \
  --gateway-key-locator GATEWAY_KEY_LOCATOR \
  --receipt RECEIPT.json
```

如 transport 已自带经验证的正式发布与状态回读，可沿用其实现，但仍按本 Skill 的状态和收据契约报告。

### 7. 处理可恢复错误

- `40164`：默认链路中只检查后端固定出口是否仍在公众号白名单，不要求添加本机 IP；记录后端部署与微信返回详情后修复网关配置。
- `40013`：重新核对以 `wx` 开头的 AppID。
- `40001` / `40125`：重新获取或重置 AppSecret。
- `48001`：检查账号认证状态与草稿/发布接口权限。
- 正文图片被过滤：把图片保存为本地 JPG/PNG，经 `media/uploadimg` 重写 URL 后重建草稿。
- 草稿创建中途失败：检查永久素材是否已上传；重试前避免无依据地重复堆积封面素材。

错误回复必须保留阶段、错误码、接口详情、请求 ID、时间和最短恢复动作，并提供可复制内容。

## 完成前检查

1. 预检无 `errors`，标题、Lovpen 微信复制态 HTML、品牌封面合成收据和正文来自本次输入。
2. 目标公众号账号已核对，AppSecret 未进入项目文件或输出。
3. 正文图片所选 transport 能真实上传并重写 URL。
4. `media_id` 只报告为远端草稿；`publish_id` 只报告为已提交任务。
5. 只有 `freepublish/get` 状态为 0 且回读到文章标识时报告公开发布完成。
6. 收据包含输入摘要、动作、远端标识、状态、时间和可复制的错误详情。
7. Lovpen 路径同时记录提交前 `lovpenFidelityVerified=true` 和远端 `remoteFidelityVerified=true`；后者必须列出微信实际清洗的标签/属性，并证明其余标签、class、CSS 与文字不变。standalone HTML 被明确拒绝而不是静默降级。
8. 品牌化文章的分享封面回读为带 `publication.logo` 的最终合成件；正文首块是独立的 `4:3` 横向首图，与分享封面不是同一文件，也不在正文再写一次平台标题。
9. 研究评测类文章的方法、实际 Prompt、指标、评分规则、评分示例、复现方法和局限性已在 canonical Markdown 中通过预检；发布器未把内容问题包装成版式问题或用远端成功掩盖。
10. 需要原创声明时，收据 transport 为 `wechat-web-private-api`、`originalVerified=true`、`editorFieldsVerified=true`，并且已保存重载后回读 `copyright_type=1` 与目标分类；只得到 `operate_appmsg ret=0` 不算完成。推荐语、封面和其他指定字段同样必须回读一致，未指定设置保持平台默认。
11. 所有需要读者可见 Caption 的正文图片均已由 `lov-image-decorator` 生成派生文件并回读收据；Caption 只承担证据说明、必要归属或解释任务，不重复 alt、正文或内部制作备注，也不暗示未经授权的品牌背书。
12. `publicationComponentsVerified=true`；永久品牌尾注与个人卡片已出现，当前仍开放、未满员且未过期的活动位于其前，满员或结束的活动未被误投。

官方端点、字段限制与状态码见 [references/official-api.md](references/official-api.md)。

## References

- [已有草稿操作](references/existing-draft-operations.md)
- [文章状态契约](references/article-state-contract.md)
- [结果契约](references/result-contract.md)
- [Skill 组合](references/skill-composition.md)
