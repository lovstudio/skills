# lov-article-creator

![Version](https://img.shields.io/badge/version-0.4.1-CC785C)

公众号文章统一离线入口：从主题、研究材料或旧稿创建正文，也可品牌化现有文章或忠实转载合作方原文；正文文风统一走 `lov-writing-style → lov-human-writing`，再生成来源、分享封面、`4:3` 正文首图、品牌信息和质量报告。

## 为什么是一个 Kit

公众号文章不是单纯的 Markdown。内容写作、模板装配、双比例视觉与质量门彼此依赖，但发布到远端又必须保持独立授权，因此本项目把前四个阶段做成自包含 Skill Kit：

- `article-writing`：事实账本、题材结构与 `lov-writing-style` 交接；
- `editorial-template`：固定语义模板和文章 manifest；
- `cover-package`：无字艺术底图、官方 Logo、分享封面与 `4:3` 正文首图；
- `quality-gate`：结构、品牌、尺寸、散列和状态验收。

默认管线止于本地 `prepared` 包，不会自动创建公众号草稿或正式发布。

## 本地安装

Canonical 源码位于 LovStudio Skills 工作区，安装入口应指向共享 Skill 目录：

```bash
npx skills add /absolute/path/to/article-creator-skill -g -y
ln -s /absolute/path/to/article-creator-skill ~/.agents/skills/lov-article-creator
```

不同宿主的 Skill 目录再用相对软链接指向 `~/.agents/skills/lov-article-creator`，避免产生多份漂移副本。

## 使用

完整创建：

> 根据这些研究材料，按我的文风写成公众号文章；公开测试方法、Prompt、评价指标、评分方法与复现入口，并生成分享封面和 4:3 正文首图。

输入是主题、材料或草稿；输出是 `output/articles/<slug>/` 下的完整文章包。

只做审计：

> 检查这套公众号文章包，不要发布；把内容、品牌、封面和 manifest 的问题列出来。

`audit` 管线只生成报告，不修改远端状态。

品牌化和转载不再各自作为公开 Skill：使用 `brand` 或 `repost` 管线。公众号后台已有草稿的读取、修改与保存回读统一交给 `lov-publish-wechat-article`。

## 固定默认值

- 模板：`wechat-longform-v1`
- 文风：`手工川-v2`
- 品牌系统：`lovstudio-warm-academic-v1`
- 母品牌：`LovStudio`
- 公众号发布主体：`手工川`
- 封面 Logo：手工川官方白色横向 lockup；LovStudio、方形和橙色变体禁止使用
- 横版封面：`2.35:1`，默认 `1880×800`
- 正文首图：`4:3` 横向，默认 `1600×1200`
- 首图位置：标题之后、导语之前

这些值记录在共享 `user-profile/v1`，源码只保留可移植的安全默认值，不写入用户私有绝对路径。

## 输出

```text
article.md
article-manifest.json
sources.md
cover/art-master.png
cover/wechat-cover-wide.png
cover/wechat-cover-wide.jpg
cover/article-opening-4x3.png
cover/article-opening-4x3.jpg
cover/cover-manifest.json
quality-report.json
```

历史案例见 [`cases/agent-harness-system-prompt`](cases/agent-harness-system-prompt)，它保留 v1 的 `3:4` 首图作为迁移回归样本；v2 新文章包必须使用 `4:3` 正文首图。

## 验证

```bash
python3 scripts/validate_skill.py .
python3 scripts/validate_article_package.py \
  --package cases/agent-harness-system-prompt \
  --json
```

## 依赖

- Python 3.9+
- PyYAML
- Pillow 10+
- 完整封面需要宿主图像生成能力，或一张有合法使用权的艺术底图

## License

MIT。文章素材、Logo 和生成图片仍服从各自来源、品牌及平台规则。
