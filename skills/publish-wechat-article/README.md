# 微信公众号文章发布器

![Version](https://img.shields.io/badge/version-0.8.0-CC785C)

微信公众号远端操作的唯一入口：读取或局部编辑已有草稿，也可从 Markdown、HTML 或纯文本创建草稿并通过统一网关回读核验。正式发布与草稿创建使用不同状态，只有微信返回公开文章标识时才报告已发布。

## 主要能力

- 读取已有草稿；按 mutation plan 做最小修改，保存重载后比较 before/after 状态
- 预检标题、作者、摘要、封面、正文与图片限制
- 经 LovStudio 统一网关上传正文图片、创建草稿并执行 `draft/get` 回读
- 解析 `lov-env-management` locator，不在参数、日志或收据中暴露密钥
- 直接接收 `lovpen-cli --format wechat` 复制态 HTML，只替换图片 URL，并对微信存储后的正文逐节点回读版式
- 在 Lovpen 渲染前调用 `lov-image-decorator`，只为需要证据说明、必要归属或解释的图片生成带 Caption 的派生文件与收据
- 读取公众号品牌 Profile，验收永久品牌尾注、个人介绍卡片与仍开放且未满员的活动组件
- 强制接收 `lov-wechat-branding-cover-composition` 的 `cover-composition.json`，核对官方 Logo 与实际上传封面
- 通过已登录编辑器的 `operate_appmsg` 私有网页 API 写入原创声明，保存重载确认后再把草稿标记为完整可用
- 将公开 API 的 `digest` 作为摘要/文章推荐语处理并回读，避免和原创字段混为一谈
- 品牌化文章强制区分无 Logo 艺术底图与带官方 Logo 的封面上传件
- 常规发布强制验收正文第一块为独立的 `4:3` 横向首图；`3:4` 竖图或复用分享封面成品会在远端写入前失败
- 研究评测类文章在发布前必须公开方法、实际 Prompt、指标、评分规则、评分示例、复现方法与局限性，避免只有排名和雷达图却没有证据链
- 提交既有草稿并轮询正式发布状态

## 安装

```bash
npx skills add lov-publish-wechat-article -g -y
```

## 必需的上游产物

常规草稿创建必须先完成五步：

1. 从当前品牌 Profile 应用永久 endcap、个人卡片，以及状态仍开放且未满员的活动组件。
2. 确认 canonical Markdown 第一块是独立的 `4:3` 横向正文首图；研究评测类文章的方法、Prompt、评分与复现链完整。
3. 用 `lov-wechat-branding-cover-composition` 生成带官方公众号 Logo 的 `share-cover-wide-logo.jpg` 与 `cover-composition.json`。
4. 逐图判断 Caption 是否承担真实阅读任务；需要者用 `lov-image-decorator` 和显式 Caption 生成派生文件，不需要者保持原样。
5. 用 `lovpen-cli` 渲染已更新的文章副本，生成 `--format wechat` 产物，再把同一品牌 Profile 传给预检和 `publish_via_gateway.py --brand-profile`。

活动满员、暂停、关闭或过期后只更新 Profile 状态，不修改通用 Skill，也不继续要求新文章携带该活动。图片装饰不允许调用默认 `Powered by ...` fallback 代替编辑判断，也不能把 alt、邻接正文和 Caption 写成同一句。独立网页格式 `--format standalone` 不属于微信公众号复制态。缺少必需上游产物时，发布脚本会在远端写入前失败关闭；两个 `--allow-*` 开关只用于显式诊断旧链路。

## 许可证

MIT
