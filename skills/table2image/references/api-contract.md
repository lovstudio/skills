# Mable table image API contract

## Base URL

默认生产根地址为 `https://api.lovstudio.ai`。本地或自托管环境通过 `--api-base`、
`MABLE_API_BASE` 或 Skill Profile 覆盖；根地址末尾的 `/` 会被移除。

## Create image

`POST /mable/images`

请求头必须包含 `Authorization: Bearer <LovStudio Access Token 或 sk_live_ API Key>`。
每次成功生成扣 3 Credits；输入、鉴权、余额不足或服务端失败不扣费。同内容重复生成仍按每次调用计费。

请求体：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `markdown` | string | 是 | 标准 Markdown 表格，最多 30000 字符 |
| `model` | string | 否 | 11 位 Mable 型号，与 `layout` 互斥 |
| `layout` | object | 否 | 完整布局参数，与 `model` 互斥 |
| `caption` | string | 否 | 底部说明；空字符串隐藏 |
| `pixel_ratio` | 1 或 2 | 否 | PNG 像素倍率，默认 2 |

成功响应：

```json
{
  "image_url": "https://api.lovstudio.ai/mable/images/sha256.png",
  "format": "png",
  "width": 1520,
  "height": 344,
  "layout_width": 760,
  "model": "Asge8oUog7I",
  "credits_spent": 3,
  "credits_remaining": 97
}
```

服务端返回值是唯一事实来源；客户端不得猜测图片地址、尺寸或最终型号。

## Download image

对 `image_url` 发起 GET。成功响应的 `Content-Type` 应为 `image/png`，内容应以
PNG signature 开头。托管图片使用内容寻址，因此同一内容与同一布局可以返回同一 URL。

## Errors

- 输入错误通常返回 HTTP 422。
- 缺少或无效凭据返回 HTTP 401。
- Credits 不足返回 HTTP 402，并包含 `required` 与 `balance`。
- 图片不存在返回 HTTP 404。
- 服务端或持久化异常返回 5xx。
- 客户端错误信息保留状态码和最多 800 字符的响应摘要，不输出请求之外的环境配置。

## Layout JSON

`layout` 直接传给 Mable API。Skill 不在本地复制服务端默认值、约束规则或求解算法，
以避免客户端与服务端版本漂移。
