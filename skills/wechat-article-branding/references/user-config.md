# 用户配置

公众号品牌化将“品牌公开资料”和“个人运行偏好”分开保存：

- `SKILL_PROFILE_PATH` 指向用户的 `profile.json`；官网配置完成后由宿主同步或生成该文件。
- `SKILL_PREFERENCES_PATH` 指向用户的 `preferences.json`；这里只保存管线、开关和审美偏好。
- 如果宿主设置了 `SKILLS_CONFIG_DIR`，默认文件为该目录下的 `profile.json` 与 `preferences.json`。

## 解析顺序

1. 当前请求中的显式值；
2. 当前文章和项目上下文；
3. `preferences.json` 中 `skills.wechat_article_branding` 的偏好；
4. 通用 Profile 的公开品牌事实；
5. 不改变文章可见结果的中性默认值；
6. 仍缺少必需身份或 Logo 时，只询问一个聚焦问题。

```json
{
  "schema": "skill-preferences/v1",
  "version": 1,
  "user": {
    "language": "LANGUAGE",
    "timezone": "TIMEZONE"
  },
  "skills": {
    "wechat_article_branding": {
      "default_pipeline": "full",
      "opening_hero": {"enabled": true, "ratio": "3:4", "placement": "before_intro", "logo_position": "bottom_center"},
      "cover_prompt": {"enabled": true, "placement": "before_endcap", "title": "封面 Prompt"},
      "cover_composition": {
        "base": "artistic",
        "logo": {
          "enabled": true,
          "asset": "PUBLICATION_COVER_LOGO",
          "variant": "white",
          "position": "center",
          "max_width_ratio": 0.24,
          "panel": false,
          "square": {
            "position": "bottom_center",
            "max_width_ratio": 0.36,
            "max_height_ratio": 0.15,
            "bottom_margin_ratio": 0.05
          }
        },
        "background_dimming": {"enabled": true, "strength": 0.45}
      }
    }
  }
}
```

首次运行时只展示准备保存的字段；用户明确同意后才写入个人配置。文章正文、Cookie、编辑令牌、私人 URL、本地浏览器状态和生产 Prompt 不进入任何共享配置。
