# 表现力组件

`card-base.css` 自带五个组件，任何模板的长卡都可以直接用。文字全部留在 HTML 层，
图形尺寸写在内联样式里，`audit` 的 `scale_integrity` 会核对尺寸与数值是否成比例。

## hero：首屏主数字

卡片回答「多少／最高／多大」时用它开场，读者一眼拿到答案。数字超过五个字符时加 `is-long`。

```html
<section class="hero" data-source-ref="S1">
  <p class="hero-label" data-role="label">最高市值 · 开盘价 111.50 美元/股</p>
  <p class="hero-figure"><span class="hero-value" data-role="value">2.02</span><span class="hero-unit" data-role="label">万亿美元</span></p>
  <p class="hero-sub" data-role="body">按完全稀释股本计算</p>
</section>
```

`vivid` 风格会把整个 hero 放进深强调色色块，文字自动变白。

## split：一条分段色块表达构成

宽度按数值换算成百分比，图例与色块等宽对齐；强调段放在右端，标签自动右对齐。
数值写在 `.split-num` 里，与色块顺序一一对应。

```html
<div class="split" data-source-ref="S1" data-encoding="长度 = 市值（万亿美元），颜色 = 股份类型">
  <div class="split-bar">
    <span class="seg seg-base" style="width:72.8%"></span>
    <span class="seg seg-accent" style="width:27.2%"></span>
  </div>
  <div class="split-legend">
    <div class="split-key" style="width:72.8%">
      <span class="split-num" data-role="label">1.47 万亿</span>
      <span class="split-name" data-role="note">基本股本 · 约 132 亿股</span>
    </div>
    <div class="split-key is-accent" style="width:27.2%">
      <span class="split-num" data-role="label">+0.55 万亿</span>
      <span class="split-name" data-role="note">潜在股份</span>
    </div>
  </div>
</div>
```

## columns：时间顺序或阶段，柱高 = 数值

按时间排，不按大小倒序。选一个最大的柱高（例如 360px），其余按比例换算。
`is-accent` 标出读者该看的那根柱，`is-soft` 是同一类的次要柱，默认色用于对照组。
2–6 根柱放得下；更多时改用 `bar-ranking`。

```html
<div class="columns" data-source-ref="S1" data-encoding="高度 = 金额（万亿美元），颜色 = 私募估值 / 上市后市值">
  <div class="col">
    <span class="col-value" data-role="label">0.38</span>
    <span class="col-bar" style="height:68px"></span>
    <span class="col-name" data-role="note">Series G</span>
    <span class="col-date" data-role="note">2026-02</span>
  </div>
  <div class="col is-accent">
    <span class="col-value" data-role="label">2.02</span>
    <span class="col-bar" style="height:360px"></span>
    <span class="col-name" data-role="note">首日开盘</span>
    <span class="col-date" data-role="note">11-19</span>
  </div>
</div>
```

单位写在小节副标题里（「高度 = 金额（万亿美元）」），柱顶只放数字。

## section：长卡里的小节

```html
<section class="section">
  <div class="section-head">
    <h2 class="section-title" data-role="label">从私募估值到上市</h2>
    <p class="section-sub" data-role="note">完全稀释口径 · 高度 = 金额（万亿美元）</p>
  </div>
  <!-- 图形组件 -->
</section>
```

## chips：一行短名单

四五个短词的名单不值得占四行时用它。

```html
<p class="chips" data-role="note"><span class="chips-key">潜在股份</span>员工期权 · RSU · 认股权证 · 可转换证券</p>
```
