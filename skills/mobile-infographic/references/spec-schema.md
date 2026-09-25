# HTML 契约与 audit 字段

`audit` 只依赖这些属性做判定。手工编辑卡片时保留它们，否则会得到假的通过结果。

## 卡片级属性

| 属性 | 位置 | 含义 |
| --- | --- | --- |
| `data-card` | 根元素 | 截图与测量的唯一目标 |
| `data-template` | 根元素 | 六个模板之一 |
| `data-ratio` | 根元素 | `3:4`、`4:5`、`9:16`、`1:1`、`long` |
| `data-series-index` / `data-series-size` | 根元素 | 系列位置，用于校验页码 |

## 元素级属性

| 属性 | 含义 | audit 后果 |
| --- | --- | --- |
| `data-claim` | 可选的结论行（只放来源给出的结论，不写作者总结） | 数量最多 1，多于 1 条即 critical |
| `data-role` | `title`、`value`、`claim`、`body`、`label`、`note`、`source` | 决定字号下限与行宽上限 |
| `data-source-ref` | 证据来源 ID | 每张卡至少 1 处 |
| `data-encoding` | 该元素用位置、长度、颜色、形状或顺序表达什么 | 必须位于带 `data-source-ref` 的元素内 |
| `data-annotation` | 直接标注在改变判断的证据旁 | 计入标注数量 |
| `data-skeleton` | 尚未替换的骨架文案 | 留有任何一处即 critical |
| `data-brand-logo` / `data-attribution` / `data-page` | 页脚三件套 | 缺失即 critical |

## audit.json

| 字段 | 说明 |
| --- | --- |
| `schema` | `lov-mobile-infographic/audit/v1` |
| `context` | 模板、比例、实际画布像素、文本条目数、计数 |
| `score` | 100 分制代理分，critical 扣 12、error 扣 6、warning 扣 2 |
| `threshold` | 85；低于阈值或存在 critical 失败即不通过 |
| `checks` | 每项含 `id`、`level`、`status`、`detail` |
| `human_review` | `pending`、`passed`、`failed`；`passed` 必须同时给出图片与具体复核说明 |
| `strict` | 为真时，未经人工复核一律不通过 |

## 检查项

| id | 级别 | 判定内容 |
| --- | --- | --- |
| `canvas` | critical | 画布尺寸与模板可测 |
| `ratio` | error | 实际宽度符合声明的比例基准 |
| `image_size` | error | PNG 像素等于画布 × scale |
| `font_floor` | critical | 所有文本达到角色字号下限 |
| `line_length` | error | 每行字符当量在上限内 |
| `contrast` | error | 正文 4.5:1、大字 3:1 |
| `overflow` | critical | 无裁切与滚动溢出 |
| `truncation` | warning | 无省略号截断 |
| `glyph_overflow` | warning | 文本未溢出自身盒模型（行高偏紧但未裁切） |
| `out_of_bounds` | critical | 无元素越出画布 |
| `safe_area` | critical | 内容位于安全区内 |
| `single_claim` | critical | `data-claim` 最多一条；可以没有 |
| `evidence_linkage` | error | 编码元素挂在来源上 |
| `brand_footer` | critical | Logo 与署名完整 |
| `series_page` | warning | 页码与系列声明一致 |
| `skeleton_replaced` | critical | 骨架文案已全部替换 |
| `copy_volume` | warning | 可见文字量在 60 字以上 |
| `bar_order` | error | 每个 `.chart` 分组内部条形按数值倒序 |
| `bar_value` | error | 每行条形的数值可解析（以数字开头，单位写在数字后） |
| `long_height` | warning | `long` 单卡只记录高度与约合屏数，不设上限 |
| `title_is_subject` | warning | 标题写明作用或主题，不能只有数字或符号 |
| `title_filler` | warning | 标题不含「要点／速览／一图读完」这类通用废话 |
| `source_hygiene` | error | 卡面不含内部路径、库表名与账号标识 |

## 渲染契约

- `render` 捕获 `[data-card]` 元素而非整页，返回 PNG 实际像素并与画布 × scale 比对。
- 截图框先对齐到设备像素网格：长卡高度是小数，不这么做会与「画布 × scale」差出 1–2
  设备像素。
- 生成的 `card.html` 自带内联 CSS 与 data URL 形式的品牌 Logo，可离线打开。
- `long` 比例由内容撑高，渲染前先测量元素高度再截图。
- 一个长卡可以包含多个 `.chart` 分组（总览 + 分领域小节）；`bar_order` 在每个分组内分别校验。
