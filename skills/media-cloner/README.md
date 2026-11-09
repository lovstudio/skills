# 视频风格复刻

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

`lov-media-cloner`：给一个博主，产出一份可校验的风格包。

- **风格包内容。** 八个维度的规则；每句原话都能在转写里逐字找到，每个数字都能回读到测量文件。
- **留出检验。** 画像冻结后才检验留出样本。
- **附带产物。** 风格说明书和参数化的 Remotion 包装模板。
- **封装。** 需要时可以把风格包封装成该博主的专属风格 Skill。

## 已包含

- `scripts/cloner.py`：流程台账。

  | 阶段 | 命令 |
  | --- | --- |
  | 环境与进度 | `doctor`、`status` |
  | 取样与拆分 | `init`、`register`、`freeze-split` |
  | 规则与冻结 | `build`、`verify`、`freeze` |
  | 留出检验 | `holdout-init`、`holdout-check` |
  | 统计与路由 | `metrics`、`route` |

  `build` 把规则草稿里的引文在转写中精确定位、编号、计算支持样本，并拒绝来自留出样本的证据。
- `scripts/measure.py`：测量。

  | 子命令 | 做什么 |
  | --- | --- |
  | `media` | 全片测量：剪点、静音、响度、真峰值、抽帧、接触表 |
  | `layout` | OCR 版式扫描，含区域发现与颜色聚类 |
  | `tones` | 提示音扫描 |
  | `transcribe`、`import` | 本地转写；或导入 Whisper、听悟、SRT |
  | `speakers` | 说话人提示 |

  画像冻结前，所有子命令都拒绝处理留出样本。
- `scripts/build_audio.py`：连续音轨，包括人声拼接、两遍响度归一，以及按参考测量放置的分隔音与配乐。
- `templates/remotion`：参数驱动的 `StyleClip` 与 `StyleCover`。颜色、字体、位置、描边都在 `style-tokens.json`。
- 六份 Schema：样本清单、规则草稿、风格画像、证据、留出报告、转写。
- [分析协议](references/analysis-protocol.md)、[选样与平台](references/sampling-and-platforms.md)、[八个维度](references/dimensions.md)、[规则与证据](references/rules-and-evidence.md)、[模板与演示](references/template-and-demo.md)、[封装](references/packaging.md)、[工作区与交付物](references/deliverables.md)。

## 使用

对宿主 AI 说：“复刻一下小红书博主「某某」的视频风格。”默认交付冻结风格包、留出报告、风格说明书和模板预览。

要演示时说：“用我这段录像按复刻出的风格剪一条演示，出镜的人已经同意。”

要封装时说：“把这个风格封装成 Skill。”

## 本地安装

在源码根目录运行。目标已存在时先核对，不要覆盖未知目录。

```bash
SKILL_SOURCE_DIR="$(pwd -P)"
mkdir -p "$HOME/.agents/skills" "$HOME/.claude/skills" "$HOME/.codex/skills"
ln -s "$SKILL_SOURCE_DIR" "$HOME/.agents/skills/lov-media-cloner"
ln -s ../../.agents/skills/lov-media-cloner "$HOME/.claude/skills/lov-media-cloner"
ln -s ../../.agents/skills/lov-media-cloner "$HOME/.codex/skills/lov-media-cloner"
```

也可以从 LovStudio 官网目录安装：`npx skills add lov-media-cloner -g -y`。

## 验证

```bash
SKILL_DIR="$(pwd -P)"
PY="uv run --with jsonschema --with pyyaml --with numpy --with opencv-python-headless --with pillow python"
$PY "$SKILL_DIR/scripts/cloner.py" doctor
$PY "$SKILL_DIR/scripts/test_contract.py"
python3 "$SKILL_DIR/scripts/validate_skill.py" "$SKILL_DIR"
```

契约测试用合成媒体走完整条流程，并检查每一道拒绝门：

- 冻结前封存留出；
- 拒绝留出证据和找不到的引文；
- 冻结后改动会被发现；
- 留出检验必须逐条覆盖。

## Profile

遵循 [user-profile/v1](references/user-profile.md)。本 Skill 的 records 是 `projects_root`、`logged_in_browser`、`asr`、`split`，只保存用户明确说要长期沿用的值；凭据、Cookie 与被分析博主的信息不写入 Profile。

## 组合、限制与权利

[组合记录](references/skill-composition.md)说明：

- 上游：登录态浏览器、`lov-media-crawler` 和外部转写负责前置步骤；
- 下游：`lov-skill-creator` 负责封装，`lov-skill-publisher` 只在用户要求时发布。

两者都只做文件交接。

已核实：在晓暖的研究数据上，本 Skill 的工具复现了 v0.1 冻结包（画像与证据逐字节一致）、各项测量和她的专用模板画面。

尚未核实：还没有用本 Skill 从头分析过一位新博主，也没有人工听审或盲评。字体只能近似替代；原作的剪辑软件与工程参数未知。

代码、协议与模板采用 MIT。被分析作品的原片、人像、声音、台词、截图、封面和品牌标识的权利不被转授，包内不含这些素材。本 Skill 不做换脸或声纹克隆，也不会自动发布。
