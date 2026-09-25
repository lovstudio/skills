# 图片装帧 · Image Finishing

![Version](https://img.shields.io/badge/version-0.2.3-CC785C)

为现有图片增加底部 caption 与右下品牌 Logo；艺术图片使用 Warm Academic 圆角外框，
软件截图使用无外框版式。

## 安装

目录发布后可使用统一安装命令：

```bash
npx skills add lov-image-decorator -g -y
```

从本地真源安装：

```bash
ln -s "$(pwd)" ~/.agents/skills/lov-image-decorator
```

## Profile

Skill 连接共享 `user-profile/v1`。当前请求优先于 Skill 记录与品牌 Profile；未提供
caption 时默认显示 `Powered by lovstudio.ai/skill/image-decorator`。

记录用户明确声明的长期默认 caption：

```bash
python3 scripts/profile_store.py record \
  --skill-id lov-image-decorator \
  --path records.default_caption \
  --value '"Powered by lovstudio.ai/skill/image-decorator"' \
  --confirm
```

## 使用

当前 DSH 深度文章的真实封面案例：

```bash
python3 scripts/decorate_image.py cases/assets/input-artwork.jpg \
  --caption "本期封面：Adriaan de Lelie《扬·希尔德梅斯特画廊》，1794—1795" \
  --output cases/assets/output-artwork-decorated.png \
  --json
```

不传 caption，验证默认 fallback：

```bash
python3 scripts/decorate_image.py cases/assets/input-artwork.jpg \
  --output cases/assets/output-artwork-decorated-fallback.png \
  --profile cases/assets/empty-profile.json \
  --json
```

输出会保留完整原图，并追加米白外框、炭黑 caption 栏与右下 LovStudio Logo。

截图已有窗口边界时，使用无外框模式；它会同时移除截图工具产生的透明阴影画布：

```bash
python3 scripts/decorate_image.py screenshot.png \
  --caption "插件市场搜索结果" \
  --style screenshot-caption \
  --output screenshot-decorated.png \
  --json
```

## 原子组合

`references/skill-composition.md` 记录相邻图片 Skills、文件级交接和 Single Skill
决策。上游可以生成或提供图片，下游可以上传或发布成品，但都不是运行依赖。

## 可信度卡与案例

- `skill-card.yaml` / `skill-card.md`
- `cases/cases.json`
- `pricing-card.yaml`

## 质量门

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.9+
- Pillow 9+

## License

MIT。内置 Noto Sans SC 使用 SIL Open Font License 1.1；品牌 Logo 仍受其品牌资产
使用规范约束。
