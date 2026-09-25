# WeChat 品牌 Profile 适配

公众号品牌化只读取用户 Profile，不在 Skill 源码内保存任何真实品牌资料。Profile 分为两层：通用字段由官网或其他 Profile 编辑器生成，公众号特有的发布主体、产品和文章区块放在 `extensions.lov-wechat-article-branding-skill` 下。

## 最小输入

```json
{
  "schema": "skill-profile/v1",
  "profile_id": "profile-id",
  "revision": 1,
  "identity": {
    "id": "publisher-id",
    "name": {"zh-CN": "发布主体名称", "en-US": "Publisher name"},
    "logo": "assets/publisher-logo.svg",
    "tagline": {"zh-CN": "Tagline", "en-US": "Tagline"}
  },
  "purpose": {
    "mission": {"zh-CN": "使命", "en-US": "Mission"},
    "vision": {"zh-CN": "愿景", "en-US": "Vision"},
    "values": ["价值观"]
  },
  "brand": {
    "site": "https://example.com",
    "colors": {"primary": "#3366FF"},
    "tone": ["clear", "restrained"],
    "public_facts": ["APPROVED_PUBLIC_FACT"],
    "forbidden_context": ["INTERNAL_CONTEXT"]
  },
  "extensions": {
    "lov-wechat-article-branding-skill": {
      "publication": {
        "name": {"zh-CN": "发布主体名称"},
        "logo": "assets/publisher-logo.svg",
        "cover_logo": "assets/publisher-cover-logo-white.png",
        "cover_logo_variant": "white",
        "logo_policy": "publisher_only"
      },
      "products": [],
      "blocks": {}
    }
  }
}
```

## 读取规则

- 优先读取 `extensions.lov-wechat-article-branding-skill`；没有扩展时，从通用 `identity` 和 `brand` 适配发布主体与品牌名称。
- `identity.logo` 是通用 Logo；公众号扩展中的 `publication.logo` 可以为不同发布账号指定官方 Logo。`publication.cover_logo` 是封面与正文首图专用变体，优先级高于通用 Logo；`publication.cover_logo_variant` 记录 `white` 等需要验收的颜色语义。这些字段都必须由用户 Profile 明确提供。
- `brand.public_facts`、产品名称、产品承诺、链接和固定品牌区块是允许公开的事实；`brand.forbidden_context` 只用于最终排除。
- 品牌尾注默认不枚举产品；只有与正文主题直接相关或用户明确要求时才读取对应产品。被选中的产品只展示 `products[].url` 主链接，品牌级链接不重复产品链接。
- 缺少会改变文章可见结果的字段时，按 `skill.yaml` 生成一个聚焦问题；不从项目名称、文章主题或当前聊天背景猜测。
- 公开文章不写入 Profile 版本、同步来源、个人配置、生产 Prompt、本地路径或内部备注。

## 兼容旧文件

验证器仍可读取根节点直接包含 `publication`、`brand`、`products`、`blocks` 和 `visual` 的旧结构。新配置应迁移到通用 Profile 与 `extensions`，旧结构只作为一次性迁移输入，不再作为分发示例。
