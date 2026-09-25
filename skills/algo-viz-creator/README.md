# 算法演示台 · Algorithm Theater

![Version](https://img.shields.io/badge/version-0.1.1-CC785C)

为算法、数据结构、流程或任何信息对象生成「逐步演示」的可交互可视化。
输入：算法名或概念描述。输出：自包含单文件 HTML，支持播放/暂停、逐帧前进
后退、变速与键盘演示，每帧附一句中文解说与伪代码高亮。离线可开，双击即演示。

## 本地安装

本 Skill 通过 Lovstudio 三层 symlink 链安装（真源 → `~/.agents/skills` →
`~/.claude/skills`），`readlink -f` 应解析到真源：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
ln -s "$SKILL_SOURCE_DIR" ~/.agents/skills/lov-algo-viz-creator
ln -s ../../.agents/skills/lov-algo-viz-creator ~/.claude/skills/lov-algo-viz-creator
```

## 用户 Profile（跨 session）

每个生成的 Skill 都会在 `skill.yaml` 中声明 `user-profile/v1`，并从共享
Profile 读取用户、品牌、工作区和本 Skill 的长期记录。用户直接说出的持久
偏好或品牌事实由 `scripts/profile_store.py` 写回 Profile；源代码保持可移植。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

核心工作流（详见 `SKILL.md`）：

1. 把算法翻译成帧模型 JSON（schema 见 `references/step-model.md`）。
2. 校验：`python3 scripts/validate_viz.py model.json`
3. 生成：`python3 scripts/build_viz.py model.json -o output/demo.html`

真实示例：

- **二分查找**（sequence）：7 节点、4 帧，目标 23。`validate_viz.py` 0 error，
  产物在浏览器中渲染出节点、STEP 徽标与解说文本。
- **拓扑排序**（network）：6 节点、6 条有向边、7 帧，settledEdges 随帧累积，
  headless Chrome 渲染出箭头与高亮。
- **冒泡排序**（bars）：5 根柱子、13 帧，active/settled 高亮，柱高随帧变化。

三个示例模型内置在 [`examples/`](examples/)，可直接跑
`python3 scripts/build_viz.py examples/binary-search.json` 体验完整链路。

## 原子组合

`references/skill-composition.md` 记录了已检查的相邻 Skills、可选交接与
重叠处理。本 Skill 为 Single Skill，不需要 Kit 拆分。

## 可信度卡与用户案例

- `skill-card.yaml` / `skill-card.md`：用途、负责人、依赖、风险、输出与维度地图。
- `cases/cases.json`：两个真实 Input → Prompt → Output 案例（二分查找 /
  拓扑排序与冒泡排序）。
- `pricing-card.yaml`：免费，教学演示用途；进入商业培训时复评。

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 scripts/validate_viz.py examples/binary-search.json   # 有示例时
```

## 依赖

- Python 3.8+（运行 `validate_viz.py` / `build_viz.py`）
- PyYAML（仅 `validate_skill.py` 需要）
- 产物不需要 npm / 构建 / 外部 CDN

## License

MIT
