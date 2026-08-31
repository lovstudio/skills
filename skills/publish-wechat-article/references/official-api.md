# 微信公众号官方接口基线

以下链接是运行前的权威回读入口：

- 稳定版接口调用凭据：<https://developers.weixin.qq.com/doc/service/api/base/api_getstableaccesstoken>
- 上传永久素材：<https://developers.weixin.qq.com/doc/service/api/material/permanent/api_addmaterial>
- 上传图文消息内图片：<https://developers.weixin.qq.com/doc/service/api/material/permanent/api_uploadimage>
- 新增草稿：<https://developers.weixin.qq.com/doc/service/api/draftbox/draftmanage/api_draft_add>
- 更新草稿：<https://developers.weixin.qq.com/doc/service/api/draftbox/draftmanage/api_draft_update>
- 发布草稿：<https://developers.weixin.qq.com/doc/service/api/public/api_freepublish_submit>
- 查询发布状态：<https://developers.weixin.qq.com/doc/service/api/public/api_freepublish_get>

## 当前关键限制

- 标题：最多 32 字。
- 作者：最多 16 字。
- 摘要：最多 120 字。
- 正文：官方页面同时写有“2kb”“少于 20,000 字符”“小于 1M”，措辞自相矛盾。2026-08-27 实测 `draft/add` 接受 347,212 字符、361,820 UTF-8 字节的 HTML，其中去标签正文约 14,729 字符。因此 20,000 不得按原始 HTML 字符数校验；当前保守按渲染后的可见正文少于 20,000 字符、UTF-8 HTML 小于 1,000,000 字节检查。JavaScript 会被过滤。
- 阅读原文 URL：小于 1 KiB。
- 图文封面：永久素材 `media_id`；图片素材最多 10 MiB，支持 BMP/PNG/JPEG/JPG/GIF。
- 正文图片：先经 `media/uploadimg` 获取微信 URL；仅 JPG/PNG 且小于 1 MiB，不占永久图片素材数量。
- 原创声明：公开 `draft/add` / `draft/update` 文档没有 `copyright_type`、`original_article_type` 或等价字段。2026-08-27 实测给这两个接口附加这些字段会被静默忽略：调用成功、`draft/get` 不返回、后台未勾选。不得根据 HTTP 200 或 `errcode=0` 报告原创已设置。

公众号网页编辑器另有登录态私有端点 `mp.weixin.qq.com/cgi-bin/operate_appmsg`，可观察到 `copyright_type0`、`original_article_type0` 与 `reprint_permit_type0`。该端点不是公开 OpenAPI，字段和行为没有兼容性承诺；只能在授权登录态中使用，并以保存后重载回读为完成证据。

文档字段和账号权限会调整。执行真实发布前重新打开对应官方页面，页面现值优先于本文件。

## 发布状态

| `publish_status` | 含义 | Skill state |
| ---: | --- | --- |
| 0 | 成功 | 回读到文章标识后为 `published`，否则保留 `publishing` |
| 1 | 发布中 | `publishing` |
| 2 | 原创声明失败 | `publish_failed` |
| 3 | 常规失败 | `publish_failed` |
| 4 | 平台审核未通过 | `publish_failed` |
| 5 | 成功后用户删除全部文章 | `publish_failed` |
| 6 | 成功后系统封禁全部文章 | `publish_failed` |

`freepublish/submit` 返回成功只表示任务提交成功。以 `freepublish/get` 或官方回调的终态为完成证据。
