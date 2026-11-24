# 撞款表情包 · Lookalike Meme

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

给一位真人的照片和一张“像谁”的参考形象图，做出一张网感十足的撞款对比图：
AI 以本人照片为参考画原创 Q 版卡通并模仿参考姿势，HTML 排出粉色网点放射线背景、
白边歪斜贴纸和一个黄字黑描边大标题，输出 1080×1440 PNG，卡通另存一张。

## 安装

```bash
npx lovstudio skills add lookalike-meme -g -y
```

本地源码安装：

```bash
ln -s "$(pwd)" "${LOVSTUDIO_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}/lov-lookalike-meme"
```

## 使用

对 Agent 说：

- “把他和这只黄色卡通鸭做张撞款图，标题叫‘鸭鸭本鸭’。”
- “用这段视频 12 分 03 秒的画面，P 一张像不像的表情包。”
- "Make a lookalike meme of my friend and this cartoon."

Agent 会先确认本人同意、说明照片会上传到 OpenRouter、报价，然后：

```bash
# 1. 取帧裁剪
python3 scripts/prep_photo.py --video clip.mp4 --time 00:12:03 --out work/frame.png
python3 scripts/prep_photo.py --image work/frame.png --crop 280,620,520,520 --out work/photo-crop.jpg

# 2. 原创 Q 版（付费，约 USD 0.17–0.25 / 张，写入 ledger/costs.jsonl）
python3 scripts/gen_cartoon.py --quote
python3 scripts/gen_cartoon.py --photo work/frame.png \
  --features "yellow raincoat, round glasses" \
  --pose "both arms stretched out to the sides" \
  --out work/cartoon.png --ledger ledger/costs.jsonl

# 3. 排版
python3 scripts/render_meme.py --title "鸭鸭本鸭" \
  --sticker work/ref.png#contain --sticker work/cartoon.png --sticker work/photo-crop.jpg \
  --out work/meme.png
```

## 门禁

- 本人同意才做；照片会上传第三方模型服务，先说明。
- 参考角色只用用户提供的原图，不交给生图模型；含版权角色的成品只适合私下或群内使用。
- 生图前报价，每次调用记账；网络失败不自动重试。
- 中文标题只由 HTML 排版，不让生图模型写字。

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`。长期偏好（如默认配色、生图模型、账本路径）写入
`skills.lov-lookalike-meme.records`：

```bash
python3 scripts/profile_store.py record --skill-id lov-lookalike-meme \
  --path records.default_palette --value blue --confirm
```

详见 [`references/user-profile.md`](references/user-profile.md)。

## 依赖

- Python 3.9+、Pillow
- Chrome / Chromium / Edge
- 得意黑 SmileySans（[下载](https://github.com/atelier-anchor/smiley-sans)）
- `OPENROUTER_API_KEY`（卡通步骤）
- ffmpeg（仅视频取帧）
- `lov-branding-consistency`

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## License

MIT
