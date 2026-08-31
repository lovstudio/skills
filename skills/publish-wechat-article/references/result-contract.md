# 公众号文章结果契约

每次执行保留一份 JSON 收据。字段按可获得程度填写，不虚构远端标识。

```json
{
  "schemaVersion": 1,
  "platform": "wechat_official_account",
  "action": "read_draft | edit_draft | create_draft | publish | status",
  "state": "prepared | draft_reading | draft_read | draft_editing | draft_saved | draft_creating | draft_created | draft_enriching | draft_ready | publish_submitted | publishing | published | publish_failed",
  "title": "文章标题",
  "source": "/absolute/path/article.md",
  "transport": "uni-api-gateway | oneshot-direct | browser | wechat-web-private-api",
  "mediaId": "REMOTE_DRAFT_MEDIA_ID",
  "publishId": "PUBLISH_TASK_ID",
  "publishStatus": 0,
  "articleId": "PUBLISHED_ARTICLE_ID",
  "articleUrls": ["https://mp.weixin.qq.com/s/..."],
  "failIndexes": [],
  "verificationPending": false,
  "editorFields": {
    "originalRequested": true,
    "originalCategoryRequested": "艺术文化",
    "copyrightTypeObserved": 1,
    "originalCategoryObserved": "艺术文化",
    "originalVerified": true,
    "recommendationRequested": "字一放大，术语就不能含糊。",
    "recommendationObserved": "字一放大，术语就不能含糊。",
    "coverPublisherLogoPresent": true,
    "otherFields": "platform_defaults",
    "saved": true,
    "reloaded": true,
    "editorFieldsVerified": true
  },
  "checkedAt": "ISO-8601",
  "technicalDetail": {
    "publicationComponentsVerified": true,
    "bodyHeroVerified": true,
    "bodyHero": {
      "path": "/absolute/path/article-opening-4x3.jpg",
      "width": 1600,
      "height": 1200,
      "ratio": 1.3333,
      "distinctFromShareCover": true
    },
    "brandProfile": "/absolute/path/wechat-article-branding-brand.json",
    "endcap": {
      "required": true,
      "verified": true,
      "card": {"required": true}
    },
    "activeCampaigns": [
      {"id": "campaign-id", "verified": true}
    ],
    "imageCaptionPreparation": {
      "articleImageCount": 13,
      "decoratedImageCount": 8,
      "undecoratedImageCount": 5,
      "explicitCaptionsOnly": true,
      "fallbackCaptionUsed": false,
      "sourceImagesPreserved": true,
      "captionDuplicationChecked": true,
      "artifacts": [
        {
          "sourceSha256": "64_HEX_CHARS",
          "outputSha256": "64_HEX_CHARS",
          "style": "screenshot-caption",
          "receipt": "/absolute/path/image-caption-receipt.json"
        }
      ]
    },
    "coverCompositionVerified": true,
    "coverCompositionReceipt": "/absolute/path/cover-composition.json",
    "coverCompositionSchema": "lov-wechat-cover-composition/v1",
    "coverArtifactSha256": "64_HEX_CHARS",
    "coverLogoSha256": "64_HEX_CHARS",
    "coverLogoVariant": "white",
    "lovpenArtifact": "/absolute/path/article.lovpen.wechat.html",
    "lovpenArtifactSha256": "64_HEX_CHARS",
    "lovpenFidelityVerified": true,
    "lovpenFidelitySha256": "64_HEX_CHARS_WITH_IMAGE_SRC_NORMALIZED",
    "lovpenFidelityMetrics": {
      "inlineStyleAttributes": 582,
      "classAttributes": 150,
      "spanTags": 105,
      "tableTags": 2,
      "imageTags": 20
    },
    "remoteFidelityVerified": true,
    "remoteFidelityMetrics": {
      "inlineStyleAttributes": 544,
      "classAttributes": 150,
      "spanTags": 105,
      "tableTags": 2,
      "imageTags": 20
    },
    "remoteWechatSanitization": {
      "removedTags": {"a": 38},
      "removedStyleProperties": {"position": 3},
      "preservedTagSequence": true,
      "preservedClasses": true,
      "preservedRemainingCssProperties": true,
      "preservedVisibleTextIgnoringWhitespace": true
    },
    "endpoint": "mp.weixin.qq.com/cgi-bin/operate_appmsg",
    "appMsgId": "100014941",
    "sessionSecretsPersisted": false,
    "verificationSource": "operate_appmsg response or editor reload"
  }
}
```

常规草稿创建必须同时记录 Profile 驱动的出版组件、正文首图、图片 Caption 准备、品牌封面合成字段与 Lovpen 字段。`bodyHeroVerified=true` 表示 canonical Markdown 第一块是可回读尺寸的 `4:3` 横向首图，且与分享封面不是同一文件。`publicationComponentsVerified=true` 表示永久 endcap、个人卡片与当前生效活动已经在 canonical Markdown 中验收；活动满员、关闭或过期后不再列入 `activeCampaigns`。`imageCaptionPreparation` 说明哪些图片经 `lov-image-decorator` 生成派生文件、哪些图片因没有真实说明任务而保持原样；文章链必须满足 `explicitCaptionsOnly=true`、`fallbackCaptionUsed=false` 与 `sourceImagesPreserved=true`。`coverCompositionVerified=true` 表示上传封面与 `lov-wechat-branding-cover-composition` 收据中的 `shareCoverUpload` 一致，且收据中的官方 Logo 文件通过 SHA-256 复核。`lovpenFidelityVerified=true` 表示本地图片占位符和最终微信 HTTPS URL 替换前后，上述五项结构计数完全一致，而且把全部图片 `src` 归一化后全文 SHA-256 不变；这些本地证据都不替代远端 `draft/get` 回读。

`remoteFidelityVerified=true` 才表示微信存储后的正文通过逐节点回读。平台已观察到会移除外链 `<a>` 包装和 `position` CSS 属性；这些变化必须明确计数，其他标签顺序、class、CSS 属性与可见文字如有变化则回读失败。

## 判定规则

| 证据 | state | 对外表述 |
| --- | --- | --- |
| 本地文件与封面通过预检 | `prepared` | 已完成发布前检查 |
| 已有草稿完成读取并形成快照，未执行写入 | `draft_read` | 已读取公众号草稿 |
| 已有草稿保存、重载且状态差异符合 mutation plan | `draft_saved` | 草稿修改已保存并核验 |
| 已开始调用草稿 transport，尚未取得远端标识 | `draft_creating` | 正在创建远端草稿 |
| `draft/add` 返回 `media_id` | `draft_created` | 已同步至公众号草稿箱 |
| 正在补齐公开 OpenAPI 未覆盖的原创字段，或私有 API 已保存但尚未重载验证 | `draft_enriching` | 正在完善草稿设置 |
| 原创、推荐语与封面等字段保存重载后通过 | `draft_ready` | 草稿已完整核验 |
| `freepublish/submit` 返回 `publish_id` | `publish_submitted` | 发布任务已提交 |
| `freepublish/get` 返回 1 或等待超时 | `publishing` | 平台仍在处理 |
| `freepublish/get` 返回 0 且有文章标识 | `published` | 已公开发布 |
| `freepublish/get` 返回 0 但尚无文章标识 | `publishing` | 接口已报成功，仍待文章标识回读 |
| `freepublish/get` 返回 2–6 | `publish_failed` | 发布任务结束，状态为对应失败/移除原因 |

## 错误结构

```json
{
  "state": "failed",
  "stage": "stable_token | draft_add | freepublish_submit | freepublish_get",
  "code": 40164,
  "message": "接口原始详情",
  "recovery": "检查 LovStudio 网关固定出口是否仍在 API IP 白名单；无需添加本机 IP",
  "whitelistIp": "IP",
  "checkedAt": "ISO-8601"
}
```

错误详情用于复制和调试；AppSecret、access token、Cookie 与完整 Keychain 记录永远不进入收据。
