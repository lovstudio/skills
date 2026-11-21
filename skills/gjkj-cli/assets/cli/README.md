# 共绩算力 Open API 与大模型云服务

由 cli2anything++ suanli 适配器 0.1.0 生成，共 83 个操作：Open API 81 个、大模型云服务 2 个；只读 44 个，写操作 39 个，要求请求体加密 7 个。

## 证据等级

- `documented-apifox-openapi`：官方 Apifox 公开分享中逐接口导出的 OpenAPI 片段，路径与字段未改写。来源 https://s.apifox.cn/6aa360d3-d8f2-471e-b841-3a35c33a7b7c，抓取于 2026-11-19T00:07:14+00:00。
- `documented-docs-example`：docs.suanli.cn 文档中的调用示例。
- `live-verified-token-mode`：在上面任一文档等级之上，又用真实密钥做了只读实测并返回成功，实测时间与请求、结果摘要写在该操作的 `x-evidence.liveCheck`。

已实测 14 个只读接口（2026-11-19T02:39:10Z，token 模式）：GET /api/deployment/resource/search、GET /api/storage/get_storage、GET /api/deployment/task/search、GET /api/task/deployment/search、GET /api/task/image_preheat/get_regions、GET /api/task/job/search、GET /api/job/queue/search、GET /api/billing/get_billing_record、GET /api/storage/get_regions、GET /api/storage/nas/v1/summary、GET /api/storage/nas/v1/dictionaries、GET /api/storage/nas/v1/list、POST /api/output/v2/device-output/page_list_product_single_v2、POST /api/output/v2/device_order/get_order_list_v2。其余接口仍只有文档证据，写操作都没有执行。两个网关都先校验凭据再路由，无凭据探测只证明了鉴权头名称与错误格式，记录在 `openapi.json` 的 `x-discovery.gatewayProbes`。每个操作的 `x-evidence.sources` 给出接口页地址与 sha256。

## 推断与未验证

- 下列 10 个接口的官方片段没有声明 token、version、timestamp 头，按 https://docs.suanli.cn/api-key/overview 的统一规则补上：GET /api/deployment/task/points、POST /api/output/v2/device-output/list_rent_device_single_v2、POST /api/output/v2/device-output/list_rent_device_network_v2、POST /api/output/v2/device_order/get_device_details_v2、POST /api/output/v2/device_order/buy_v2、POST /api/output/v2/auto_renew_device_config/set_auto_renew_config、POST /api/output/v2/auto_renew_device_config/delete_auto_renew_config、POST /api/output/v2/device-output/page_list_product_single_v2、POST /api/output/v2/device-output/page_list_product_network_v2、POST /api/output/v2/device_order/get_order_list_v2。
- operationId 由 path 派生；api-graph.json 中 basis 为 `parameter-name` 的边按参数名推断，`docs` 与 `apifox-description-link` 的边有文档依据。
- 没有任何接口经过带凭据的实测：两个网关都先鉴权后路由，无凭据探测只能证明鉴权头名称和错误格式。
- 所有写操作只按官方 Apifox 定义生成并标注 x-write-operation，没有在线执行。
- 裸金属 9 个接口与 GET /api/deployment/task/points 的官方片段没有声明 token、version、timestamp 头；生成物按 /api-key/overview「所有 API 请求均需在 HTTP Header 中携带鉴权参数」补上，属于推断。
- GET /api/deployment/task/points 的官方参数含必填 tenant_id，文档没有说明它从哪里获取。
- 官方 Apifox 里 2 处 method + path 各有多份接口页（/api/storage/get_storage 3 份，/api/storage/billing/get_billing_record 2 份），生成物合并为一个操作并保留每份的说明。
- 任务修改接口的说明链接到 api-296882076，该页不在公开分享的接口清单里。
- 分布式训练没有独立接口；云主机（开发机）在公开 Open API 中没有接口，只有计费查询接口提到云主机。
- 大模型云服务只收录文档出现过的 2 个接口和示例字段，其余 OpenAI 兼容参数未逐一核对。

## 文档之间的冲突

- 统一响应的提示字段：/api-key/overview 与 /api-key/rsa 写作 msg，官方 Apifox 的 IResponse 与网关实测都是 message。生成物以 message 为准，SDK 两者都读。
- 成功码：/api-key/overview 写 code 为 "0000"，/job-batch/best-practices/api-job 写 code=200。生成物以 Apifox 与 overview 的 "0000" 为准。
- 网关实测返回 A001（缺少鉴权头）、A003（token 无效或过期），这两个码不在 Apifox IResponse 的 code 枚举里。
- /api-key/rsa 的请求示例用 POST /api/deployment/task/detail 带 JSON body，官方 Apifox 定义为 GET 加 query.task_id。生成物以 Apifox 为准。
- Apifox 的 version 头在 1 个接口里类型写成 number，示例却是 1.0.0；文档说明为字符串。生成物统一为字符串。
- /llm/status-codes 说 Token 缺失返回 401；实测不带 Authorization 时 /v1/models 返回 HTTP 400、message 为「缺少用户凭证」，无效 key 才返回 401。
- /distributed-training/overview 说可以用 OpenAPI 创建和管理训练任务，但官方 Apifox 里没有分布式训练的创建或管理接口，只有 GET /api/deployment/task/points 在说明中接受 task_type=DistributedTraining。

## 认证

凭据不写入本目录任何文件，运行时从环境变量读取：

```bash
export SUANLI_TOKEN=<API 密钥>                           # Token 模式与 RSA 模式都需要
export SUANLI_PRIVATE_KEY_FILE=./private.key             # 可选：设置后自动按 RSA 模式签名
export SUANLI_PLATFORM_PUBLIC_KEY_FILE=./platform_pub.pem # 加密接口需要：平台返回的公钥
export SUANLI_LLM_API_KEY=<大模型云服务 API Key>
```

在 macOS 上也可以只存一次钥匙串，之后 CLI 与 Swagger 代理在环境变量缺失时自动读取（`SUANLI_KEYCHAIN=0` 可关闭）：

```bash
security add-generic-password -a "$USER" -s suanli-token -w     # Open API 密钥，提示输入两次，不回显
security add-generic-password -a "$USER" -s suanli-llm-key -w   # 大模型云服务 API Key
```

获取 Open API 密钥：控制台 https://console.suanli.cn/settings/key 新建密钥。团队账号下只有主账号和团队管理员能创建或删除密钥，开发者角色只能使用已有密钥调用。

获取大模型 API Key：控制台 https://console.suanli.cn/models 的 API 密钥页新建（可设过期时间与额度）。

## 资源分组

| 分组 | 操作数 | 其中写操作 |
| --- | --- | --- |
| 资源 | 2 | 0 |
| 弹性部署服务任务 | 12 | 8 |
| 镜像预热任务(申请开通) | 6 | 3 |
| Job批处理任务 | 4 | 2 |
| Job批处理任务队列 | 9 | 5 |
| 弹性部署服务/Job批处理节点 | 4 | 1 |
| 费用 | 4 | 0 |
| 存储/对象存储 | 14 | 7 |
| 存储/集群存储/存储卷 | 8 | 4 |
| 存储/集群存储/S3互传 | 7 | 4 |
| 存储/集群存储/SFTP | 2 | 2 |
| 裸金属/已购列表 | 3 | 0 |
| 裸金属/创建订单 | 3 | 3 |
| 裸金属/可购列表 | 2 | 0 |
| 裸金属/订单列表 | 1 | 0 |
| 大模型云服务 | 2 | 0 |

## CLI

```bash
node bin/lov-suanli-cli.mjs help                                   # 按分组列出全部命令
node bin/lov-suanli-cli.mjs deployment-resource-search --dry-run   # 只打印请求，不发出
node bin/lov-suanli-cli.mjs deployment-task-search --page 1 --page-size 5
node bin/lov-suanli-cli.mjs deployment-task-change-points --data '{"task_id":388,"points":1}' --confirm-write
node bin/lov-suanli-cli.mjs llm-list-models
```

命令表在启动时由随包的 `openapi.json` 构建，operationId 转 kebab-case 即命令名，83 个操作都能直接调用。查询参数用同名选项（下划线可写成连字符），请求体用 `--data '<json>'` 或 `--data @file.json`。写操作必须加 `--confirm-write` 才会发出；`--dry-run` 打印请求时凭据只显示是否已提供。

## Swagger

```bash
node swagger/server.mjs --port 4790      # 只监听 127.0.0.1
```

打开 http://127.0.0.1:4790 。页面里的 Try it out 经本地代理发出，代理从环境变量读取凭据并现场生成 timestamp 与 sign_str，浏览器里不需要也不应填写 token。代理默认拒绝写操作，确需调试写接口时加 `--allow-write`。`swagger/drilldown.html` 按分组列出全部操作与调用顺序。

## SDK

`sdk/index.mjs` 导出 `SuanliClient`：`request(method, path, {query, body, encryption})` 自动加 version、timestamp、token，提供私钥时生成 sign_str，需加密的接口用平台公钥按 244 字节分段加密后再签名；`call(operationId, {query, body})` 按生成的操作表调用任意接口；`chatCompletions()`、`listModels()` 调用大模型云服务。响应 code 不是 "0000" 时抛出 `SuanliApiError`。

## 调用顺序

`api-graph.json` 记录 25 条调用边，起点是 `deploymentResourceSearch`（资源列表，创建任务时的 resources[].mark 来自这里）。
