# 晓暖说媒风格短视频

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

`lov-xiaonuan-style-media-creator`：把小红书博主「晓暖（清醒择偶）说媒」直播连麦切片的推理方式、叙事结构、口语招式和包装模板，转成有证据的创作协议与可渲染模板，再用于你自己的连麦录像或新选题。

## 已包含

- 12 条公开参考作品的来源、哈希与测量，10 条训练、2 条留出，分析前冻结拆分。
- 8 个维度、32 条规则、219 条带时间码的证据；引文均为转写原文的精确子串。
- 5 种叙事模板（连麦个案、个案转观点、编号作答、单人讲机制、服务介绍结构）与 4 种布局。
- 包装参数：顶部双行黄白粗斜标题、76.6% 高度单行粗宋体字幕、资料卡、右下连麦头像窗、彩条加 1 kHz 分隔。
- [风格 JSON](assets/xiaonuan-v0.1/style-profile.json)、[证据](assets/xiaonuan-v0.1/evidence.jsonl)、[留出报告](assets/xiaonuan-v0.1/holdout-report.json)。
- [Remotion 模板](templates/remotion/README.md)与出片脚本：`build_audio.py`（人声拼接、提示音、两遍响度）、`build_render_plan.py`（剪辑计划转渲染数据）。
- [演示案例](cases/yiqimao-demo/style-review.json)：用《易七猫对话手工川》素材重剪的 72.5 秒成片计划、校验与质检记录。

## 使用

对宿主 AI 说：“用晓暖的风格，把这段连麦录像剪成 5 分钟的切片；来访者已经书面同意，只露头像。”

只要方案时说：“按晓暖说媒的连麦切片包装，给‘35 岁程序员想做一人公司’写脚本和剪辑计划，标成虚构演示。”

## 本地安装

在源码根目录运行。目标已存在时先核对，不覆盖未知目录。

```bash
SKILL_SOURCE_DIR="$(pwd -P)"
mkdir -p "$HOME/.agents/skills" "$HOME/.claude/skills" "$HOME/.codex/skills"
ln -s "$SKILL_SOURCE_DIR" "$HOME/.agents/skills/lov-xiaonuan-style-media-creator"
ln -s ../../.agents/skills/lov-xiaonuan-style-media-creator "$HOME/.claude/skills/lov-xiaonuan-style-media-creator"
ln -s ../../.agents/skills/lov-xiaonuan-style-media-creator "$HOME/.codex/skills/lov-xiaonuan-style-media-creator"
```

也可以从 LovStudio 官网目录安装：`npx skills add lov-xiaonuan-style-media-creator -g -y`。

## 验证

```bash
SKILL_DIR="$(pwd -P)"
uv run --with jsonschema --with pyyaml python "$SKILL_DIR/scripts/style_media.py" doctor
uv run --with jsonschema --with pyyaml python "$SKILL_DIR/scripts/style_media.py" validate-profile
uv run --with jsonschema --with pyyaml python "$SKILL_DIR/scripts/style_media.py" validate-plan \
  --brief "$SKILL_DIR/cases/yiqimao-demo/brief.json" \
  --plan "$SKILL_DIR/cases/yiqimao-demo/edit-plan.json"
uv run --with jsonschema --with pyyaml python "$SKILL_DIR/scripts/test_contract.py"
python3 "$SKILL_DIR/scripts/validate_skill.py" "$SKILL_DIR"
```

## Profile

遵循 [user-profile/v1](references/user-profile.md)，每次读取当前用户、品牌、工作区与本 Skill records。只保存用户明确声明的长期偏好，比如栏目名、定位关键词、标题字体；不保存凭据、私聊或来访者信息。

## 组合、限制与权利

[组合记录](references/skill-composition.md)区分下载、转写、风格迁移、出片与发布，它们只通过明确的文件交接。[分析协议](references/analysis-protocol.md)说明采样、测量与留出纪律。

转写来自本机 Whisper large-v3，专名有误听并按原样保留；说话人由阅读判断；没有人工听审或盲评。字体为近似替代，原作的剪辑软件与工程参数未知。

代码与原创协议采用 MIT。原片、人像、声音、台词、截图、封面和品牌标识的权利不被转授，包内不含这些素材。来访者须书面同意并只露头像；没有默认的人脸或声纹克隆，也没有默认发布行为。
