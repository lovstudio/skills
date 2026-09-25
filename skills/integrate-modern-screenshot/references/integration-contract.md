# Integration Contract

`scripts/integrate_screenshot.py integrate` 在目标 HTML 里注入一套最小、自包含
的截图能力。本契约说明注入后的 DOM 结构、样式约定、截图行为与验证口径，便于
后续在任意页面一致地复现或排查。

## Injected DOM

```html
<body>
  <div class="shot-bar">
    <button id="shot" type="button" title="导出 PNG 图片">…</button>
    <div class="shot-err" id="shot-err">
      <span id="shot-err-msg"></span>
      <button id="shot-err-copy" type="button">复制</button>
    </div>
  </div>

  <div id="capture">
    …主体内容（原本的 header + main / article / body 内容）…
  </div>

  <script>/* modern-screenshot v4.5.1 inline */ …</script>
  <script>(function(){ … domToPng … })();</script>
</body>
```

- 截图按钮（`.shot-bar`）位于 `#capture` 之外，因此永远不会被截入成图。
- `#capture` 包裹主体内容；脚本用 `getElementById('capture')` 作为截图根节点。

## Style contract

```css
#capture { width: 760px; max-width: 100%; margin: 0 auto; }
```

- `--width 0` 时省略固定宽度，仅保留 `max-width: 100%`。
- 按钮颜色用 `var(--x, fallback)` 形式，目标页定义了设计令牌就自动适配主题：

| 用途 | 令牌 | 回退 |
| --- | --- | --- |
| 按钮/错误条背景 | `--surface` | `#fff` |
| 文字 | `--ink` | `#1c1a18` |
| 边框 | `--line` | `rgba(0,0,0,.14)` |
| 悬停强调 | `--accent` | `#CC785C` |

## Capture behavior

截图时调用：

```js
modernScreenshot.domToPng(node, {
  width: node.scrollWidth,
  height: node.scrollHeight,
  scale: SCALE,
  backgroundColor: getComputedStyle(document.body).backgroundColor
})
```

- **显式 `width`/`height` = 节点实际渲染尺寸**，是「文字不换行」的关键：
  modern-screenshot 若自行测量 `foreignObject` 宽度会偏小，导致 flex/`nowrap`
  文字被错误重排。显式对齐后输出排版与屏幕一致。
- `scale` 控制输出分辨率（默认 2，760px 宽 → 1520px 输出）。
- `backgroundColor` 取自 `body`，跟随页面主题，避免默认白底在暗色页面穿帮。

## Failure surface

- 截图失败时 `.shot-err` 显示错误摘要，`#shot-err-copy` 复制
  `JSON.stringify(error.stack)`，便于带回 debug。
- 若 `modernScreenshot` 未定义（库内联失败），按钮提示「截图库未加载」。

## Verification contract

`verify` 用 headless Chrome 渲染，解析输出 PNG 的 IHDR 宽高，断言：

```
out == node.scrollWidth × scale  (宽)
out == node.scrollHeight × scale (高)
```

尺寸精确匹配即为「渲染一致、无重排」的机器可判证据。不匹配时优先检查
`--width` / `--selector` 是否与页面实际主体边界一致。

## Library

- `assets/modern-screenshot.js`：modern-screenshot v4.5.1 UMD 构建，MIT 许可，
  约 28 KB，不含 `</script>` 字样，可安全内联。
