# 品牌片尾 · Logo Sting

![Version](https://img.shields.io/badge/version-0.2.0-CC785C)

把品牌的官方 Logo SVG 做成一段卡拍的片尾动画与同帧合成音效：中心光点吸气内爆，Logo 笔画一拍一笔砸入（震屏、RGB 分离、
冲击波、火花），吸入变暗，小节线上一帧负片，字标落定并扫过一道光，随拍呼吸，硬切黑场。画面和声音读同一份帧表，每一击落在同一帧。

可以挂进 Remotion 工程作最后一个 Sequence，也可以渲染成独立 MP4 接到任何剪辑管线的成片末尾。它也是 LovStudio 所有视频类 Skill 的
默认片尾（media end）：片尾配置在共享 Profile `preferences.video_outro` 里登记一次，`media_end.py make` 一条命令生成，`media_end.py mix`
一条命令并进整片混音。

参考实现是《如何用 AI 制作视频》v0.2（2026-10-21）的 4.8 秒片尾：30 fps、100 bpm、三笔。本 Skill 用同一官方 SVG 生成的音效与原片
逐字节一致，画面与成片逐帧对照平均 Y-PSNR 约 53.5 dB（片尾黑场之外的 140 帧）（细节见 [`references/qc.md`](references/qc.md)）。

## 安装

```bash
npx lovstudio skills add logo-sting
```

视频类 Skill 把它登记为默认片尾依赖，安装命令相同。开发时也可以用本地源码三层链接：

```text
~/.agents/skills/lov-logo-sting  ->  <本地源码>/logo-sting-skill
~/.claude/skills/lov-logo-sting  ->  ../../.agents/skills/lov-logo-sting
```

```bash
export SKILL_SOURCE_DIR="$(pwd)"          # 在本仓库根目录执行
ln -s "$SKILL_SOURCE_DIR" ~/.agents/skills/lov-logo-sting
ln -s ../../.agents/skills/lov-logo-sting ~/.claude/skills/lov-logo-sting
readlink -f ~/.claude/skills/lov-logo-sting   # 应解析到本仓库
```

## 使用

对 Agent 说：

> 给这条视频加个品牌片尾，用我们的白色横版 Logo，配乐最后一小节结束后接上，要 9:16 和 16:9 两版。

> Add a logo sting to the end of this Remotion film, hits on the score's beat grid.

手动跑一遍（`$W` 是你项目里的工作目录，不要放在 Skill 目录里）：

```bash
export SKILL_DIR="$HOME/.agents/skills/lov-logo-sting"
export W="$PWD/work/sting" && mkdir -p "$W"   # 项目里的工作目录

# 1. Logo 规格 + 分组预览（只读官方 SVG，路径原样拷贝）
python3 "$SKILL_DIR/scripts/logo_spec.py" --svg logo-white.svg --accent '#3366FF' \
  --out "$W/spec.json" --preview "$W/spec-preview.svg"
rsvg-convert -w 1200 "$W/spec-preview.svg" -o "$W/spec-preview.png"

# 2. 帧表：独立使用按 fps + bpm；跟配乐时用 --beats 传入以片尾起点为 0 的拍点帧
python3 "$SKILL_DIR/scripts/sting_timing.py" --spec "$W/spec.json" --fps 30 --bpm 100 --out "$W/timing.json"

# 3. 音效（确定性生成，48 kHz 立体声，真峰值 −1 dBTP）
python3 "$SKILL_DIR/scripts/sting_audio.py" --timing "$W/timing.json" --out "$W/sting.wav"

# 4a. Remotion 工程：拷入组件，JSON 放 src/data/，wav 放 public/，作为最后一个 Sequence 挂上
cp "$SKILL_DIR/assets/remotion/LogoSting.tsx" src/

# 4b. 其它管线：渲染独立片段（首次会 npm install 一次；已有 Remotion 4.0.534 时加 --node-modules）
python3 "$SKILL_DIR/scripts/render_sting.py" --spec "$W/spec.json" --timing "$W/timing.json" \
  --audio "$W/sting.wav" --aspect 9x16,16x9 --out "$W/clips/"
```

Remotion 挂载方式、外部混音、光点交接、FFmpeg 拼接命令和响度复测见 [`references/integration.md`](references/integration.md)；
三份数据文件的字段见 [`references/spec-contract.md`](references/spec-contract.md)。

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`。每次运行读共享 Profile：

- Logo SVG：当前请求或宿主 Skill 交来的文件 → `skills.lov-logo-sting.records.logo_svg` → `brand.logo` → 问一次。
- 颜色：`records.accent`、`records.hot`、`records.final`，没有时分别取 SVG 的彩色填充、强调色推出的高光、白色。

用户直接说出的长期偏好（例如「以后片尾都用这个 SVG」）用 `scripts/profile_store.py record ... --confirm` 写回并报告保存路径；
推断出的值不写回。完整合同见 [`references/user-profile.md`](references/user-profile.md)。

## 依赖

- Python 3.9+；`sting_audio.py` 需要 numpy，其余脚本只用标准库。
- Node.js 24+、npm/npx；Remotion 4.0.534 与 React 19.1.0（锁在 `assets/remotion-template/package.json`）。
- ffmpeg、ffprobe；看分组预览用 rsvg-convert、qlmanage 或浏览器。
- 路线 B 首次渲染联网 `npm install` 一次，装进 `~/.cache/lov-logo-sting/remotion-4.0.534`；给 `--node-modules` 时不联网。
- 不依赖其它 Skill；不生成读者可见文案，因此不需要 `lov-branding-consistency`。

## 原子组合

本 Skill 是 `lov-media-creator`、`lov-motion-media-creator`、`lov-3d-motion-media-creator`、`lov-interview-media-creator`、
`lov-motivational-video`、`lov-roundtable-clip` 的可选下游能力，交接全是文件：官方 SVG → spec → timing → wav → Sequence 或片段。
成片放在哪、整片混音与响度验收归片型 Skill。见 [`references/skill-composition.md`](references/skill-composition.md)。

## 质量门

```bash
python3 scripts/validate_skill.py .
```

每次交付前按 [`references/qc.md`](references/qc.md) 检查：关键帧联系表（光点、每一击、吸入、负片、扫光、静置、黑场），
spec 的 sha256 等于官方文件且重跑逐字节一致，整段没有「圆盘 + 放射线」构图，加入片尾后整片响度与真峰值在编码文件上复测。

可信度材料：[`skill-card.md`](skill-card.md)、[`cases/cases.json`](cases/cases.json)、[`pricing-card.yaml`](pricing-card.yaml)。

## License

MIT
