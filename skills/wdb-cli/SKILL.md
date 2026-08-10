---
name: sgc-wdb-cli
description: "自由查看与检索微信数据库中的各类数据，支持按日期、对象、关键词、数据类型与稳定记录身份精准定位，并输出适合分析和自动化处理的结构化结果。"
version: 0.1.1
---

# wdb-cli（加密 Skill）

这是 Lovstudio 的付费 Skill。安装时只会下载加密分发包；登录并用 Credits 兑换后，运行时才会按账户权益解密。

安装与兑换：

```bash
npx lovstudio skills add wdb-cli
```

解密当前 Skill：

```bash
uvx lovstudio-skill-helper decrypt wdb-cli
```

解密输出仅用于当前 Agent 调用，不会把源代码写入安装目录。
