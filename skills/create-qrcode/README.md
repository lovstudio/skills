# lov-create-qrcode

![Version](https://img.shields.io/badge/version-0.1.1-CC785C)

把网址、文本或其他 UTF-8 内容生成可扫码验证的二维码 PNG，并跨 session 复用用户
自己的配色、圆角、尺寸、纠错和海报偏好。默认只有码本体，不带 header、footer、
标题或明文。

## 本地安装

```bash
npx skills add lov-create-qrcode -g -y
```

本地开发时，共享安装位应指向本 Skill 真源，宿主安装位再用相对 symlink 指向共享入口。

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`，读取用户、品牌、工作区、共享 Preferences 和
`skills.lov-create-qrcode.records`。当前请求优先于 Profile；只有用户直接声明的长期
偏好才由 `scripts/profile_store.py` 原子写回。

二维码载荷、Wi-Fi 密码、token、cookie 和一次性输入不得写进 Profile。

## 使用

默认命令只输出二维码方图。海报、标题和明文都必须由当前请求显式启用。

生成普通二维码，不把载荷留在 shell history：

```bash
printf '%s' 'https://example.com' | python3 scripts/create_qrcode.py \
  --stdin --output ./qrcode.png --verify auto --json
```

生成带标题和可见链接的陶土暖色海报，并真实扫码回读：

```bash
printf '%s' 'https://example.com' | python3 scripts/create_qrcode.py \
  --stdin --poster --title '扫码访问' --show-data \
  --palette clay --shape rounded --error-correction M \
  --output ./qrcode-poster.png --verify scan --json
```

保存用户直接声明的长期默认值：

```bash
python3 scripts/profile_store.py record \
  --skill-id lov-create-qrcode \
  --path records.default_shape \
  --value '"rounded"' --confirm
```

## 支持的偏好

- `preference_policy`: `apply-saved-qr-preferences`
- `default_palette`: `classic`、`clay`、`ink`、`olive`
- `default_shape`: `square`、`dots`、`rounded`、`extra-rounded`、
  `gapped-square`、`vertical-bars`、`horizontal-bars`
- `default_size`: 128–4096
- `default_error_correction`: `L`、`M`、`Q`、`H`
- `default_border`: 4–16 modules
- `default_poster`、`default_show_data`: boolean
- `default_title`: 仅在用户明确声明为长期默认时保存

## 原子组合

`references/skill-composition.md` 记录已检查的相邻能力、图片级交接与 Single Skill
判断。生成二维码是本 Skill 的唯一核心结果；图像装饰、Logo 创作和二维码识别均保持
独立。

## 可信度卡与用户案例

- `skill-card.yaml` / `skill-card.md`：用途、依赖、风险、输出和维度证据。
- `cases/cases.json`：真实 Input → Prompt → Output 案例。
- `pricing-card.yaml`：免费边界、价值依据与复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 -m unittest discover -s tests -p 'test_*.py'
```

## 依赖

- Python 3.10+
- `qrcode` 7.4+、Pillow 9+
- OpenCV Python 可选，用于 `--verify scan`
- PyYAML，仅用于 Skill 源码校验

## License

MIT
