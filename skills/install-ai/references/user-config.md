# AI 功能偏好配置

持久化的是用户可见或产品级偏好，不是密钥。每个项目的显式需求优先于本文件。

## 首次使用

1. 从当前 App 的平台、现有后端和用户需求推断默认 route。
2. 读取环境变量和共享 profile 中已有的非敏感偏好。
3. 仅在选择会改变产品体验时询问：Agent Client、MaaS、Hybrid；模型意图；是否需要 UI。
4. 向用户展示将保存的偏好后再写入 profile。

## 建议字段

```json
{
  "ai_feature": {
    "route_order": ["maas", "agent-client"],
    "model_intent": "balanced",
    "locale": "zh-CN",
    "ui_default": "infer"
  }
}
```

## 禁止保存

- API Key、访问令牌、Cookie 或登录态。
- 私有 endpoint、客户项目路径、原始提示词或用户内容。
- 只对单一项目成立的模型 ID。

将秘密交给目标项目的环境变量、密钥管理或服务端部署配置；不要写进浏览器 bundle、Skill profile 或 README。
