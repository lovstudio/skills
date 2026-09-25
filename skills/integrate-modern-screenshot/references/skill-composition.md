# Skill Group Composition

## Nearby Skills Inspected

| Skill | 实际 routing contract | 分类 |
| --- | --- | --- |
| `lov-rich-export` | 把内容稳定导出为单文件 HTML、带 assets 的 HTML、Markdown、DOCX 与 PDF，并按格式处理图片/音视频/交互内容。 | upstream atom |
| `lov-html2pptx` | 用真实浏览器引擎把 HTML `.slide` 渲染成 16:9 图片并打包为 PPTX。 | not composed |
| `lov-png2svg` | PNG 转 SVG，含去白底与 vtracer 矢量化。 | downstream atom（弱） |
| `lov-pdf2png` | PDF 单页渲染并纵向拼接为 PNG（macOS CoreGraphics）。 | not composed |

无已检查的 Skill 拥有本 Skill 的完整输出：给一个已存在的 HTML 页面注入自包含的
前端截图按钮，并端到端验证截图与屏幕渲染一致。

## Atomic Handoffs

| 阶段 | Owner | 输入产物 | 输出产物 | 验收归属 |
| --- | --- | --- | --- | --- |
| 可选内容导出为 HTML | `lov-rich-export` | 内容源 | 单文件/带 assets 的 HTML | rich-export 拥有导出正确性 |
| 核心截图集成 | `lov-integrate-modern-screenshot` | 目标 HTML | 带导出按钮的 HTML + 验证报告 | 本 Skill 拥有截图与渲染一致性验收 |
| 可选 PNG 矢量化 | `lov-png2svg` | 导出 PNG | SVG | png2svg 拥有矢量化质量 |

每次交接都通过文件产物，无运行时 Skill 依赖。调用方可只使用核心阶段。

## Overlap Decisions

- 内容导出不重复：`lov-rich-export` 负责「多格式交付」，本 Skill 只负责「页面内前端截图按钮」。
- HTML→PPTX 不重复：`lov-html2pptx` 是后端确定性转换，本 Skill 是前端按钮注入，产物与用途不同。
- PDF→PNG 不重复：那是后端文档转换，与本 Skill 的前端截图无交集。
- PNG→SVG 仅作为可选下游，不作为隐藏依赖。

## Composition Decision

本源码是 **Single Skill**。`integrate` 与 `verify` 是同一个用户可见结果——「给页面加
可验证的截图能力」——的不可分阶段；`self-test` 只是同一 CLI 的内置冒烟路径，不是
独立可触发的产品。额外 Skill Kit 只会增加路由开销而不产生有意义的模块边界。
