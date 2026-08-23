---
name: lov-wxmp-cracker
description: Export WeChat Official Account articles into reusable structured content.
version: 0.4.0
---

# wxmp-cracker（加密 Skill）

这是 Lovstudio 的付费 Skill。安装时只会下载加密分发包；登录并用 Credits 兑换后，运行时才会按账户权益解密。

```bash
npx lovstudio skills add wxmp-cracker
uvx lovstudio-skill-helper decrypt wxmp-cracker
```

解密输出仅用于当前 Agent 调用，不会把源代码写入安装目录。需要额外资料时，用 helper 按需解密对应相对路径。
