# CLI 工坊 · CLI Studio

![Version](https://img.shields.io/badge/version-0.1.1-CC785C)

把任意本地项目转换为可安装、可测试、支持稳定 JSON 输出且调用真实项目后端的 CLI。

## 本地安装

源码应由共享 Skills 中间层链接到各 Agent 运行时：

```bash
ln -s /path/to/cli-creator-skill "$SKILL_AGENTS_DIR/lov-cli-creator"
ln -s ../../.agents/skills/lov-cli-creator "$SKILL_CODEX_DIR/lov-cli-creator"
ln -s ../../.agents/skills/lov-cli-creator "$SKILL_CLAUDE_DIR/lov-cli-creator"
```

实际安装工具会拒绝覆盖已有目标。

## 输入与输出

- 输入：一个本地项目路径；省略时使用 Skill 执行所在的当前目录。
- 默认输出：目标项目内的 `agent-harness/`。
- 默认命令：`lov-cli-项目名`。
- 交付：Python CLI 包、`lov-cli.json` 契约、后端适配器、README、测试计划、
  单元测试和真实 E2E 测试。

## 使用示例

```text
给当前项目做一个 CLI
```

Skill 会分析当前目录、生成并安装 CLI，然后运行真实后端工作流和验收。

```text
Build a CLI for /path/to/project and put the harness in ./tools/project-cli
```

显式路径和输出位置优先于默认值；不会把个人绝对路径写入可移植 Skill 源码。

## 三个辅助工具

```bash
python3 scripts/inspect_project.py PROJECT --format markdown
python3 scripts/scaffold_cli.py PROJECT --plan CLI_PLAN.json
python3 scripts/validate_cli.py PROJECT/agent-harness --run-tests --require-installed
```

`scaffold_cli.py` 只创建空目标；已有 harness 应原地增量完善。

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`。只有用户明确要求长期复用的命令前缀、
输出目录约定等偏好，才通过 `scripts/profile_store.py` 原子写回共享 Profile。
项目路径、凭据和推断值不持久化。详见
[`references/user-profile.md`](references/user-profile.md)。

## 设计边界

- 生成的 CLI 调用项目真实 CLI、公共 API、协议或原生格式/渲染器。
- 每个命令同时提供人类输出和 `--json`，失败使用非零退出码。
- 至少有一个项目特定命令和一个真实 E2E 工作流。
- 本 Skill 不负责 PyPI、GitHub Release、Marketplace 或其他发布。

## 质量门

```bash
python3 scripts/test_cli_creator.py
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.9+
- 目标项目的真实运行时或可执行程序
- PyYAML（仅验证本 Skill 源码）

## License

MIT。上游方法研究与差异说明见
[`references/upstream-research.md`](references/upstream-research.md)。
