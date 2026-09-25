# 文章品牌化（旧入口） · Article Branding (Legacy)

![Version](https://img.shields.io/badge/version-0.11.1-CC785C)

> 已归并：新任务请使用 `lov-article-creator` 的 `brand` 管线。本目录只保留历史实现与兼容路由，不应继续安装或被语义发现。

自动读取微信公众号文章，完成标题与内容智能、真实艺术或生成式主视觉、双比例 Logo 分享封面（横版居中、方版底部）、正文首屏品牌图、作品背景或可选封面 Prompt，以及稳定品牌预设应用。

## 本地安装

首选通过 Skills 目录安装：

```bash
npx skills add lov-wechat-article-branding -g -y
```

在源码开发环境中，也可从本仓库根目录链接：

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" \
  "$SKILLS_INSTALL_DIR/lov-wechat-article-branding-skill"
```

## 用户配置

发布主体、工作室品牌、产品、链接、语气和设计指南通过共享 Profile 提供。封面与正文首图只使用发布主体的官方 Logo；品牌尾注默认只展示工作室品牌，不自动枚举产品。只有与正文直接相关或用户明确要求的产品才加入，并只展示一个主链接。真实配置不进入 Skill 源码。

默认共享配置：

```bash
${SKILL_PROFILE_PATH:-$SKILLS_CONFIG_DIR/profile.json}
```

详见 `references/user-config.md` 与 `references/brand-profile.md`。

## 使用

```text
$lov-wechat-article-branding-skill 把当前公众号文章整体品牌化：生成目录、重构封面、增加专业的品牌收尾并保存验证。
```

```text
$lov-wechat-article-branding-skill audit 当前文章，只检查内容、审美和品牌一致性，不修改。
```

```text
$lov-wechat-article-branding-skill 给当前文章增加正文首屏品牌图，并把这次实际使用的封面 Prompt 作为可复制区块放在品牌尾注之前。
```

## 管线

- `full`：内容、封面、品牌和验收
- `content`：标题、结构、TOC、摘要或明确要求的正文润色
- `cover`：封面策略、制作、上传和裁切验收
- `brand`：稳定、独立的品牌内容与可复制资产块
- `audit`：只读质量检查

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 scripts/validate_brand_profile.py --self-test
```

## 依赖

- 能复用用户登录状态的浏览器自动化适配器
- 封面任务按需使用图像或素材能力
- Python 3.8+
- PyYAML（源码结构校验）

正文首屏品牌图与封面 Prompt 是独立可关闭选项，`full` 管线默认开启。封面艺术方向从旧封面创作 skill 与共享 Profile 持久读取；生产 Prompt 模板内置在 `prompts/cover-hero-editorial-painterly.md`，公开选项与落地规则见 `references/cover-prompt.md`。

## License

MIT
