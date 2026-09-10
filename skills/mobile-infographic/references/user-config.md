# 品牌与用户配置

## 品牌解析顺序

1. 命令行 `--brand-profile <path>`。
2. 环境变量 `SKILL_MOBILE_INFOGRAPHIC_BRAND_PROFILE`。
3. 共享 Profile（`SKILL_PROFILE_PATH` 指向的 JSON）中的 `brand` 作用域，可覆盖
   `name`、`site`、`logo`、`font_family`。
4. 本 Skill 自带的 `assets/brand-profile.json`。

解析到的来源会写进 `scaffold` 的 JSON 输出（`brand_origin`）与系列 `manifest.json`，
便于回读这套卡用的是哪份品牌配置。

## 字段

| 字段 | 说明 |
| --- | --- |
| `name` | 页脚显示的品牌名 |
| `site` | 页脚链接；卡片上显示去掉协议的版本 |
| `logo` | 相对 `assets/` 的文件名或绝对路径，生成时内联为 data URL |
| `primary` | 标题与结论的主色 |
| `accent` | 强调色，用于线条、色块与序号底 |
| `accent_ink` | 强调色对应的文字色，必须达到 4.5:1 对比度 |
| `ink` / `muted` / `paper` | 正文色、次级色与纸色 |
| `font_family` | 字体栈，默认包含 PingFang SC 与回退字体 |
| `attribution` | 旧版署名前缀（兼容字段），默认 `Powered by` |
| `credit` | 页脚署名正文，如 `Powered by 卡片`；留空即不署名 |
| `credit_link` | 是否在署名后追加 `site` 链接，默认 `false` |

## 初始化

```bash
python3 "$SKILL_DIR/scripts/infographic_cli.py" init-brand \
  --name "品牌名" \
  --logo "/absolute/path/to/logo.png" \
  --site "https://example.com/mobile-infographic" \
  --path "$HOME/.config/lov-mobile-infographic/brand-profile.json"
```

`init-brand` 拒绝覆盖已有文件，除非显式加 `--force`；它不写入凭据，也不修改共享 Profile。

## 跨 session 记录

用户直接说出的长期偏好（默认比例、默认输出目录、常用模板）通过
`scripts/profile_store.py record --confirm` 写入 `skills.lov-mobile-infographic.records`，
例如 `records.default_ratio` 或 `records.output_dir`。推断值不写入 Profile。
