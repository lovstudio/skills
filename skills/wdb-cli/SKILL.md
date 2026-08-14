---
name: lov-wdb-cli
description: "万能微信秘钥：使用已有密钥或已解密数据库，按日期、对象、关键词、结构与稳定记录身份精准读取本地微信数据。"
version: 0.1.2
---

# 万能微信秘钥（加密 Skill）

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
