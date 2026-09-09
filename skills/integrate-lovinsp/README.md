# Lovinsp 接入 · Lovinsp Setup

![Version](https://img.shields.io/badge/version-1.6.4-CC785C)

> 幂等集成 lovinsp (click-to-code) 到当前前端项目，支持从 code-inspector 迁移

## 本地安装

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
ln -s "$SKILL_SOURCE_DIR" \
  "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}/lov-integrate-lovinsp"
```

## 使用

显式调用：

```
使用 lov-integrate-lovinsp 完成以下任务：<任务目标、输入和约束>
```

也可由模型自动触发。典型触发语：

- 「给这个项目装上 lovinsp。」
- 「接入点击 DOM 跳转源码。」
- 「把 code-inspector 迁移成 lovinsp。」
- 由 `lov-app-generator` 等 Skill 把 Lovinsp 集成列为默认不变量时自动调用。

本 Skill 幂等：已集成则检查版本与默认交互，重复执行无副作用，因此适合无人值守推进。

## 默认交互

默认顺序固定为 **Copy Path → Open in IDE**，优先使用 Lovinsp 原生默认配置。

| 操作 | Mac | Windows / Linux |
| --- | --- | --- |
| Copy Path（默认） | Option + Shift + 点击 | Alt + Shift + 点击 |
| Open in IDE | Option + Shift + Command + 点击 | Alt + Shift + Ctrl + 点击 |

不得因“点击定位源码”的任务描述而擅自交换按键。集成和幂等检查都需核对配置、运行态与说明文案。

## Status

- Version: 1.6.4
- Published at `github.com/lovstudio/integrate-lovinsp-skill`

## 官网安装

```bash
npx -y lovstudio@latest skills add integrate-lovinsp
```
