---
name: lov-proposal
description: Generate complete business proposals for client projects from requirements.
version: 1.1.0
---

# proposal（加密 Skill）

这是 Lovstudio 的付费 Skill。安装时只会下载加密分发包；登录并用 Credits 兑换后，运行时才会按账户权益解密。

```bash
npx lovstudio skills add proposal
uvx lovstudio-skill-helper decrypt proposal
```

解密输出仅用于当前 Agent 调用，不会把源代码写入安装目录。
