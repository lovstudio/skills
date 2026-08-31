# Profile-driven editorial components

公众号文章的临时活动与永久品牌尾注都来自当前品牌 Profile，不写死在发布 Skill 中。正常发布前把品牌 Profile 路径同时传给 `preflight_article.py` 与 `publish_via_gateway.py`；两个脚本会在任何微信远端写入前核对 canonical Markdown。

## Profile contract

```json
{
  "blocks": {
    "endcap": {
      "enabled": true,
      "title": "关于品牌",
      "paragraphs": ["已批准的长期介绍。"],
      "links": [{"label": "个人主页", "url": "https://example.com/about"}],
      "card": {
        "enabled": true,
        "asset": "$HOME/branding/profile-card.jpg",
        "marker": "个人介绍卡片",
        "required_image": true
      }
    },
    "campaigns": [
      {
        "id": "campaign-id",
        "enabled": true,
        "status": "open",
        "capacity_state": "available",
        "starts_at": "2026-08-31T00:00:00+08:00",
        "ends_at": "2026-09-06T18:00:00+08:00",
        "title": "活动标题",
        "required_text": ["https://example.com/signup"],
        "required_image": true,
        "asset": "$HOME/events/campaign-poster.jpg",
        "placement": "before_endcap"
      }
    ]
  }
}
```

## Eligibility and placement

- `endcap.enabled=true` 时，标题、批准段落、链接与启用的个人卡片必须在 Markdown 中各出现一次；个人卡片不自动加 Caption，自包含的卡片保持安静。
- 活动只在 `enabled=true`、`status` 为 `open` 或 `active`、`capacity_state` 不是 `full`、`closed`、`paused` 或 `sold_out`，且当前时间位于可选起止窗口内时生效。
- 生效活动必须位于永久品牌尾注之前，并包含 Profile 声明的必要信息与招募海报。
- 满员或结束时更新 Profile 状态，不删除历史文章，也不在通用 Skill 中改活动文案。
- Profile 声明的品牌资产必须真实存在；文章可以引用适合微信上传的派生 JPG，但可见 marker 与组件结构必须保留。

## Commands

```bash
python3 <skill-dir>/scripts/preflight_article.py ARTICLE \
  --brand-profile BRAND_PROFILE \
  --cover COVER \
  --cover-composition-receipt COVER_DIR/cover-composition.json \
  --lovpen-wechat-html ARTICLE.lovpen.wechat.html \
  --transport gateway \
  --json
```

发布脚本使用同一个 `--brand-profile BRAND_PROFILE`。缺失或重复组件、活动已开放但正文没有招募区、个人卡片资产不存在，都会在上传前失败关闭。
