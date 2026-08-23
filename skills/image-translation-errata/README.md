# lov-image-translation-errata

![Version](https://img.shields.io/badge/version-0.2.0-CC785C)

把含有原文与劣质机翻的截图变成校样式勘误图：旧错误仍可见，正确译文可独立
通读，原图布局与身份信息尽量不变。

## 安装

```bash
npx lovstudio skills add image-translation-errata
```

## 源码开发安装

将真实源目录接入共享 Skills 中间层，再让各 agent 目录指向中间层：

```bash
ln -s "/absolute/path/to/image-translation-errata-skill" \
  "$HOME/.agents/skills/lov-image-translation-errata"
ln -s "../../.agents/skills/lov-image-translation-errata" \
  "$HOME/.codex/skills/lov-image-translation-errata"
ln -s "../../.agents/skills/lov-image-translation-errata" \
  "$HOME/.claude/skills/lov-image-translation-errata"
```

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`。Skill 会读取用户语言、品牌语气、工作区
与专属记录；用户明确给出的长期偏好由 `scripts/profile_store.py` 写回共享
Profile，图片正文、隐私文本和推断信息不会持久化。

默认不显示“勘误”标题：删除线与深红替换文字已经承担校样语义。只有用户明确
要求，或缺少标题会导致标记被误读时才加。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

示例一：

> 给这张中英对照截图做机翻勘误。保留“银行重置”让读者看到错误，但划掉它，
> 紧接着写正确的产品语义；英文、头像、数据和布局不要变。

输出是一张校样式图片：错误片段保留并被删除线否定，正确片段紧随其后，完整
译文仍可通读。

示例二：

> Create an in-image translation errata for this product screenshot. Verify the
> terminology against official docs, expose the bad machine translation, and
> preserve the original interface.

输出包括经来源核验的修正图，以及一段简短的术语说明和仍存在的视觉限制。

## 原子组合

[`references/skill-composition.md`](references/skill-composition.md) 记录了
翻译审校、事实校验、通用图像生成与视觉复刻 Skills 的边界。外部能力只通过
证据简报或渲染简报进行可选交接，不是运行时隐藏依赖。

## 可信度卡与真实案例

- [`skill-card.yaml`](skill-card.yaml) / [`skill-card.md`](skill-card.md)
- [`cases/cases.json`](cases/cases.json)
- [`references/verified-case.md`](references/verified-case.md)
- [`pricing-card.yaml`](pricing-card.yaml)

## 质量门

```bash
python3 scripts/validate_skill.py .
```

验收同时检查语义正确、旧错误可见、修正译文可独立通读、原图结构不漂移和
CJK 文本逐字准确。

## 依赖

- 能查看图片的多模态运行时
- 宿主提供的参考图编辑能力
- 术语依赖当前或权威来源时需要联网或原始文档访问
- 无必需 Python 包、API Key 或 sibling Skill

## License

MIT
