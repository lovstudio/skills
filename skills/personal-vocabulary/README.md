# lov-personal-vocabulary

![Version](https://img.shields.io/badge/version-0.2.0-CC785C)

把散落在各语音输入法里的个人词条收敛成一份规范词汇表，并映射回 OpenLess、Typeless 等 App；按 phrase 去重、产出只读同步计划，确认后再写入。

## 本地安装

```bash
export SKILL_SOURCE_DIR="$(pwd)"
export SKILL_SKILLS_INSTALL_DIR="${SKILL_SKILLS_INSTALL_DIR:-$HOME/.agents/skills}"
ln -s "$SKILL_SOURCE_DIR" "$SKILL_SKILLS_INSTALL_DIR/lov-personal-vocabulary"
```

按 Lovstudio 三层链约定补中间层：

```bash
ln -s "$SKILL_SOURCE_DIR" "$HOME/.agents/skills/lov-personal-vocabulary"
ln -s "../../.agents/skills/lov-personal-vocabulary" "$HOME/.claude/skills/lov-personal-vocabulary"
```

## 用户 Profile（跨 session）

在 `skill.yaml` 声明 `user-profile/v1`，从共享 Profile 读取用户、品牌、工作区与本 Skill 长期记录。用户直接说出的持久偏好由 `scripts/profile_store.py` 写回；源码保持可移植。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

```bash
# 建规范词库
python3 scripts/vocab_cli.py init --canonical vocabulary.json

# 从 OpenLess 词库导入并去重
python3 scripts/vocab_cli.py merge --canonical vocabulary.json --import openless-dictionary.json --from-app openless

# 生成 OpenLess 格式文件
python3 scripts/vocab_cli.py render --app openless --canonical vocabulary.json --output out.json

# 对比规范词库与某 App 词条，产出同步计划
python3 scripts/vocab_cli.py diff --app openless --canonical vocabulary.json --app-file openless-dictionary.json
```

## 原子组合

本 Kit 为自包含三模块：`canonical-store`（规范词库）、`app-adapters`（各 App 映射）、`sync-plan`（差异计划）。外部 sibling Skill 不作为隐藏依赖。详见 [`references/skill-composition.md`](references/skill-composition.md)。

## 可信度卡与用户案例

- [`skill-card.yaml`](skill-card.yaml) / [`skill-card.md`](skill-card.md)：用途、负责人、依赖、风险、输出与维度地图。
- [`cases/cases.json`](cases/cases.json)：真实 OpenLess 21 条词库跑完整流水线。
- [`pricing-card.yaml`](pricing-card.yaml)：免费，价值锚点与交付边界。

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.9+（仅标准库）
- 用户授权访问本机词库文件或账号凭据

## License

MIT
