# 程序化插图的文字与 CJK 字体安全

当插图通过 HTML/CSS、SVG、Canvas、Pillow、Mermaid 或其他确定性渲染方式包含
可读文字时，本文件是强制门禁。目标不是禁止字体回退，而是让每一次回退都可见、
有意且在栅格化前得到验证。

## 1. 为什么 CSS 声明不足以证明最终字体

浏览器按字符寻找包含字形的字体。同一个 DOM 文本节点可能同时使用多套字体；
`font-family` 只给出候选顺序，不能证明候选字体覆盖了所有字符。

一旦页面被截图成 PNG/JPG，字体回退、区域字形和度量差异都会固化进像素。下游的
Markdown、LovPen 或微信公众号 CSS 都无法再修正。因此所有检查必须发生在截图前。

## 2. 语言 run 与字体栈

1. 页面根节点声明主要语言，例如 `<html lang="zh-CN">`。
2. 每段不同语言使用独立元素和准确 `lang`：简中 `zh-CN`，日文 `ja`。
3. 简中 run 的首选字体必须是简中字体；日文 run 的首选字体必须是日文字体。
4. 中日文并列时使用协调的区域实例，例如 Source Han Serif SC 与 JP，而不是让一个
   区域字体依赖系统兜底覆盖另一种语言。
5. generic family（`serif`、`sans-serif`）只能放在最后；它的具体映射随系统、
   浏览器和 locale 变化，不能作为可复现的主字体。

```html
<span lang="zh-CN" class="zh-serif">纵组</span>
<span aria-hidden="true"> / </span>
<span lang="ja" class="ja-serif">縦組</span>
```

```css
.zh-serif { font-family: "Songti SC", "STSongti-SC", serif; }
.ja-serif { font-family: "Hiragino Mincho ProN", "Yu Mincho", serif; }
```

`lang` 能参与 OpenType 本地化字形选择，但不会自动跳过字体栈中排在首位、区域错误
却包含部分共享汉字的字体。语言标签与字体栈必须同时正确。

## 3. 导出前双重门禁

### 3.1 字符覆盖

逐个语言 run 确认首选字体覆盖全部正文字符。发现缺字时改字体或拆 run；不得通过
添加更多未知系统字体来掩盖问题。图标、emoji、数学符号等有意 fallback 必须单独
标记并允许。

### 3.2 最终浏览器实际字体

HTML/CSS 插图使用 Chromium 导出时，运行：

```bash
python3 scripts/audit_html_fonts.py \
  --html /absolute/path/to/plate.html \
  --spec /absolute/path/to/font-audit-spec.json \
  --output /absolute/path/to/font-audit-receipt.json
```

规格文件示例：

```json
{
  "runs": [
    {
      "selector": "#plate .zh-title",
      "lang": "zh-CN",
      "allowedFamilies": ["Songti SC"],
      "maxFamilies": 1
    },
    {
      "selector": "#plate .ja-sample",
      "lang": "ja",
      "allowedFamilies": ["Hiragino Mincho ProN"],
      "maxFamilies": 1
    }
  ]
}
```

脚本使用 Chrome DevTools Protocol 的实际 platform-font 回读，不以 computed
`font-family` 代替真实结果。以下任一情况必须阻止导出：

- selector 不存在或命中多个节点；
- 有效语言与规格不一致；
- 实际字体不在 allowlist；
- 字体数量超过声明值；
- Playwright/Chrome 不可用而无法完成等价回读。

## 4. 有意混植

字体混植可以是设计手法，但必须按 run 显式实施，不能把缺字 fallback 当成混植。
若同一 selector 有意包含两套字体：

- 在方案中说明目的；
- 分别给子元素设置 `lang` 与字体；
- `allowedFamilies` 列出两者并设置 `maxFamilies: 2`；
- 人工检查字面、重心、标点、行高和纵横排方向。

## 5. 收据与 provenance

每张含文字的程序化合成图至少保留：

- 合成源文件路径与 SHA-256；
- 输出图片路径、尺寸与 SHA-256；
- 每个 run 的 selector、语言、请求字体、实际 family/PostScript name、glyph count；
- 有意 fallback 的原因和 allowlist；
- 素材来源与生成方式：联网素材合成、数据图表、程序化合成或生成式 AI。

没有收据的 HTML/CSS 截图只能标为 `typography_verification: incomplete`，不能报告为
字体验收通过。
