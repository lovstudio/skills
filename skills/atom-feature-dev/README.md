# 功能工坊 · Feature Studio

![Version](https://img.shields.io/badge/version-0.2.2-CC785C)

把一个原子功能实现为共享 SDK、CLI、REST API、前端、Profile Preset 与 Agent Skill，
并通过同一 Dashboard 验证生产、分发和运营状态。

## 本地安装

```bash
npx skills add lov-atom-feature-dev -g -y
```

本地真源开发时，`~/.agents/skills/lov-atom-feature-dev` 应指向本目录，各宿主入口再以
相对 symlink 指向共享安装位。

## 用户 Profile

`skill.yaml` 声明 `user-profile/v1`。当前请求优先于项目上下文、Skill records、共享
preferences 与用户/品牌 Profile；只有用户直接声明并要求长期沿用的值才写回 Profile。
Profile Preset 为 Feature Contract 参数提供默认值，不复制业务逻辑。

## 使用

完整开发一个原子功能：

> 把“把 Markdown 转为带目录的 PDF”完整做成 SDK、CLI、REST API、前端和 Agent Skill，
> 用户在前端保存纸张、字体和目录深度 Preset，并在 Dashboard 对比各形态结果。

输出包括 `.atom-feature/manifest.json`、共享核心、适用 surface、Preset、测试矩阵和
Dashboard 证据。

审计已有功能：

> Audit this export feature as an atom. Find duplicated rules across SDK, API,
> UI and Agent Skill, then make the dashboard show verified evidence only.

`audit` 管线只回读现状；除非请求同时要求修复，否则不改实现。

## Skill Kit

Kit 内含六个独立模块：Feature Contract、Core SDK、Distribution Surfaces、Profile
Experience、Operations、Dashboard。默认 `full` 管线按依赖顺序执行；也可运行
`surface-first`、`profile-first` 或 `audit`。

## Manifest helper

```bash
python3 scripts/atom_feature.py init --root PROJECT --id export-pdf --title "Export PDF"
python3 scripts/atom_feature.py validate --root PROJECT
python3 scripts/atom_feature.py status --root PROJECT --format markdown
```

## Companion Dashboard

Dashboard 是一个随 Skill 分发的本地 ADE-style 工作区，组织单位是 atom，而不是文件：

```bash
python3 scripts/atom_feature.py dashboard --root PROJECT
```

也可以直接打开 `dashboard/index.html` 查看只读 Demo。`file://` 模式只加载内置示例快照，
不会连接项目、执行 surface 或保存 Profile；真实工作区仍必须使用上面的 bridge 命令。

默认提供只读控制面。允许从界面运行 manifest 中声明的 surface command：

```bash
python3 scripts/atom_feature.py dashboard --root PROJECT --allow-run
```

只有需要从界面保存 Profile Preset 时再加入 `--allow-write`。Bridge 只绑定 loopback，执行
使用 argv 数组和 `shell=False`，输出会做秘密模式脱敏并写入项目自己的 `.atom-feature/runs/`。

界面包括 Overview、Contract、Run、Compare、Review、Profile inspector、Agent brief 和
底部 Console。静态前端位于 [`dashboard/`](dashboard/)，运行契约见
[`dashboard/README.md`](dashboard/README.md)。

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 scripts/atom_feature.py selftest
python3 scripts/atom_dashboard.py selftest
```

完成还要求真实目标仓库至少有一个测试向量跨两个适用 surface 得到等价结果；本 Skill
自身验证不能代替目标功能运行验证。

## 依赖

- Python 3.8+
- PyYAML，仅用于 Skill 源校验
- 目标项目已有的语言、前端、服务端和测试工具

## License

MIT
