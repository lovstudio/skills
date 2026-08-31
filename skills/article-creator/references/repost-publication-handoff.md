# 公众号发布交接

## 交给下游的产物

本 Skill 只交付完成且审计通过的 `article.md`、`edition-manifest.json`、来源素材、封面资产和 source fidelity 收据。Lovpen、Caption、封面合成、网关上传、草稿回读与正式发布由 `lov-publish-wechat-article` 按自身入口与强制引用执行。

## 强制字段

- `content_source_url`：真实原文 URL；
- `copyrightMode`：`reprint`；
- 作者：来源账号或用户明确指定的转载署名；
- 摘要/推荐语：发布方新增微文案，不冒充来源摘要；
- 原创：不得请求或确认；
- 动作：默认 `create_draft`，除非用户明确授权公开发布。

## 远端回读

除了发布器的 Lovpen 保真门禁，还要重新选择 `data-repost-source`：归一化可见文字 SHA-256 与本地来源一致，原图数量符合账本，所有 `data-repost-block` 各出现一次，来源 URL 和封面可观察。

## 失败与重复草稿

`draft/add` 返回 `mediaId` 后，该标识必须立即写入诊断状态。若随后 `draft/get` 或保真审计失败：

1. 保存远端正文、元数据、阶段和 `mediaId`；
2. 比对平台实际删除的标签、属性、链接和空白；
3. 不再次 `draft/add`；
4. 优先更新同一草稿；无法更新时，只有在旧草稿可精确删除或用户接受重复风险后才新建；
5. 未核验草稿不得报告为 `draft_created`。

删除旧草稿是高影响操作，必须有精确 `mediaId` 和用户授权。

