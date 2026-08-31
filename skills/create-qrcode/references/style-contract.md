# QR Style and Verification Contract

## Resolution order

每次运行按以下顺序解析每个字段：

1. 当前请求和 CLI flag；
2. 当前项目上下文；
3. `skills.lov-create-qrcode.records`；
4. 共享 `preferences`；
5. 共享品牌 Profile；
6. 安全默认值。

当前请求只覆盖被明确指定的字段，不能让一个 flag 清空其余已保存偏好。

## Safe defaults

- `palette`: `classic`
- `shape`: `rounded`
- `size`: `768`
- `error_correction`: `M`
- `border`: `4`
- `poster`: `false`
- `show_data`: `false`

这些是可移植、安全的 fallback，不代表任何用户的长期偏好。

`poster=false` 是输出边界：默认只有码本体，不带 header、footer、标题、说明、海报
边框或载荷明文。只有当前请求明确需要这些呈现元素时才能覆盖；品牌名称或品牌资料的
存在本身不构成启用海报的理由。

## Built-in palettes

| ID | Foreground | Background | Meaning |
| --- | --- | --- | --- |
| `classic` | `#181818` | `#F9F9F7` | Warm Academic 炭黑与暖白 |
| `clay` | `#CC785C` | `#F9F9F7` | Warm Academic 陶土色 |
| `ink` | `#181818` | `#F0EEE6` | 炭黑与燕麦米色 |
| `olive` | `#5B6A3B` | `#F9F9F7` | 橄榄青绿与暖白 |

自定义色必须为 6 位十六进制，并满足最低 3.0 对比度；只有显式
`--allow-low-contrast` 才能越过对比度闸门，且仍需扫码回读。

## Shape presets

- `square`: 方形模块和定位点，兼容性最高。
- `dots`: 圆形模块与定位点。
- `rounded`: 圆角数据模块与标准方形定位点，品牌化与可靠性平衡。
- `extra-rounded`: 最大圆角数据模块，定位点仍保持标准方形以保护扫码率。
- `gapped-square`: 带间隙的方形模块。
- `vertical-bars` / `horizontal-bars`: 条形模块；交付前必须扫码验证。

## Error correction and logo

- `L`、`M`、`Q`、`H` 分别提供递增的冗余。
- 默认 M；打印、易污损场景优先 Q 或 H。
- 嵌入 Logo 时必须使用 H，Logo 宽度不得超过二维码宽度的 20%。
- 高纠错会增加模块密度，不等于任意裁切、遮挡或低对比度都安全。

## Privacy

- CLI 的 JSON 只返回载荷字节数与 SHA-256，不回显载荷。
- 私密内容从 stdin 或权限受控的输入文件传入。
- `--show-data` 会把原始载荷绘制到海报，必须由用户显式启用。
- 不把载荷、Wi-Fi 密码、token 或一次性内容保存到 Profile、案例或日志。

## Acceptance levels

- `off`: 只完成编码和原子写入，不建议用于交付。
- `structure`: 回读 PNG、尺寸、颜色与非空像素，只证明文件结构成立。
- `scan`: OpenCV 解码结果与输入逐字节一致，才可称为“已扫码验证”。
- `auto`: 有 OpenCV 时执行 `scan`，否则明确返回 `structure`。
