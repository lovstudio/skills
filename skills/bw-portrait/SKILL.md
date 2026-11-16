---
name: lov-bw-portrait
description: >
  把单人照片用 gpt-image-2 重绘成身份保真的黑白棚拍头像，默认浅灰背景的明亮编辑风，并核对五官、牙齿、饰品与小尺寸辨识度。Use when the user asks“做成黑白高级感头像”or “create a B&W editorial avatar”。
license: MIT
compatibility: "Portable Agent Skills format. Requires image viewing, Python 3.8+, an OpenRouter key with gpt-image-2 image editing, and ImageMagick 7 or macOS sips for image preparation."
depends_on:
  - lov-branding-consistency
metadata:
  author: lovstudio
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  tags:
    - portrait
    - avatar
    - black-and-white
    - image-editing
    - identity-preservation
---

# 黑白人像 · B&W Portrait

把一张单人照片重绘成有棚拍质感的黑白头像：人物仍然一眼可认，光线、背景和影调是
重新拍出来的效果，而不是给原照片去色再叠颗粒。默认是浅灰无缝背景、柔光、细颗粒
的明亮编辑风，也可以换成深色背景的经典棚拍。

## Triggers

### Activate when

- 用户说“把这张照片做成黑白高级感头像”“出一版黑白形象照”“按黑白明亮的风格重做头像”。
- 用户给出已有成品并要求“参考这个黑白风格，把另一张也做一下”。
- 用户对黑白头像成品提出单点修改，例如“牙齿要优化”“表情别那么丧”。
- The user asks to “create a B&W editorial avatar”, “make a black-and-white studio
  portrait from this photo”, or “restyle this headshot in the airy monochrome look”.

### Do not activate when

- 用户要彩色职业照、磨皮提亮、去帽补发型；使用 `lov-professional-portrait`。
- 用户要 Riso、孔版印刷或插画风头像；使用 `lov-riso-portrait`。
- 用户要带文字、Logo 的海报、名片或信息图；使用相应设计 Skill。
- 多人合影且没有指定主角；先请用户指定或换单人照片。
- 当前环境既没有可用的 gpt-image-2 图像编辑，也无法补上密钥：明确停止并说明缺什么，
  不得用去色、叠雨丝、暗角、背景虚化等本地滤镜冒充同等结果。

## User Profile (cross-session)

每次运行读取 `skill.yaml` 声明的 `user-profile/v1`，按当前请求、项目上下文、
`skills.lov-bw-portrait.records`、共享 Preferences 和安全默认值解析默认风格、景别与
输出目录。只有用户直接声明的长期偏好才通过 `scripts/profile_store.py record --confirm`
保存，并报告保存路径；照片、人物身份信息、临时提示词、访问凭据和生成结果不得写入
Profile。完整约定见 `references/user-profile.md`。

## Skill Group Composition

运行前读取 `references/skill-composition.md`。本 Skill 独占“身份保真的黑白棚拍头像”
这一结果；相邻能力只通过原图或完成后的图片文件可选交接，不构成隐藏依赖。

## Workflow (MANDATORY)

**按顺序执行。**

### Step 0: 解析根目录与运行条件

1. 使用环境变量 `SKILL_DIR`；未设置时从当前 Skill 上下文解析安装目录。
2. 确认 `scripts/bw_portrait.py`、`references/art-direction.md`、
   `references/quality-gate.md`、`references/provider.md` 存在；缺失时报出相对路径并停止。
3. 读取 `references/provider.md`，确认生图通道可用。默认通道是自带 CLI 加
   `OPENROUTER_API_KEY`；宿主自带 gpt-image-2 图像编辑时可作为等价替代。
4. 开工前只读查询余额，余额不足时先告诉用户，不要生成到一半才卡住：

```bash
python3 "$SKILL_DIR/scripts/bw_portrait.py" balance --images 2
```

### Step 1: 说明上传并确认照片

- 生图意味着照片会上传到第三方模型服务。用户已明确要求用 AI 生图或点名本 Skill 时，
  用一句话说明照片将上传到哪里，然后继续；用户只说“优化一下”“换个风格”而没有提到
  AI 生图时，先用一句话问清是否同意上传。不得为了回避上传而悄悄改成本地滤镜方案。
- 上传许可只针对当前这张照片和当前任务，不延伸到其他照片。
- 只处理用户有权使用的单人照片。原始文件一律不修改，所有中间文件写到工作目录。

### Step 2: 查看原图并规整参考图

先查看原图，记录会影响提示词的事实：

- 人物在做什么、表情和视线、头部角度；
- 眼镜形状、头巾或帽子、耳机、首饰、胡须、麦克风等身份特征；
- 衣服上是否有印花、文字或 Logo；
- 原图是否带有色彩处理、半调网点、海报图形或其他风格化处理；
- 是否是镜子自拍：文字是反的、手里举着手机。

再规整成可上传的参考图。人物在全身照里占比小的时候先裁出头肩区域；镜子自拍加
`--flip` 还原方向：

```bash
python3 "$SKILL_DIR/scripts/bw_portrait.py" prepare PHOTO --out WORK/ref.jpg
python3 "$SKILL_DIR/scripts/bw_portrait.py" prepare PHOTO --crop 1200x1200+905+1450 --flip --out WORK/ref.jpg
```

### Step 3: 定最小简报

读取 `references/art-direction.md`。只在缺失信息会明显改变人物或用途时问一个问题，
其余用默认值补齐：

| 项目 | 默认 | 可选 |
| --- | --- | --- |
| 风格 `--style` | `airy`：浅灰背景、柔光、明亮编辑风 | `studio`：深色背景棚拍 |
| 景别 `--framing` | `close`：头肩特写，适合头像 | `keep`：保持原构图、姿势与手势 |
| 表情 `--expression` | 不填，保持原图表情 | 用英文写明要变成什么 |

`--subject`、`--keep`、`--remove` 用英文把 Step 2 记下的事实写进去。这三项决定身份
保真度，不能省略。用户的额外要求放进 `--note`，不得覆盖身份约束。

### Step 4: 生成

先干跑检查提示词，再真正调用。单张约两分钟，超过两张或预计超过两分钟时放到后台
运行，等待期间不要轮询：

```bash
python3 "$SKILL_DIR/scripts/bw_portrait.py" generate --photo WORK/ref.jpg \
  --style airy --framing close \
  --subject "A man speaking mid-sentence at a talk, with a purple halftone poster treatment." \
  --keep "thin rectangular metal-rimmed glasses, bandana headwrap, clip-on microphone at the collar." \
  --name portrait-close --out-dir WORK/gen --dry-run
```

- 第一轮每个方向只生成一张，先验收再决定是否修正；需要给用户选择时，用不同的
  `--framing` 或 `--style` 各出一张，而不是同一提示词重复多张。
- 要改表情时不要传 `--style-ref`：风格参考图会把表情、眼镜和饰品往它身上拉。
  细节见 `references/art-direction.md` 的“参考图的拉力”。
- 脚本拒绝覆盖已有输出，每一轮换一个 `--name`，旧版本保留。

### Step 5: 三个尺度验收

读取 `references/quality-gate.md` 并逐项检查，必须亲自查看图片：

1. 全图：人物、姿势、衣服和画面重心是否符合原图与简报；
2. 脸部放大：眼睛、鼻子、嘴唇、牙齿、胡须、眼镜框形状是否仍是本人；
3. 头像尺寸：用 `thumb` 缩到 132 像素，确认仍可辨认、头顶和下巴没有被裁掉。

```bash
python3 "$SKILL_DIR/scripts/bw_portrait.py" thumb WORK/gen/portrait-close.png --out WORK/thumb.png
```

整体氛围好看不能替代事实检查。和原图有出入的地方逐条记下，交付时如实说明。

### Step 6: 一次只改一个事实

发现问题或用户提出修改时，以已验收的成品为底图做单点修正，不整张重来：

```bash
python3 "$SKILL_DIR/scripts/bw_portrait.py" fix --image WORK/gen/portrait-close.png \
  --preset teeth --name portrait-close-teeth --out-dir WORK/gen
python3 "$SKILL_DIR/scripts/bw_portrait.py" compare --before WORK/gen/portrait-close.png \
  --after WORK/gen/portrait-close-teeth.png --zoom 300x220+330+470 --out WORK/teeth-compare.jpg
```

- 内置 `--preset teeth`；其他事实用 `--change` 写英文，衣服印花、手势等容易被顺手
  重画的部分用 `--keep` 点名。
- 每次修正后用 `compare` 看修改处的放大对比和整体差异，确认没有修好一处又改坏
  另一处，再重新走 Step 5。
- 表情调整属于重新生成，回到 Step 4。

### Step 7: 交付

```bash
python3 "$SKILL_DIR/scripts/bw_portrait.py" export --image WORK/gen/portrait-close-teeth.png \
  --out OUTPUT/portrait-close-v0.2.jpg
```

- 按用户、宿主或项目约定的路径与命名导出；没有约定时写入当前目录的 `output/images/`。
- 直接展示成品并报告保存路径。
- 如实说明：脸是模型重画的而不是原始像素；哪些细节与原图不一致；衣服印花和文字
  属于近似重绘；本轮与累计的模型费用。
- 未经用户另行要求，不上传、不发布、不替换任何账号头像。

## Completion Criteria

- 缩到头像大小仍能认出同一个人。
- 画面是重新打光的黑白棚拍照片质感，不是去色照片或叠加滤镜。
- 五官、牙齿、可见手指、眼镜、头饰、衣服和姿势没有未说明的事实错误。
- 原图保持不变；每一轮结果都保留，最终文件路径、与原图的出入和费用已报告。

## Dependencies

- 可查看本地图片的 Agent 运行时
- Python 3.8+（脚本只用标准库）
- 环境变量 `OPENROUTER_API_KEY`，账户可调用 `openai/gpt-5.4-image-2`
- ImageMagick 7（`magick`）用于裁切、翻转、对比与缩略图；仅规整和导出时可用 macOS `sips` 代替
- `scripts/profile_store.py` 与 `scripts/validate_skill.py` 需要 PyYAML
- 生成服务按张计费，费用由使用者自己的账户承担
