# Skill 透视镜 · Skill Lens

![Version](https://img.shields.io/badge/version-0.6.1-CC785C)

把一个本地 Agent Skill 转成证据驱动的单文件信任审阅页、带源码行号证据的
内部运行图与 JSON 逻辑模型。重点不是“画出流程”，而是判断 Skill 声明了什么、
依据在哪里、如何验收，以及哪些真实效果仍未被案例证明。

## 本地安装

推荐让各 Agent 的安装入口共同指向一个用户级 canonical link：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "$HOME/.agents/skills" "$HOME/.codex/skills" "$HOME/.claude/skills"
ln -s "$SKILL_SOURCE_DIR" "$HOME/.agents/skills/lov-skill-visualizer"
ln -s ../../.agents/skills/lov-skill-visualizer \
  "$HOME/.codex/skills/lov-skill-visualizer"
ln -s ../../.agents/skills/lov-skill-visualizer \
  "$HOME/.claude/skills/lov-skill-visualizer"
```

## 用户 Profile（跨 session）

每个生成的 Skill 都会在 `skill.yaml` 中声明 `user-profile/v1`，并从共享
Profile 读取用户、品牌、工作区和本 Skill 的长期记录。用户直接说出的持久
偏好或品牌事实由 `scripts/profile_store.py` 写回 Profile；源代码保持可移植。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

输入可以是 Skill 目录，也可以直接是 `SKILL.md`：

```bash
python3 scripts/visualize_skill.py ../skill-creator-skill \
  --output output/skill-creator-logic.md \
  --json output/skill-creator-logic.json \
  --language zh \
  --strict
```

指定 `--output output/name.md` 时会同时生成 `output/name.html`。HTML 先回答一个
具体问题：什么场景值得启动这个 Skill。随后用一次连续滚动展示使用前状态、内部
转化链、使用后结果、不可替代性、非适用边界与可信边界；不要求点击节点、拖图、
缩放或切换面板才能理解。触发匹配属于宿主外部路由，不进入内部主逻辑。

审阅页默认采用简约克制、场景先行的结构。Mermaid 11.12.2 仍然实际渲染内部
运行、资源关系和 Kit 管线，但统一收进末尾的技术复核层；外部触发边界、源码、
资源与 JSON 也在这里按需展开。所有样式、运行时、Mermaid 源码和完整 JSON 均
内嵌，不依赖网络。中文报告尽量使用中文；文件名、路径、Skill ID、命令、源码和
Mermaid 语法保持原文。

Markdown 默认包含内部运行图、资源与依赖关系；Skill Kit 还会生成模块管线图。
JSON 使用 `lovstudio/skill-logic/v1`，新增逐步细节、模块子流程、质量门与 trust
证据层，可继续交给 SVG、图数据库或目录渲染器。

横向图和浅层引用扫描：

```bash
python3 scripts/visualize_skill.py /path/to/SKILL.md \
  --direction LR \
  --max-depth 1 \
  --output skill-flow.md
```

没有 `--output` 时，Markdown 写到标准输出，除非另行传入 `--html`，否则不会
推断 HTML 路径。`--strict` 在发现缺失流程或资源时返回退出码 3，但仍保留已经
提取的审阅页、报告和 JSON 供修复使用。

## 提取边界

- 单独提取外部触发边界；内部运行图只包含 Skill 启动后的步骤和条件。
- 提取步骤全文、Kit 模块子流程、质量门、Profile、依赖与本地资源。
- 所有关键逻辑保留 Skill 相对路径与行号；报告不泄漏 canonical 绝对路径。
- 区分“有声明”“有能力依据”“有验收规则”和“真实效果已观察”；不执行目标
  Skill 时绝不把静态完整度写成运行效果。
- 细节见 [`references/logic-model.md`](references/logic-model.md)。

## 原子组合

每个新 Skill 都带有 `references/skill-composition.md`。它记录已检查的相邻
Skills、可选的上游/下游交接、重叠处理，以及为何选择 Single Skill 或自包含
Skill Kit；外部 sibling Skill 不作为隐藏依赖。

## 可信度卡与用户案例

每个新 Skill 都必须随源代码提供：

- `skill-card.yaml` / `skill-card.md`：用途、负责人、依赖、风险、输出与维度地图。
- `cases/cases.json`：至少一个真实的 Input → Prompt → Output 案例。
- `pricing-card.yaml`：免费或付费都要写清价值锚点、交付边界和复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
python3 scripts/visualize_skill.py . --strict >/tmp/lov-skill-visualizer-self.md
```

## 依赖

- Python 3.8+
- PyYAML
- 外置 Mermaid 渲染器、网页框架和网络连接都不是生成产物的必要依赖
- HTML 内嵌 vendored Mermaid 11.12.2；许可与来源见
  [`assets/vendor/README.md`](assets/vendor/README.md)

## License

MIT
