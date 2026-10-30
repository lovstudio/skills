# script.json（talking-head-script/v1）

一条短片的唯一事实源：台词、镜头、事实、封面都在这里；提词器、分镜表、时间线、封面都从它生成。
完整示例：[`assets/templates/script.example.json`](../assets/templates/script.example.json)。

## 顶层

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `schema` | 是 | 固定 `talking-head-script/v1` |
| `topic` | 是 | 选题一句话 |
| `format` | 是 | `list` / `tips` / `review` / `tier` / `case`（style-grammar §2，决定时长区间） |
| `title` | 是 | 发布标题（平台描述首行），≤ 30 字 |
| `author` | 是 | `name`、`handle`（水印/片尾）、`avatar`（片尾圆头像）、`portrait`（样片占位） |
| `cover` | 是 | 见下 |
| `facts` | 有数字时必填 | `[{id, claim, source, checked}]`；`source` 是 URL 或本机证据路径 |
| `lines` | 是 | 逐句台词与镜头，见下 |
| `end` | 否 | `line`（片尾一句话）、`covers`（作者往期封面，片尾网格） |

## lines[]

| 字段 | 说明 |
| --- | --- |
| `id` | `L01`… 唯一；提词器、对齐、时间线都按它对应 |
| `beat` | `hook` 钩子 / `setup` 悬念或痛点 / `point` 要点 / `proof` 证据 / `verdict` 判断 / `cta` 收尾 |
| `text` | 作者要念的原话；字幕逐字取自这里（ASR 只给时间） |
| `layout` | `split`（默认）/ `face` / `broll` |
| `broll` | 上屏素材数组（`face` 忽略）；同一句多张时按 `at` 或平均切分 |
| `emphasis` | 句中要标黄放大的词，必须是 `text` 的子串；对齐时也作为 Whisper 的专名提示 |
| `callout` | 大号橙黄标注（「怎么做到的？」「《功能名》」「第 2 招」），整句停留 |
| `facts` | 本句引用的事实 id |

### broll[]

| 字段 | 说明 |
| --- | --- |
| `src` | 相对集目录的文件：PNG/JPG 截图或 MP4/MOV 录屏 |
| `at` | 从台词里这个子串开始切到本张（缺省平均切分） |
| `fit` | `cover` / `contain`；缺省时分屏在裁切 ≤ 25% 时铺满，全屏素材完整显示 |
| `focus` | `[x, y, w, h]` 归一化：前 60% 时长推近到这块区域 |
| `boxes` | `[[x, y, w, h], …]` 归一化：句首 0.2 秒依次弹出的红框 |
| `label` | 素材左上角橙色标签（「修改前」「第一步」） |
| `start` | 录屏素材从第几秒开始播 |
| `capture` | 素材怎么来：`{url, width, height, selector, full_page, wait_ms, color_scheme, hide, press}` 给 `capture.py script`；`{note}` 给作者补拍；`{prompt}` 给生图 |

## 写作约束（check_script.py 机械检查）

- 首句 `hook` 且带素材；末句 `cta`；第 2–3 句有 `setup`（WARN）。
- 每句估时 ≤ 5.5 秒（5.8 字/秒，英文词按 1.5 字）；单张素材 ≤ 4.2 秒（WARN）；素材覆盖 ≥ 60%（WARN）。
- 含阿拉伯数字、百分号或「三秒/五万积分」这类计量的句子必须引用事实。
- 禁用 AI 腔（在当今、赋能、综上所述……）与参考博主的固定口头禅。
- 封面每行 ≤ 7 字（> 9 为 ERROR）。
