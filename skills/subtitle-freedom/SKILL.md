---
name: lov-subtitle-freedom
description: Create learner-friendly English subtitles with level-aware glosses and optional spoiler-safe subtitle sidecars.
version: 1.2.8
---

# subtitle-freedom (encrypted)

这是一个 Lovstudio 付费 Skill。安装命令会在兑换 Credits 后下载加密包；使用时由本地 helper 按当前账户权益解密到内存。

```bash
npx lovstudio skills add subtitle-freedom
uvx lovstudio-skill-helper decrypt subtitle-freedom
```

每次使用都会重新校验账户权益，不会把解密后的 Skill 写回磁盘。
