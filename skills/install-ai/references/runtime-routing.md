# AI 运行时路由

## 路由选择

| 运行环境 | 首选 | 原因 |
| --- | --- | --- |
| Web、移动端、多人产品 | MaaS 服务端适配器 | 密钥、配额、审计和模型路由留在服务端 |
| 本机桌面功能 | Agent Client 本地适配器或 MaaS | 可以复用用户本机 Client；仍需要缺失时的可用状态 |
| 需要统一生产行为且允许本机增强 | Hybrid | MaaS 是默认产品路径，Agent Client 是可选增强 |

## 统一合同

无论使用哪个通道，应用层都只依赖一个内部接口：

```ts
type AiIntent = 'fast' | 'balanced' | 'reasoning' | 'vision' | 'creative';

type AiRequest = {
  feature: string;
  input: unknown;
  intent: AiIntent;
};

type AiResult = {
  output: unknown;
  usage?: { inputTokens?: number; outputTokens?: number };
  requestId: string;
};
```

Adapter 负责把 intent 映射到可用模型；前端不得依赖某个供应商的原始响应结构。

## 故障语义

- Client 未安装：提示该本机增强不可用，并按路由策略尝试 MaaS 或保留可重试状态。
- MaaS 配置缺失：显示产品级配置状态，避免泄露 endpoint 或鉴权细节。
- 上游失败：返回稳定错误码和可理解的用户操作；完整诊断只进入受控日志。
- 限流与超时：保留输入，允许重试，避免重复提交和重复计费。
