---
name: lov-wdb-cli
description: "万能微信秘钥：通过隔离 DB+WAL 副本读取本地微信数据，保留精确记录身份，避免查询引擎干扰微信共享内存。"
depends_on:
  - lov-branding-consistency
version: 0.3.1
---

# 万能微信秘钥 · Universal WeChat Key

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

0.3.1：所有查询使用私有 DB+WAL 副本，复制失败不直连原库。15 项回归测试通过；微信运行中稳定性尚待实测。
