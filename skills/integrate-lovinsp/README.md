# lov-integrate-lovinsp

![Version](https://img.shields.io/badge/version-1.5.0-CC785C)

> 幂等集成 lovinsp (click-to-code) 到当前前端项目，支持从 code-inspector 迁移

## 本地安装

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)/integrate-lovinsp-skill"
ln -s "$SKILL_SOURCE_DIR" \
  "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}/lov-integrate-lovinsp"
```

## 使用

显式调用：

```
/lov-integrate-lovinsp [arguments]
```

也可由模型自动触发。典型触发语：

- 「给这个项目装上 lovinsp。」
- 「接入点击 DOM 跳转源码。」
- 「把 code-inspector 迁移成 lovinsp。」
- 由 `lov-app-generator` 等 Skill 把 Lovinsp 集成列为默认不变量时自动调用。

本 Skill 幂等：已集成则只做版本检查，重复执行无副作用，因此适合无人值守推进。

## Status

- Version: 1.5.0
- Published at `github.com/lovstudio/integrate-lovinsp-skill`
