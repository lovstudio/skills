---
name: lov-wechat-article-operator
description: 自动读取、编辑、保存并重载验证微信公众号文章；适用于“读取当前公众号文章”“替换封面”“插入这段内容”、"edit this WeChat
  article" 等需要可靠操作现有文章的任务。
version: 0.2.0
---

# wechat-article-operator（加密 Skill）

这是 Lovstudio 的付费 Skill。安装时只会下载加密分发包；登录并用 Credits 兑换后，运行时才会按账户权益解密。

安装与兑换：

```bash
npx lovstudio skills add wechat-article-operator
```

解密当前 Skill：

```bash
uvx lovstudio-skill-helper decrypt wechat-article-operator
```

解密输出仅用于当前 Agent 调用，不会把源代码写入安装目录。
