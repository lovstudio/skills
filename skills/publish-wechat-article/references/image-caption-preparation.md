# 正文图片 Caption 准备契约

`lov-publish-wechat-article` 在 Lovpen 渲染前组合 `lov-image-decorator`。该阶段只处理确实需要读者可见 Caption 的图片，并交回不覆盖原图的派生文件与机器可读收据；发布器不复制图片装饰实现。

## 先决定 Caption 是否应该存在

Caption 只有三类正当任务：

1. 说明这张图证明了什么、比较了什么或为什么值得读者注意。
2. 提供必要的作品、作者、年代、摄影者、馆藏或资料来源归属。
3. 补充离开正文后仍不可缺少的阅读上下文。

以下情况不添加 Caption：

- 只是重复 alt、相邻正文、章节标题或图中已经清楚可见的文字。
- 只是在描述制作过程，例如“这是正文首图”“使用官方 Logo”。
- 正文后文已有完整作品背景，首图本身不需要重复归属。
- 只能写出通用 `Powered by ...`，却没有真实阅读信息。

Alt 描述图像内容，Caption 提供读者需要的补充，正文负责论证，作品说明承载扩展背景；四者不得机械复制。

## 选择装饰材料

| 图片类型 | `lov-image-decorator` 样式 | Caption 重点 |
| --- | --- | --- |
| 艺术作品、摄影、封面图片 | `editorial-caption` | 作者、作品名、年代、摄影或馆藏等必要归属 |
| 软件截图、产品界面 | `screenshot-caption` | 截图展示的状态、问题、操作或结果 |
| 研究资料截图 | 按画面边界选择 | 资料名称、图号、关键结论和必要来源 |
| 表格与图表渲染图 | 调用方显式选择 | 对比对象、指标或结论；白底不能单独作为截图判据 |
| 装饰图、节奏图 | 不处理 | 没有真实信息任务时不增加 Caption |

引用人物、作品或外部品牌时，只写事实归属，不使用“品牌背书”等模板化免责语，也不得暗示未经授权的合作或认可。

## 执行顺序

1. 盘点正文全部图片，记录源路径、图片类型、邻接正文、alt 与现有可见图注。
2. 对每张图片写出 `caption | no-caption` 决定及理由；只有 `caption` 项进入装饰步骤。
3. 为每个 `caption` 项提供显式 Caption。公众号文章链不得依赖 `lov-image-decorator` 的 fallback。
4. 调用 `lov-image-decorator`，输出到新的本地 JPG 或 PNG，并保留它返回的尺寸、Caption 来源、Logo 来源、字节数与 SHA-256。
5. 只在文章副本中把原图片引用替换为派生文件；不覆盖原图，不修改未选中图片。
6. Caption 必须位于原图之外的固定区域，不遮挡图片，也不改变文章中图片组件的外部 `gap`；文章把“原图 + Caption 区”作为一张完整图片处理。
7. 若派生图已经烧录 Caption，删除紧邻图片、内容相同的独立斜体图注，避免读者看到两遍。
8. 回读派生图，确认原图内容完整、Caption 未截断、Logo 未变形，截图没有透明阴影画布或第二层外框。
9. 检查 Caption 与 alt、相邻正文和图内文字没有重复，再把文章副本交给 Lovpen 渲染。

示例：

```bash
python3 "$IMAGE_DECORATOR_DIR/scripts/decorate_image.py" screenshot.png \
  --caption "同一张三列表格在微信移动端被连续换行后，整表高度显著增加" \
  --style screenshot-caption \
  --output screenshot-captioned.png \
  --json
```

## 验收与收据

发布收据的 `technicalDetail.imageCaptionPreparation` 至少记录：

- 正文图片总数、使用 Caption 的图片数与未使用 Caption 的图片数；
- 每个派生文件的路径、样式、Caption、源文件 SHA-256、输出 SHA-256 与装饰收据；
- `explicitCaptionsOnly=true`、`sourceImagesPreserved=true`、`fallbackCaptionUsed=false`；
- Caption 与 alt/邻接正文的重复检查结果；
- 未添加 Caption 的图片及其简短理由。

没有图片或全部图片均判定为 `no-caption` 时，该阶段仍然完成，但记录 `decoratedImageCount=0`；不要为了让依赖“看起来被调用”而制造无信息底栏。
