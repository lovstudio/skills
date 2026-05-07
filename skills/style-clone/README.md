# lovstudio-style-clone

![Version](https://img.shields.io/badge/version-0.1.1-CC785C)

输入样本文章 → 提取结构化**文风画像** → 用该文风改写任意内容。

Analyze sample articles to extract an 8-dimension writing style profile, then rewrite any target article in that exact style.

Part of [lovstudio skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
git clone https://github.com/lovstudio/style-clone-skill \
  "${LOVSTUDIO_SKILLS_INSTALL_DIR:?Set LOVSTUDIO_SKILLS_INSTALL_DIR}/lovstudio-style-clone"
```

Or via the skills CLI:

```bash
npx lovstudio skills add style-clone -g -y
```

No external dependencies — pure Claude reasoning workflow.

## Usage

In Claude Code:

```
/lovstudio:style-clone
```

Paste your sample article(s) and target article. Claude will:

1. Extract an 8-dimension **style profile** (文风画像)
2. Rewrite the target article in the extracted style
3. Provide a diff explanation of key style adjustments

## Style Profile Dimensions

| 维度 | 分析内容 |
|------|---------|
| 句式节奏 | 句子长度分布、节奏模式 |
| 段落结构 | 段落长度、开头/结尾习惯 |
| 词汇偏好 | 用词风格、高频词、禁忌词 |
| 叙事视角 | 叙事人称、与读者的距离 |
| 情感温度 | 情绪基调、情感弧线 |
| 论证逻辑 | 论证结构、案例/数据使用习惯 |
| 修辞手法 | 常用修辞、标志性句式 |
| 整体基因 | 一句话文风定义 + 参照系作者 |

## Use Cases

- 模仿名家/博主文风写作
- 统一团队或品牌写作风格
- 将正式报告改写为公众号风格（或反之）
- 保存个人文风画像，批量改写内容

## License

MIT
