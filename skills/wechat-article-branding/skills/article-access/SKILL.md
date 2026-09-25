---
name: lov-wechat-branding-article-access
description: >
  获取微信公众号文章的真实正文、结构、元数据和封面，并提供安全写回入口；用于 Branding 管线中的“读取当前文章”或 "acquire this WeChat article" 阶段。
license: MIT
metadata:
  author: contributors
  version: "0.1.1"
  tags:
    - wechat
    - article-access
    - browser-automation
  compatibility: "Embedded module for lov-wechat-article-branding-skill; authenticated browser automation required."
  dependencies: []
---

# 文章读取 · Article Access

为 Branding 管线取得真实文章状态，并在下游产物完成后提供可验证的写回路径。

## Triggers

### Activate when

- Branding 管线要求“读取当前公众号文章”“取得正文和封面”。
- 用户明确要求从当前微信公众号编辑器获取真实内容。
- The pipeline asks to "acquire this WeChat article" before content or brand work.

### Do not activate when

- 已经有同一版本的完整文章状态且页面未变化。
- 用户只提供离线 Markdown，不需要微信公众号页面。

## Workflow (MANDATORY)

1. 优先调用已安装的 `lov-wechat-article-operator`。
2. Operator 不可用时，选择能复用登录状态并隔离任务空间的浏览器适配器。
3. 读取标题、摘要、正文 HTML 与文本、章节、图片、封面、字数和保存状态。
4. 形成内部文章状态，记录必须保持不变的字段。
5. 返回给下游模块；不要把登录凭据、编辑令牌和私有 URL 放入产物。
6. 写回阶段执行最小变更，保存并重载后重新采集状态。

## Output contract

输出必须足够支持：

- 内容智能理解文章；
- 封面模块建立视觉命题；
- 品牌模块选择相关公开事实；
- 质量门比对预期变化。

## Validation

- 正文文本与页面可见内容一致。
- 标题、摘要和封面来自当前页面，不来自旧聊天记录。
- 保存后的状态经过重载。

## Dependencies

`lov-wechat-article-operator` 优先；缺少时使用当前运行时可用的已登录浏览器自动化能力。

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
