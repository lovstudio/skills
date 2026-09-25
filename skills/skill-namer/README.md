# Skill 命名大师 · Skill Naming Master

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

为单个或整组 Skill 找到准确、简短、优雅、一致的名字。保留已认可的好名字，
让中英文名称贴合真实能力，并生成可交给维护和发布流程的命名清单。

## 使用

```text
$lov-skill-namer 给这个 Skill 起名：它根据能力说明，审查单个或整组 Skill 的中英文名称。
$lov-skill-namer 参考“汉字镜、BP 大师、人人字幕”的风格，审查这份 Skill 清单。
$lov-skill-namer “GitHub 仓库信息”适合一个优化仓库简介的 Skill 吗？
```

单个起名给一个最佳推荐和简短理由；批量审查记录每项修改或保留的依据，区分用户
认可与编辑建议。示例名称展示一种可选风格，不覆盖用户自己的命名偏好。

“GitHub 仓库简介优化”保留具体任务，“汉字镜”保留产品意象，“PDF大师”保留
已认可的拼写。整组一致不要求每个名字都叫“助手”或“大师”。

## 本地安装

在本仓库根目录执行；若目标已存在，先核对其真实来源，不覆盖：

```bash
export SKILL_SOURCE_DIR="$(pwd -P)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" "$SKILL_SKILLS_INSTALL_DIR/lov-skill-namer"
```

安装 `lov-branding-consistency` 以完成最终文案门禁。核心命名使用宿主语言能力，
离线审计与 Profile 需要 Python 3.8+；源码校验另需 PyYAML。

## 清单校验

输入合同见 [结果清单](references/review-contract.md)。

```bash
python3 scripts/audit_names.py cases/evidence/catalog-review.json
python3 scripts/audit_names.py cases/evidence/self-naming-review.json
python3 scripts/validate_skill.py .
```

审计只读，报告写到标准输出。它检查完整覆盖、重复名称、锁定名称和结构问题，
不打审美分、不修改 Skill，也不发布内容。

## 用户 Profile

`skill.yaml` 声明 `user-profile/v1`。共享 Profile 提供语言、品牌语气及本 Skill 的
长期命名偏好；当前请求优先。仅直接陈述且希望跨任务保留的偏好可通过
`scripts/profile_store.py` 写入。详见 [Profile 合同](references/user-profile.md)。

## 能力组合与证据

- [能力组合](references/skill-composition.md)：创建、命名、精修、发布之间的交接。
- [Skill Card](skill-card.md)：适用范围、维度、风险与分发状态。
- [真实案例](cases/cases.json)：历史批量命名及本 Skill 自身命名的输入与结果。
- [定价说明](pricing-card.yaml)：当前免费，宿主模型成本由使用者承担。

当前版本已创建并验证本地源码；尚未发布到远程渠道。

## License

MIT，见 [LICENSE](LICENSE)。名称示例仅用于说明方法，不声明商标权或可注册性。
