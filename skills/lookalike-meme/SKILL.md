---
name: lov-lookalike-meme
description: >
  把真人现场照片和一张参考形象图做成网感“撞款/像不像”表情包对比图：AI 画原创 Q 版，HTML 排大标题，出 1080×1440 PNG。用于“做张撞款图”“P 个像不像表情包”或 "make a lookalike meme"。
license: MIT
compatibility: "Python 3.9+ with Pillow; Chrome or Chromium for headless rendering; SmileySans font; OPENROUTER_API_KEY for the cartoon step; ffmpeg only for video frames."
depends_on:
  - lov-branding-consistency
metadata:
  author: lovstudio
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: microcopy
  tags:
    - meme
    - lookalike
    - comparison-image
    - chibi-cartoon
---

# 撞款表情包 · Lookalike Meme

给一位真人的照片（或视频帧）和一张“她/他像谁”的参考形象图，交付一张粉色网点加放射线背景、
三张白边歪斜贴纸、一个黄字粗黑描边大标题的竖版对比图，外加单独的原创 Q 版卡通 PNG。

## Triggers

### Activate when

- “把他和这只黄色卡通鸭做张撞款图。”
- “P 一张像不像的表情包，配个大标题。”
- “用这张视频截图画个 Q 版，和这个卡通角色放一起对比。”
- "Make a lookalike meme of my friend and this cartoon."
- "Turn this photo into a twinning comparison sticker image."

### Do not activate when

- 修人像、做头像大片：交给 `lov-spectacular-ps`。
- 只要一张通用插画或海报：交给 `lov-image-creator` 或 `lov-event-poster`。
- 只给现有图片加说明底栏或 Logo：交给 `lov-image-decorator`。
- 未经本人同意拿真人做梗图，或用于嘲讽、骚扰、冒充、商业广告。

## Gates (MANDATORY, before any upload or paid call)

1. **本人同意**：确认照片中的人本人同意被做成表情包；请求里没有说明时问一次，未确认不做。
   只拿到“别人说可以”时同样先问清。
2. **第三方上传告知**：卡通步骤会把本人照片（缩到长边 1024）上传到 OpenRouter 及其下游
   模型服务商。开工前用一句话说明；用户不同意上传时，只做排版，卡通格换成用户自备图或去掉。
3. **版权标注**：参考图若是有版权的角色（动画、品牌吉祥物、游戏角色等），交付时写明
   “参考图含第三方版权角色，成品仅适合私下或群内使用，不适合商用或公开推广”。
   参考角色只用用户提供的原图，不让生图模型画它，也不把它上传给生图模型。
4. **报价**：生图前运行 `gen_cartoon.py --quote` 并告诉用户单次估价（默认模型约
   USD 0.17–0.25 / 张）与计划调用次数；用户请求里已授权本次生成时可直接执行。
5. **记账**：每次调用（成功、拒绝、网络失败）都由脚本追加一行到项目的
   `ledger/costs.jsonl`；网络失败不自动重试，费用记为未知，由用户决定是否重来。

## Workflow

`SKILL_DIR` 指本 Skill 根目录；所有输出默认放在当前项目的工作目录（如 `work/<slug>/`）。

### Step 1: 素材准备

- 真人图：视频里取帧并方裁到脸和标志物（帽子、衣服）：

  ```bash
  python3 "$SKILL_DIR/scripts/prep_photo.py" --video clip.mp4 --time 00:12:03 --out work/x/frame.png
  python3 "$SKILL_DIR/scripts/prep_photo.py" --image work/x/frame.png --crop X,Y,W,H --out work/x/photo-crop.jpg
  ```

  先看图再定裁剪框；人脸占贴纸一半左右，保留撞款的那个元素。
- 参考图：用用户给的原图；带边框或水印边时先裁掉外框，内容图用 `#contain` 放进白卡。

### Step 2: 原创 Q 版卡通（付费，过完 Gates 再跑）

看参考图，把它的**姿势**用文字写进 `--pose`，把本人的辨识特征写进 `--features`：

```bash
python3 "$SKILL_DIR/scripts/gen_cartoon.py" --quote
python3 "$SKILL_DIR/scripts/gen_cartoon.py" \
  --photo work/x/photo.jpg \
  --features "yellow raincoat, round glasses, curly brown hair" \
  --pose "three-quarter side view, both arms stretched out to the sides, feet together" \
  --out work/x/cartoon.png --item x-cartoon-1 --ledger ledger/costs.jsonl
```

- 只上传本人照片；提示词要求原创角色、不模仿任何版权角色、图里不出现任何文字。
- 打开生成图检查：像本人（帽子、发型、配色）、姿势对上、无文字无水印、不像参考角色本身。
  不合格时说明原因，再报一次价后重画；不要静默连续重试。
- 模型可用 `--model` 或 `LOOKALIKE_MEME_MODEL` 覆盖，默认 `openai/gpt-5.4-image-2`。

### Step 3: 排版出图

```bash
python3 "$SKILL_DIR/scripts/render_meme.py" \
  --title "鸭鸭本鸭" \
  --sticker work/x/ref.png#contain --sticker work/x/cartoon.png --sticker work/x/photo-crop.jpg \
  --palette pink --out work/x/meme.png --keep-html
```

- 贴纸 1–3 张，按阅读顺序：参考形象 → 卡通 → 真人。3 张是认可版式（左上、右上、下中）。
- 标题只放一个，3–8 字最好，像外号或一句吐槽（“鸭鸭本鸭”“这俩是不是一个人”）；
  需要换行用 `|`。不加副标题、标签、emoji、Logo、水印。标题文案过
  `lov-branding-consistency` 的受众与语气检查：亲昵玩笑，不贬低外貌。
- 中文字只由 HTML 排（得意黑 SmileySans）；字体找不到时脚本报错并给下载地址，不降级到别的字体。
- 配色：`pink`（默认）、`yellow`、`blue`、`mint`、`purple`、`orange`，挑和撞款元素反差大的。
- `--keep-html` 会在 PNG 旁边留一个 `_html` 目录，方便手调后重渲。

### Step 4: 验收与交付

- 读回 PNG：确认 1080×1440、标题无缺字或被裁、三张贴纸完整不出画、真人脸未被卡片遮挡。
- 交付两张：对比图 PNG 与卡通 PNG（绝对路径）、本次费用与账本位置、版权标注（如适用）。
- 用户对版式的可复用意见（如“以后都用蓝底”）写进 Profile，见下节。

## User Profile (cross-session)

每次运行读取 `skill.yaml` 声明的 `user-profile/v1`。本 Skill 的长期记录放在
`skills.lov-lookalike-meme.records`，常用键：`default_palette`、`title_style`、
`image_model`、`ledger_path`。用户直接说出要长期沿用的偏好时：

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" record \
  --skill-id lov-lookalike-meme --path records.default_palette --value blue --confirm
```

并报告保存路径。不保存照片、人名、同意记录或任何密钥。详见 `references/user-profile.md`。

## Skill Group Composition

相邻能力与交接见 `references/skill-composition.md`。版式细节和参数见
`references/layout.md`。

## Dependencies

- Python 3.9+、Pillow；`ffmpeg`（仅视频取帧）。
- Chrome / Chromium / Edge（`--chrome` 或 `CHROME_BIN` 指定）。
- 得意黑 SmileySans（OFL，https://github.com/atelier-anchor/smiley-sans；`--font` 或 `LOOKALIKE_MEME_FONT` 指定）。
- `OPENROUTER_API_KEY`（仅卡通步骤，从环境变量读取，不写入任何文件）。
- `lov-branding-consistency`：标题文案的语境检查。
