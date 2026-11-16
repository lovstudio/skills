# 黑白人像 · B&W Portrait

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

把一张单人照片重绘成身份保真的黑白棚拍头像。默认是浅灰背景、柔光、细颗粒的明亮
编辑风，也可以换成深色背景的经典棚拍。每张成品都会对照原图检查五官、牙齿、饰品和
缩成头像后的辨识度，并如实说明与原图的出入。

Skill ID：`lov-bw-portrait`

## 安装

```bash
npx lovstudio skills add bw-portrait
```

## 本地开发安装

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${LOVSTUDIO_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" "$LOVSTUDIO_SKILLS_INSTALL_DIR/lov-bw-portrait"
```

## 使用

对 Agent 直接说需求即可：

- “把这张照片做成黑白高级感头像” ：给一张自拍或活动照，得到 1024×1024 的头肩特写。
- “参考这个黑白风格，把另一张也做一下” ：给一张已有成品和一张新照片，得到同一风格的
  新头像。
- “牙齿要优化” ：对成品提出单点修改，得到只改这一处的新版本和前后对比图。

也可以直接使用命令行：

```bash
# 1. 规整参考图（HEIC 会转成 sRGB JPEG；镜子自拍加 --flip）
python3 scripts/bw_portrait.py prepare photo.heic --out work/ref.jpg

# 2. 开工前查余额
python3 scripts/bw_portrait.py balance --images 2

# 3. 生成（先加 --dry-run 检查提示词）
python3 scripts/bw_portrait.py generate --photo work/ref.jpg --style airy --framing close \
  --keep "thin rectangular metal-rimmed glasses, bandana headwrap" \
  --name portrait-close --out-dir work/gen

# 4. 单点修正与前后对比
python3 scripts/bw_portrait.py fix --image work/gen/portrait-close.png --preset teeth \
  --name portrait-close-teeth --out-dir work/gen
python3 scripts/bw_portrait.py compare --before work/gen/portrait-close.png \
  --after work/gen/portrait-close-teeth.png --zoom 300x220+330+470 --out work/compare.jpg

# 5. 头像尺寸检查与导出
python3 scripts/bw_portrait.py thumb work/gen/portrait-close-teeth.png --out work/thumb.png
python3 scripts/bw_portrait.py export --image work/gen/portrait-close-teeth.png --out output/portrait.jpg
```

| 选项 | 取值 | 说明 |
| --- | --- | --- |
| `--style` | `airy`（默认）、`studio` | 浅灰背景明亮编辑风；深色背景棚拍 |
| `--framing` | `close`（默认）、`keep` | 头肩特写；保持原构图、姿势与手势 |
| `--expression` | 英文描述 | 不填则保持原图表情 |
| `--keep` / `--remove` | 英文描述 | 必须保留的身份特征；必须去掉的东西 |

## 需要知道的事

- 照片会上传到模型服务商，开工前 Agent 会说明或征得同意。
- 脸是模型重画的，不是原始像素。眼镜框形状、头巾花纹、衣服印花可能与原图有出入，
  交付时会逐条说明。
- 每张约 0.25 美元、约两分钟，费用由你自己的 OpenRouter 账户承担；账户余额低于
  1 美元时无法生图。
- 去色、叠颗粒、加暗角这类本地滤镜不属于本 Skill 的结果。

## 用户 Profile（跨 session）

`skill.yaml` 声明了 `user-profile/v1`。Skill 从共享 Profile 读取语言、时区，以及本
Skill 的长期记录：默认风格、默认景别和默认输出目录。只有你直接说出的长期偏好才会由
`scripts/profile_store.py` 写回 Profile；照片、提示词、密钥和生成结果不会写入。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 原子组合

[`references/skill-composition.md`](references/skill-composition.md) 记录了已检查的相邻
Skill。本 Skill 与 `lov-riso-portrait` 并列，与 `lov-professional-portrait` 不重叠；
相邻能力只通过图片文件可选交接，不作为依赖安装。

## 可信度卡与用户案例

- [`skill-card.yaml`](skill-card.yaml) / [`skill-card.md`](skill-card.md)：用途、负责人、依赖、风险、输出与维度地图。
- [`cases/cases.json`](cases/cases.json)：两个真实案例，标准头像重绘与牙齿单点修正。
- [`pricing-card.yaml`](pricing-card.yaml)：当前免费，以及价值锚点、交付边界和复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.8+（生图 CLI 只用标准库）
- 环境变量 `OPENROUTER_API_KEY`，账户可调用 GPT Image 2
- ImageMagick 7（`magick`）；仅规整与导出时可用 macOS `sips` 代替
- PyYAML（`scripts/profile_store.py` 与 `scripts/validate_skill.py`）

## License

MIT
