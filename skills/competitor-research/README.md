# 竞品调研 · Competitor Research

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

对点名的产品、公司或开源仓库做竞品调研，交付结论先行、每个判断都能回溯到证据的报告：
差异对比、是否二次开发的血缘溯源、含金量、投资视角。

## 安装

```bash
npx skills add lov-competitor-research -g -y
```

本地源码安装：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${LOVSTUDIO_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" "$LOVSTUDIO_SKILLS_INSTALL_DIR/lov-competitor-research"
```

## 使用

直接用自然语言提问即可：

- “调研 https://github.com/OWNER-A/REPO-A 与 https://github.com/OWNER-B/REPO-B 的区别，以及前者是不是基于后者二次开发的？”
- 接着追问：“所以它的含金量？”“有投资价值吗？”
- “Compare Notion and Obsidian for a 10-person team, and tell me where each one's moat is.”

开源对象的取证脚本也可以单独运行，输出 JSON：

```bash
python3 scripts/repo_evidence.py facts OWNER/REPO OTHER/REPO --star-sample 50
python3 scripts/repo_evidence.py history ./repo --alias OldName=NewName
python3 scripts/repo_evidence.py loc ./repo --ext py
python3 scripts/repo_evidence.py lineage ./repo --source ./origin --source-all-history
```

| 子命令 | 作用 |
| --- | --- |
| `facts` | GitHub 元数据、issue/PR 数、贡献者集中度、fork/star 等比例，可选 star 抽样 |
| `history` | 起源提交、每月提交（补全零提交月份）、停更月、作者集中度、派生信号提交 |
| `loc` | 按目录的代码行数、测试占比、依赖清单 |
| `lineage` | 目标仓库全部历史中是否出现源仓库的相同文件、特有标识符或名称 |

`history` 和 `lineage` 需要全量克隆，脚本会拒绝 `--filter` 部分克隆和 `--depth` 浅克隆。

## 用户 Profile（跨 session）

在 `skill.yaml` 中声明 `user-profile/v1`，每次运行读取共享的用户、品牌、工作区与本 Skill 的长期记录。
用户明确说出的长期偏好（例如“以后竞品报告都存成 Markdown”）由 `scripts/profile_store.py` 写回
`skills.lov-competitor-research.records`。详见 [`references/user-profile.md`](references/user-profile.md)。

## 原子组合

`references/skill-composition.md` 记录了相邻 Skill 的检查结果：赛道摸底交给 `deep-research`，
单句核实交给 `lov-fact-check`，选型方案交给 `lov-dev-research` / `lov-solution-architect`。
这些都是可选的交接，不是隐藏依赖。

## 可信度卡与用户案例

- `skill-card.yaml` / `skill-card.md`：用途、风险、输出契约与维度地图。
- `cases/cases.json`：一次两个热门开源仓库的真实调研案例（已去除项目名），包含正反对照结果。
- `pricing-card.yaml`：首版免费的依据、交付边界与复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.8+（取证脚本只用标准库；校验器需要 PyYAML）
- git；`facts` 需要已登录的 `gh` CLI
- `lov-branding-consistency`

## License

MIT
