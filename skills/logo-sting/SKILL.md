---
name: lov-logo-sting
description: >
  所有视频 Skill 共用的品牌片尾（media end）：把官方 Logo SVG 做成片尾动画与同帧合成音效，笔画逐拍砸入、字标落在小节线；一条命令按共享 Profile 生成，一条命令并进整片混音。用于「片尾品牌动画」「Logo 收尾」「给视频加品牌片尾」；Use for a logo sting, brand outro or the shared media end.
license: MIT
compatibility: >
  Portable Agent Skills format. Python 3.9+ (logo_spec.py and sting_timing.py stdlib only; sting_audio.py needs numpy);
  Node.js 24+ with npm/npx and Remotion 4.0.534 + React 19.1 (pinned in assets/remotion-template); ffmpeg and ffprobe;
  rsvg-convert, qlmanage or a browser to view the grouping preview. Network once for npm install into
  ~/.cache/lov-logo-sting unless --node-modules reuses an existing Remotion 4.0.534 install.
metadata:
  author: lovstudio
  version: "0.2.0"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  tags:
    - logo-sting
    - brand-outro
    - video-ending
    - remotion
    - sound-design
    - motion-graphics
---

# 品牌片尾 · Logo Sting

把品牌的官方 Logo SVG 变成一段卡拍的片尾：中心光点吸气内爆，Logo 的笔画一拍一笔砸入（震屏、RGB 分离、冲击波、火花），
吸入变暗，小节线上一帧负片，字标落定并扫过一道光，随拍呼吸，最后硬切黑场；合成音效与画面读同一份帧表，每一击落在同一帧。
参考实现是《如何用 AI 制作视频》v0.2 的 4.8 秒片尾（30 fps、100 bpm、三笔）。

交付物：`spec.json`（Logo 规格）、`timing.json`（帧表）、`sting.wav`（音效），以及挂进宿主 Remotion 工程的 `<LogoSting>`
Sequence，或给其它剪辑管线的独立 `sting-<画幅>.mp4`；另附关键帧联系表与数值质检。

## 共享片尾（Media End）

本 Skill 同时是**所有视频类 Skill 的默认片尾**（作者 2026-11-17：采访片结尾的 Logo 片段就是手工川视频的 media end 模板，
其他视频 Skill 都用它）。片尾长什么样只登记一次，在共享 Profile 的 `preferences.video_outro`：官方 SVG 与 sha256、
三个颜色、fps、bpm、`intro`、音效增益、真峰值上限。宿主 Skill 不再各自挑 Logo、调颜色或写混音脚本，只做两步：

```bash
# 1. 生成：读 preferences.video_outro，校验 SVG sha256，写 spec.json / timing.json / sting.wav / outro.json
python3 "$SKILL_DIR/scripts/media_end.py" make --out "<project>/work/sting" [--fps <本片 fps>]
# 2. 并进混音：配乐先在片尾起点淡出；把音效按帧加进整片混音，限幅、定响度、复测真峰值
python3 "$SKILL_DIR/scripts/media_end.py" mix --mix <整片混音> --sting "<project>/work/sting/sting.wav" \
  --at-frame <片尾起点帧> --fps <本片 fps> --out <最终混音> [--gain 0.40 --target -16 --tp -3.0]
```

- **默认开启**：宿主不必再问「要不要片尾」；只有作者明确说本片不要片尾时才省略。片尾接在正片（或合影）之后，总长 = 起点 + `outro.json.frames`。
- **画面**：Remotion 宿主把 `LogoSting.tsx` 挂成最后一个 Sequence，`intro` 取 `outro.json.intro`（手工川为 `black`），
  不传 `audioSrc`；其它管线用 `render_sting.py` 出 clip 接在末尾。
- **声音**：片尾下不垫配乐，由片尾音效收住整片；增益 0.40、真峰值 ≤ −3.0 dBTP 是参考采访成片的实测参数（0.95 增益在
  AAC 编码后真峰值会冲到 0 dBFS）。宿主有自己的母带前混音器时，可在那里按同样增益和帧位并入，只用 `make`。
- **一致性**：同一份记录、同一 fps，`timing.json` 与 `sting.wav` 逐字节相同；`spec.json` 只有 `source` 文件名可能不同。
- 记录缺失时按下方 User Profile 一节问一次并写回 `preferences.video_outro`。

## Triggers

### Activate when

- 用户说「给这条视频加个品牌片尾」「片尾用 Logo 做个酷炫收尾，带音效」「结尾加 Logo 收尾动画」。
- 用户说「把那个 Logo 收尾动画用到这条片子上」「换成 LovPen 的 Logo 再出一版片尾」「片尾要 16:9 和 9:16 两版」。
- 视频类 Skill（`lov-media-creator`、`lov-motion-media-creator`、`lov-interview-media-creator` 等）在定片尾时交来官方 Logo
  SVG、本片 fps 和可选的拍点网格，要一段片尾。
- The user asks to "add a logo sting to the end of this video", "make a brand outro from our logo SVG", or "use the
  logo sting from the last film".

### Do not activate when

- 要设计、重画或改 Logo：交给 `lov-gen-logo`。本 Skill 只用官方文件，不画新 Logo。
- 要找某个品牌的 Logo 文件：交给 `lov-find-logo`；拿到的必须是品牌自己的官方 SVG 才能进本 Skill。
- 要剪整条片、做字幕、混音或发布：交给对应片型 Skill（如 `lov-media-creator`）或 `lov-media-publisher`；本 Skill 只交片尾。
- 要一段全新风格的 Logo 演绎、片头字或别的单个动效（尤其用户点名 HyperFrames）：交给 `motion-graphics` / `hyperframes`。
- 只要静态 Logo 卡、角标水印、视频号封面或章节条：分别留给片型 Skill、`lov-channels-cover`、`lov-video-chapter`。

## User Profile (cross-session)

每次运行先读共享 Profile（`skill.yaml` 声明 `user-profile/v1`）：

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" read --skill-id lov-logo-sting --pretty
```

按下面的顺序解析，取到即停：

| 值 | 解析顺序 |
| --- | --- |
| 共享片尾（`media_end.py`） | `preferences.video_outro`（SVG、sha256、颜色、fps、bpm、intro、增益、真峰值上限）→ 缺失时问一次并写回 |
| Logo SVG（传给 `--svg`） | 当前请求点名的文件或宿主 Skill 交来的品牌素材 → `preferences.video_outro.svg` → `skills.lov-logo-sting.records.logo_svg` → `brand.logo` → 问一次 |
| 强调色 `accent` | 当前请求 → `records.accent` → SVG 自带的彩色填充（`logo_spec.py` 默认）→ 都没有时问一次 |
| 高光色 `hot` | 当前请求 → `records.hot` → 由 accent 向白混 60 % 推出 |
| 落定色 `final` | 当前请求 → `records.final` → `#FFFFFF` |

- `brand.logo` 可能是另一个品牌（母品牌、个人品牌、产品）或方形图标版。片子署名的品牌与 `brand.name` 不一致、或文件是方形图标时，
  先问一次用哪个品牌的哪个文件；Profile 里的 `$HOME/...` 路径传给脚本前要展开。
- 只有用户直接说出、并且是长期有效的值才写回，例如「以后片尾都用这个 SVG」「我们的强调色是 #3366FF」：

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" record --skill-id lov-logo-sting \
  --path records.logo_svg --value '"$HOME/brand/logo-white.svg"' --confirm
```

写完报告保存路径。推断出的值只留在本次任务里。完整合同见 `references/user-profile.md`。

## Skill Group Composition

本 Skill 是所有视频类 Skill 的默认片尾：它们在 frontmatter `dependencies:` 里登记本 Skill，按「共享片尾」一节用 `media_end.py`
生成并混音；作者明确不要片尾时才省略，宿主没装时报出安装命令。
交接全部是文件：官方 SVG → spec → timing → wav → Sequence 或 clip。片子放在哪、整片混音与响度质检仍归片型 Skill。
详见 `references/skill-composition.md`。

## Workflow (MANDATORY)

**按顺序执行。** 所有中间文件写进宿主项目的工作目录（下文记作 `$W`，例如 `<project>/work/sting`），不写进 Skill 目录。

### Step 0：解析环境与输入

1. `SKILL_DIR` 优先取宿主提供的值，否则用本 `SKILL.md` 所在目录。确认这些文件存在：
   `$SKILL_DIR/scripts/logo_spec.py`、`$SKILL_DIR/scripts/sting_timing.py`、`$SKILL_DIR/scripts/sting_audio.py`、
   `$SKILL_DIR/scripts/render_sting.py`、`$SKILL_DIR/scripts/media_end.py`、`$SKILL_DIR/assets/remotion/LogoSting.tsx`、`$SKILL_DIR/assets/remotion-template/package.json`。
   缺任何一个，报出相对路径后停止。
2. 检查工具：`python3 -c "import numpy"`、`node --version`（24+）、`ffmpeg -version`、`ffprobe -version`。
3. 按上表解析 Logo 与颜色；确定宿主：Remotion 工程（路线 A）还是其它管线（路线 B）；读出本片 fps、画幅、片尾起点，以及配乐的拍点网格（有的话）。
4. 读 `references/spec-contract.md`：三份文件的字段、取整规则和组件参数以它为准。

### Step 1：Logo 规格（只用官方 SVG，绝不重画）

```bash
python3 "$SKILL_DIR/scripts/logo_spec.py" --svg "<official-logo.svg>" \
  --out "$W/spec.json" --preview "$W/spec-preview.svg"   # 需要时加 --accent '#RRGGBB' --hot --final
rsvg-convert -w 1200 "$W/spec-preview.svg" -o "$W/spec-preview.png"   # 或 qlmanage -t -s 1200 -o "$W" …；或用浏览器打开
```

- 看一眼预览：彩色编号的是逐拍砸入的笔画（编号即落下顺序），灰色的是在小节线上一起落下的字标。笔画数、顺序、
  符号与字标的分界都要和品牌 Logo 的构成一致。
- 分错了就改参数重跑，不改文件：纯图标 Logo 被内部空隙误切成「笔画 + 字标」时用 `--mark N`（N = 全部路径数）；
  顺序不对或几段路径属于同一笔时用 `--order 2,0+1`。
- 脚本拒绝时（退出码 2）按原因处理：活字 `<text>` → 要转曲后的官方文件；徽章/反白锁定（白字压在色块上）→ 要单色版；
  没有彩色填充 → 用 `--accent` 给品牌强调色；旋转/斜切变换、`rect` 等非路径形状 → 要导出为纯路径的官方文件。
  任何情况下都不手改路径、不描摹位图、不用相近字体重排字标；也不要自己按 SVG 写的字体名转曲，活字的字形随机器上装的字体而变，转曲版要由品牌方或设计师导出并确认。
- 核对 `colors.final` 是品牌在深色底上的 Logo 颜色；彩色 Logo 要么用官方反白版，要么用 `--final` 给官方颜色。

### Step 2：帧表（卡拍）

- **独立使用**（片子没有配乐或配乐已结束）：`--fps` 填本片帧率，`--bpm` 默认 100。

```bash
python3 "$SKILL_DIR/scripts/sting_timing.py" --spec "$W/spec.json" --fps 30 --bpm 100 --out "$W/timing.json"
```

- **跟着本片配乐**：把配乐拍点网格换算成「片尾起点为 0」的局部帧，用 `--beats` 传入（第一个必须是 0），笔画落在第 1..N 拍、
  字标落在第 N+1 拍，`--dur` 可指定总长：

```bash
python3 "$SKILL_DIR/scripts/sting_timing.py" --spec "$W/spec.json" --fps 30 \
  --beats 0,18,36,54,72,90,108,126 --dur 144 --out "$W/timing.json"
```

- 推荐做法：把配乐剪到正好结束在一条小节线上，片尾从这条小节线开始，片尾底下不再垫配乐，由片尾音效收住整片（参考成片就是这样）。
  三笔 Logo 在 4/4 拍里字标正好落在下一小节线；笔画数不同时，`--beats` 可以跳过某些拍，让字标仍落在小节线上。
- 拍子太快会被拒绝（吸入段放不下），降 bpm 或换网格。规则与更多例子见 `references/integration.md`。

### Step 3：音效

```bash
python3 "$SKILL_DIR/scripts/sting_audio.py" --timing "$W/timing.json" --out "$W/sting.wav"
```

48 kHz 立体声 16-bit，确定性生成（固定种子），真峰值归一到 −1 dBTP，长度严格等于 `dur / fps` 秒。每一击都在帧表的帧上。

### Step 4：接入成片

**路线 A — Remotion 宿主**（详细步骤与代码见 `references/integration.md`）：

1. 复制 `$SKILL_DIR/assets/remotion/LogoSting.tsx` 到宿主 `src/`；`spec.json`、`timing.json` 放 `src/data/`（tsconfig 开
   `resolveJsonModule`，可直接 import 后传入）；`sting.wav` 放 `public/`。
2. 作为最后一个 Sequence 挂上：`<Sequence from={start} durationInFrames={timing.dur}>`；合成的 fps 必须等于 `timing.fps`，
   总长 = `start + timing.dur`。
3. 声音二选一：宿主直接出声时传 `audioSrc`（如 `"sfx/logo-sting.wav"`）；宿主另有统一的最终混音时不传 `audioSrc`，
   把 `sting.wav` 以 0.95 增益放在起点帧并进母带前的混音，Remotion 只挂那一条最终混音。
4. 开场：上一场戏收成画面中心的一个光点时用默认 `intro="point"`（1080 短边下约 6 px 白芯、58 px 白光晕，黑底），
   两者无缝衔接；否则用 `intro="black"`，第一击之前是纯黑，由音效的前奏承接。

**路线 B — 其它管线**（FFmpeg、剪映等）：

```bash
python3 "$SKILL_DIR/scripts/render_sting.py" --spec "$W/spec.json" --timing "$W/timing.json" \
  --audio "$W/sting.wav" --aspect 9x16,16x9 --out "$W/clips/"
# 已有 Remotion 4.0.534 安装时加 --node-modules <dir>/node_modules，免去一次 npm install
```

- 画幅：`9x16` 1080×1920、`16x9` 1920×1080、`1x1` 1080×1080、`4x3` 1440×1080；fps 取自帧表。输出 H.264 CRF 16 + AAC 320k，
  标 bt709，脚本自带 ffprobe 校验。
- 用 FFmpeg concat **滤镜**把片尾接到成片母版后面，只重编码一次（命令见 `references/integration.md`）；剪映直接导入 MP4 放到末尾。
- **接完必须重测整片**：对最终编码文件跑 `ebur128=peak=true`，看整体响度与真峰值。参考成片加片尾后，AAC 编码文件的真峰值一度超过
  0 dBFS，把母带目标降到 −2.5 dBTP、限制器 0.70 重混后才过（最终 −16.0 LUFS / −2.8 dBTP）。

### Step 5：质检（细则与参考数值见 `references/qc.md`）

1. **关键帧联系表**：光点（0）、每一击（`hits`）、吸入变暗（`gate + 1`）、负片（`bar`）、扫光、静置、硬切黑（`cut`）。
   逐张看：Logo 形状完整无变形，最终锁定位置正确，没有裁出画外（砸入的一两帧碰边属正常）。
2. **品牌检查**：`spec.json` 的 `source_sha256` 等于官方文件的 `shasum -a 256`；用相同参数重跑 `logo_spec.py` 与现有 spec 逐字节一致
   （证明没被手改）；整段没有「圆盘 + 放射线」构图，光条、火花、闪光都是水平向，圆形只有细冲击波环。
3. **声音检查**：WAV 样本数 = `round(dur / fps × 48000)`；接入后整片响度与真峰值达标；最后几帧黑场时声音已收住。
4. **时长与帧率**：片尾帧数 = `dur`，fps 与宿主一致，路线 A 的合成总长与起点正确。
5. 报告：交付文件路径、所用 SVG 与 sha256、帧表、关键帧联系表路径、各项数值；未做的检查写明未做。

## Dependencies

- Python 3.9+；`sting_audio.py` 需要 numpy，`logo_spec.py`、`sting_timing.py`、`profile_store.py` 只用标准库。
- Node.js 24+、npm/npx；Remotion 4.0.534、React 19.1.0（版本锁在 `assets/remotion-template/package.json`）。
- ffmpeg、ffprobe；查看分组预览用 rsvg-convert、qlmanage 或浏览器任一。
- 首次路线 B 渲染需联网执行一次 `npm install`（装进 `~/.cache/lov-logo-sting/remotion-4.0.534`），给 `--node-modules` 时不联网。
- 不依赖其它 Skill。正常输出是动画、音效与结构化数据，不生成读者可见的文案（字标是 Logo 原形状），因此不需要
  `lov-branding-consistency`，frontmatter 不写 `depends_on`。

## Validation

```bash
python3 "$SKILL_DIR/scripts/validate_skill.py" "$SKILL_DIR"
```

可信度材料：`skill-card.yaml`、`skill-card.md`、`cases/cases.json`、`pricing-card.yaml`。
