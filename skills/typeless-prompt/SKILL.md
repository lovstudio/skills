---
name: lov-typeless-prompt
description: 把 ASR 转写或带改口的口述草稿整理成简洁、逻辑清楚、层次舒展、可直接发送给 AI 的正文，并删除口癖、重复与被否定的旧版本。
version: 0.1.0
---

# 手工川工作室 Typeless 复刻版（加密 Skill）

这是手工川工作室通过 LovStudio 发布的付费 Skill。安装时只会下载加密分发包；登录并用 Credits 兑换后，运行时才会按账户权益解密。

安装与兑换：

```bash
npx lovstudio skills add typeless-prompt
```

解密当前 Skill：

```bash
uvx lovstudio-skill-helper decrypt typeless-prompt
```

把解密输出当作当前 Skill 的真实 `SKILL.md` 阅读并执行。解密输出仅用于当前 Agent 调用，不会把源代码写入安装目录。

如果真实指令引用 `references/`、`scripts/` 或其他相对路径，请按需解密对应文件：

```bash
uvx lovstudio-skill-helper decrypt typeless-prompt references/typeless-contract.md
```

需要 `lovstudio-skill-helper >= 0.9.0`。不要缓存解密结果，也不要把解密内容写回安装目录。
