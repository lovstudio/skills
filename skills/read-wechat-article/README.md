# 公众号文章读取器 · WeChat Article Reader

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

把公开微信公众文章链接读取为本地 Markdown，保留正文、原图、元数据和来源。
文字型文章直接提取；图片型文章下载原图、做中文 OCR，再由代理逐图核对后整理。

## 本地安装

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" \
  "$SKILL_SKILLS_INSTALL_DIR/lov-read-wechat-article"
```

当前源码可在本机常用 Skills 安装目录中找到 `lov-read-wechat-article` 符号链接。

## 用户 Profile（跨 session）

每个生成的 Skill 都会在 `skill.yaml` 中声明 `user-profile/v1`，并从共享
Profile 读取用户、品牌、工作区和本 Skill 的长期记录。用户直接说出的持久
偏好或品牌事实由 `scripts/profile_store.py` 写回 Profile；源代码保持可移植。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

文字型文章：

```bash
python3 scripts/read_wechat_article.py URL --output-dir work/wechat
python3 scripts/render_markdown.py work/wechat/manifest.json
```

图片型文章：

```bash
python3 scripts/read_wechat_article.py URL --output-dir work/wechat
python3 scripts/ocr_images.py --image-dir work/wechat/images \
  --output work/wechat/ocr.json
python3 scripts/render_markdown.py work/wechat/manifest.json \
  --ocr work/wechat/ocr.json \
  --output work/wechat/article.md
```

输入：一条公开 `mp.weixin.qq.com` 文章 URL。

输出：

- `manifest.json`：标题、账号、发布时间、正文文本、图片清单；
- `images/`：按顺序保存的原文图片；
- `article.md`：可编辑、可离线阅读的 Markdown。

## 原子组合

[`references/skill-composition.md`](references/skill-composition.md) 记录了已
检查的相邻 Skills、可选交接、重叠处理，以及为何选择 Single Skill。外部
sibling Skill 不作为隐藏依赖。

## 可信度卡与用户案例

- [`skill-card.yaml`](skill-card.yaml) / [`skill-card.md`](skill-card.md)
- [`cases/cases.json`](cases/cases.json)
- [`pricing-card.yaml`](pricing-card.yaml)

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.8+
- PyYAML（运行 `validate_skill.py` 时）
- 网络访问
- macOS Vision 或带 `chi_sim` 的 Tesseract
- `lov-branding-consistency`

## License

MIT
