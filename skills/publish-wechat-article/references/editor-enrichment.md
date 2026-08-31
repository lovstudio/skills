# 公众号编辑器补全契约

当网关 `draft/add` 未覆盖用户要求的可见字段时，使用已登录的公众号编辑页补全。这是创建草稿后的第二阶段，不是可选的人工备忘。

## 两类 API 的边界

公开 `api.weixin.qq.com/cgi-bin/draft/add` 与 `draft/update` 可写标题、正文、封面、作者、`digest`、阅读原文与评论开关。其中 `digest` 对应后台可见的摘要/文章推荐语，写入后必须经 `draft/get` 或编辑页回读。

- `draft/add` 返回 `media_id` 只能证明远端草稿存在。
- 公开接口文档没有原创声明字段。实测追加 `copyright_type`、`original_article_type`、`creation_source_type` 或 `article_type=original` 时，请求可以成功，但 `draft/get` 不返回这些字段，后台也不勾选原创。
- 公众号后台实际通过登录态私有端点 `mp.weixin.qq.com/cgi-bin/operate_appmsg` 保存原创声明，字段采用文章序号后缀，例如 `copyright_type0=1`、`original_article_type0=艺术文化`、`reprint_permit_type0=1`。
- 回读前不得把草稿写成 `draft_ready`，也不得进入正式发布。

私有网页 API 未出现在公开 OpenAPI 文档中，可能随公众号后台版本漂移。它只适用于用户已授权、已登录且目标草稿明确的会话；Cookie 与 token 不得落盘或进入收据。

## 字段契约

```json
{
  "original": {
    "requested": true,
    "categoryRequested": "艺术文化",
    "copyrightTypeObserved": 1,
    "categoryObserved": "艺术文化",
    "verified": true
  },
  "recommendation": {
    "requested": "字一放大，术语就不能含糊。",
    "observed": "字一放大，术语就不能含糊。",
    "verified": true
  },
  "cover": {
    "asset": "share-cover-wide-logo.jpg",
    "publisherLogoPresent": true,
    "verified": true
  },
  "otherFields": "platform_defaults",
  "saved": true,
  "reloaded": true
}
```

## 推荐语写法

- 默认 8–24 个中文字符，一句即止。
- 优先用文章中的张力、反差或关键判断造一个小记忆点。
- 不复述标题，不写章节摘要，不用“干货”“必看”“一篇读懂”等泛化词。
- 有梗但不强行抖机灵；优先准确，其次才是俏皮。

## 持久化验收

1. 写入前快照包含标题、推荐语、原创状态、封面和所有非目标开关。
2. 只修改计划中的字段；`otherFields: platform_defaults` 表示其他字段不主动改变。
3. 声明原创前必须由用户明确确认其拥有原创权利；执行器要求显式的 `--confirm-original-rights`，不绕过声明或强制提示。
4. 保存调用返回 `ret=0` 只证明请求被接受。随后重新获取同一编辑页，必须观察到 `copyright_type=1` 和目标 `original_article_type`，逐字比较 `digest`，并确认封面仍为带官方 Logo 的素材。
5. 重载丢失或无法可靠观测的字段保持 pending，不从 DOM 瞬时状态推断已保存。

## 私有网页 API 执行

`scripts/enrich_via_wechat_web_api.py` 连接到用户已授权的 Chrome CDP 会话，并在编辑页同源上下文内完成请求。这样 Cookie 与 token 不离开浏览器；脚本只在收据中保存脱敏编辑页 URL、`appmsgid`、字段观察值和验证状态。提交时先复制当前编辑页全部命名字段，再覆盖标题、正文、作者、推荐语、阅读原文和原创相关字段，避免用旧版最小 payload 重置评论、封面展示或其他新版设置。

脚本为避免破坏草稿设有三道保护：

1. 读取不到正文时停止，避免用空正文覆盖草稿。
2. 读取不到封面 `fileid` 或 CDN URL 时停止，避免清除封面。
3. 保存成功但重载不可观测原创字段时退出失败，状态保持 `draft_enriching`。
