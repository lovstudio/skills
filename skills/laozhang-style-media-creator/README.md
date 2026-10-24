# 老张心理风格短视频

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

`lov-laozhang-style-media-creator`：将参考作品中的解释路径、叙事、口语、声音、画面、字幕和剪辑转化为有证据的创作协议，再以新选题生成脚本与制作计划。

## 已包含

- 10条公开参考作品的来源、哈希和测量，8条训练、2条留出。
- 8个维度、23条规则、157条带时间证据；规则与题材、身份及未经验证的观点分离。
- 4种叙事模板、3种画面布局、条件式声画触发。
- 可独立交给另一个AI的 [风格JSON](assets/laozhang-v0.1/style-profile.json) 与 [证据](assets/laozhang-v0.1/evidence.jsonl)。
- [96秒新选题案例](cases/new-topic/script.md)：虚构情境，不对应真实人物；包含事实台账、分镜、58条字幕与可验证时间线，尚未拍摄或渲染。

## 使用

对宿主AI说：“用老张心理风格，基于这些事实，把这个选题做成90秒口播脚本、分镜和剪辑计划。使用我的出镜与声音，不加服务CTA。”

重新提取时说：“基于这些已授权视频，更新风格包，保留证据、例外和未参与规则选择的留出样本。”

生成阶段只需宿主AI，不依赖一个固定云服务账号。画像描述的是可迁移表达方法，不代表作者授权或背书。

## 本地安装

在源码根目录运行下列命令。目标已存在时应先核对，不覆盖未知目录。

```bash
SKILL_SOURCE_DIR="$(pwd -P)"
mkdir -p "$HOME/.agents/skills" "$HOME/.codex/skills"
ln -s "$SKILL_SOURCE_DIR" "$HOME/.agents/skills/lov-laozhang-style-media-creator"
ln -s ../../.agents/skills/lov-laozhang-style-media-creator "$HOME/.codex/skills/lov-laozhang-style-media-creator"
```

不要把API密钥写入源码或安装包。其他宿主可将其Skill入口链接到同一canonical安装目录。

## 验证与交接

```bash
SKILL_DIR="$(pwd -P)"
uv run --with jsonschema --with pyyaml python "$SKILL_DIR/scripts/style_media.py" doctor
uv run --with jsonschema --with pyyaml python "$SKILL_DIR/scripts/style_media.py" validate-profile
uv run --with jsonschema --with pyyaml python "$SKILL_DIR/scripts/style_media.py" validate-plan \
  --brief "$SKILL_DIR/cases/new-topic/brief.json" \
  --plan "$SKILL_DIR/cases/new-topic/edit-plan.json"
python3 "$SKILL_DIR/scripts/validate_skill.py" "$SKILL_DIR"
```

`prompt --brief BRIEF --output OUTPUT_JSON` 生成供宿主AI消费的输入包，不将准备提示词伪称为成片。制作交接和验收见 [创作协议](references/creation-protocol.md)。

## Profile

遵循 [user-profile/v1](references/user-profile.md)，每次读取当前用户/品牌/工作区与本Skill records。只保存用户明确声明的长期偏好，不保存凭据、原始私聊或推断出的个人特征。

## 组合、限制与权利

[组合记录](references/skill-composition.md) 区分下载、转写、风格迁移、实际制作和发布；它们只通过明确文件交接。完整 [分析协议](references/analysis-protocol.md) 说明采样和测量范围。

音视频量化来自全片扫描；听感是每片3段各15秒的抽样，画面是每片12帧。精确字体和原始工程参数未知。自动校验不等于人类盲评、用户认可或风格百分百一致。

代码与原创协议采用MIT；原片、人物照片、台词、音乐、节目水印等原始权利不被转授。附图用于本地证据分析，不作为新作品的已授权素材。没有默认声纹/人脸克隆，没有默认发布行为。
