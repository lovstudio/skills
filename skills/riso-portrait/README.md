# lov-riso-portrait

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

把单人照片用 `gpt-image-2` 重绘成身份保真的 Riso 头像，并在交付前检查五官、手指、
饰品与圆形头像裁切。它要求模型直接完成画面重组，不使用程序化滤镜冒充 Riso。

## 安装

```bash
npx skills add lov-riso-portrait -g -y
```

## 使用

上传一张清晰的单人照片，然后说：

```text
使用 Riso 人像 Skill 处理这张照片。保持人物身份、脸部结构、发型、视线和服装不变，
裁成适合圆形头像的近景，使用朱红与深青主墨色，并保留纸张颗粒、网点和轻微套印偏移。
```

第一轮完成后，可以只修一个事实：

```text
只修正右上方的手，必须是五根手指；其他人物特征、动作、构图和 Riso 风格保持不变。
```

## 结果边界

- 输出：身份保真的方形 Riso 头像 PNG，可选原图/结果或迭代对照图。
- 模型：必须使用 `gpt-image-2` 做图像编辑。
- 验收：人物识别、五官、手指、饰品、姿势、视线和圆形裁切。
- 不包含：程序化双色滤镜、照片后处理、Logo/文字海报、公开托管或模型调用额度。

## 用户 Profile

`skill.yaml` 声明 `user-profile/v1`，可以复用用户直接保存的默认配色、头像裁切和纸张
倾向。照片、人物身份信息、临时 Prompt、访问凭据和生成结果不会写入 Profile。

## 可信度与案例

- `skill-card.yaml` / `skill-card.md`：用途、依赖、风险、输出与维度证据。
- `cases/cases.json`：真实原图到 Riso 结果，以及四指到五指的局部修正案例。
- `pricing-card.yaml`：免费入口的价值依据、交付边界与复评条件。
- `references/skill-composition.md`：与职业照、通用生图和风格分析能力的边界。

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- 支持图片查看与编辑的 Agent 运行时
- `gpt-image-2`
- Python 3.8+ 与 PyYAML，仅用于 Profile 与源码校验

## License

MIT
