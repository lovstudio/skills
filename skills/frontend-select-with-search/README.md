# 搜索下拉框 · Searchable Select

![Version](https://img.shields.io/badge/version-0.1.1-CC785C)

把候选项超过 5 个的 Select 升级为可搜索、可滚动、可键盘操作的兼容组件，并专门验证 Dialog、Popover 和 Portal 组合中的真实滚轮行为。

## 本地安装

在本目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" "$SKILL_SKILLS_INSTALL_DIR/lov-frontend-select-with-search"
```

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`。Skill 每次运行都会读取用户语言、工作区和专属记录；只有用户明确要求长期保留的阈值或行为偏好，才会通过 `scripts/profile_store.py` 原子写回共享 Profile。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

### 例 1：统一升级 Select

输入：`所有的 select 组件，如果选项超过 5 个，就要支持搜索。`

输出：Select 清单、共享渐进增强组件、5/6 项边界验证，以及中文搜索、受控值和表单语义回归证据。

### 例 2：修复弹窗内无法滚动

输入：`候选项无法滚动。`

输出：先用真实滚轮复现，再定位 Dialog 滚动锁与 Popover Portal 的边界冲突；修复允许滚动的弹层归属，并验证滚动后仍可选中候选项。

## 原子组合

[`references/skill-composition.md`](references/skill-composition.md) 记录相邻 Skills、可选的上游交接和 Single Skill 决策。外部 Skills 不作为隐藏依赖。

## 可信度卡与用户案例

- `skill-card.yaml` / `skill-card.md`：用途、风险、输出和维度证据。
- `cases/cases.json`：真实 Input → Prompt → Output 案例。
- `pricing-card.yaml`：免费边界、价值依据和复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
```

真实项目验收还必须运行该项目自己的类型检查、测试或构建，并在相关 Dialog/Portal 中发送真实滚轮或触控板事件。

## 依赖

- Skill 本体：目标项目已有前端工具链
- Profile 与本地校验：Python 3.8+、PyYAML

## License

MIT
