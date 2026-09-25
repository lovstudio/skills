# Agent 对话界面 · Agent Chat UI

![Version](https://img.shields.io/badge/version-0.1.1-CC785C)

把 Agent 对话记录、工具过程、状态、Markdown、交互问题和输入区快速接入现有 React Native/Expo 或 React 应用。

## 本地安装

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" \
  "$SKILL_SKILLS_INSTALL_DIR/lov-integrate-agent-uiux"
```

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`。Skill 每次读取用户、品牌、工作区、共享偏好和 Skill 专属记录；只有用户明确要求长期保留的事实才由 `scripts/profile_store.py` 原子写回。

## 使用

审计目标项目：

```bash
python3 scripts/agent_uiux.py audit /path/to/project --format json
```

预览并生成组件：

```bash
python3 scripts/agent_uiux.py scaffold /path/to/project --dry-run
python3 scripts/agent_uiux.py scaffold /path/to/project
python3 scripts/agent_uiux.py verify /path/to/project
```

示例触发语：

- “给这个 Expo 应用接入 AI 对话 UI，包含工具调用折叠、Markdown 和发送失败重试。”
- “Integrate reusable agent conversation components into this React dashboard.”

默认生成位置为 `src/components/agent-uiux`；脚手架拒绝覆盖已有目录。React Native 与 React Web 使用同一份消息/状态契约，平台组件独立实现。

## 组件能力

- `AgentConversation`：受控的完整对话面板。
- `AgentTranscript`：用户、助手、工具、状态及待回答交互。
- `AgentComposer`：草稿、附件入口、发送、失败保留与重试。
- `types.ts` / `model.ts` / `markdown.ts`：平台无关契约与纯函数。
- `theme.ts`：宿主品牌 token 映射，不把 Yoda 品牌写死在模板里。

## 原子组合

[`references/skill-composition.md`](references/skill-composition.md) 记录了与 app generator、mobile adaptation、frontend design 和 LLM integration 的边界。它们都是可选交接，不是隐藏依赖。

## 可信度与案例

- [`skill-card.yaml`](skill-card.yaml) / [`skill-card.md`](skill-card.md)
- [`cases/cases.json`](cases/cases.json)
- [`pricing-card.yaml`](pricing-card.yaml)

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 scripts/agent_uiux.py self-test
```

## 依赖

- Python 3.8+
- 目标项目：React Native/Expo 或 React + TypeScript
- Skill 校验：PyYAML

## License

MIT
