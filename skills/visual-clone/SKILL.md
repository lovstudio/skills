---
name: lov-visual-clone
description: 'Analyze a reference design image and extract visual DNA — layout, style,
  color palette, texture, typography, copy tone, spacing, etc. — into a structured,
  reusable replication prompt that can be applied to new scenarios. Trigger when:
  user provides a reference image and asks to "extract style", "replicate this", "clone
  this design", "analyze this visual", "generate a replication prompt", "提取设计要素",
  "复刻这个风格", "分析这张图", "视觉克隆".'
version: 1.1.0
---

# visual-clone（加密 Skill）

这是 Lovstudio 的付费 Skill。安装时只会下载加密分发包；登录并用 Credits 兑换后，运行时才会按账户权益解密。

安装与兑换：

```bash
npx lovstudio skills add visual-clone
```

解密当前 Skill：

```bash
uvx lovstudio-skill-helper decrypt visual-clone
```

解密输出仅用于当前 Agent 调用，不会把源代码写入安装目录。
