# uni-app 网关调用层封装约定

参考：DCloud uni-app 项目（根目录含 `pages.json` 与 `manifest.json`）。目标是把网关调用集中到
一个 `api/` 目录，页面只 import 端点函数，不直接碰 `uni.request`。

## 目录结构（推荐）

```text
src/
├── api/
│   ├── config.ts      # baseURL 与 token 存取 key 集中配置
│   ├── request.ts     # uni.request 的 Promise 化封装
│   ├── types.ts       # 网关响应 / 错误类型
│   ├── llm.ts         # 按后端端点清单生成的模块化 API
│   └── account.ts     # …
└── pages/…
```

## request 封装要点

```ts
// api/request.ts —— 骨架
const TOKEN_KEY = 'token'

export function request<T>(path: string, options: {
  method?: 'GET' | 'POST' | ...
  data?: unknown
  auth?: boolean        // 是否注入 token，默认 true
} = {}): Promise<T> {
  return new Promise((resolve, reject) => {
    const token = uni.getStorageSync(TOKEN_KEY)
    uni.request({
      url: `${config.baseURL}${path}`,
      method: options.method ?? 'GET',
      data: options.data,
      header: {
        'Content-Type': 'application/json',
        ...(options.auth && token ? { Authorization: `Bearer ${token}` } : {}),
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data as T)
        else reject(normalizeError(res))     // 统一错误，携带可复制上下文
      },
      fail: (err) => reject(normalizeError(err)),
    })
  })
}
```

要点：
- **baseURL**：集中在 `api/config.ts`，dev/prod 按环境区分，不散落在页面。
- **token**：从 `uni.getStorageSync(key)` 读取，支持自定义 getter；401 统一回调刷新或跳登录。
- **错误提示**：非 2xx 或网关错误结构（如 uni-api `standard_error_handler` 返回的 `detail`）
  统一抛错；报错 UI 带「复制」按钮，并携带 `context_id` / `requestId` 等便于 debug 的字段。
- **流式（按需）**：SSE 端点用 `uni.request` 的 `enableChunked` 或事件源适配器封装，页面无需关心。

## 端点模块

按后端端点清单生成，一个端点一个函数：

```ts
// api/llm.ts
import { request } from './request'
export function callBase(body: { messages: unknown[]; model: string }) {
  return request<unknown>('/llm/base', { method: 'POST', data: body })
}
```

## 语言

- TS 工程生成 `.ts` 并写 `types.ts`；JS 工程生成 `.js`，类型注释可省。

## 验收

- request 封装可被页面 import 后正常调用；错误提示可复制且含上下文。
- 导出函数与后端端点清单一一对应。
