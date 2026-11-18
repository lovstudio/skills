# 地标线稿

Jessy 版式的右下角有一层出血的地标线稿，压在二维码之下。成品保留这一层，但内容换成与主体相关的场景，
不用 Jessy 名片上的建筑插画。线稿只是装饰：Logo、姓名、二维码等识别元素永远用官方文件，不交给生成模型。

## 选题

按优先级选一个与用户真实相关的场景：

1. 主体主要据点的地标或城市天际线（据点来自已有名片、Profile 或用户确认）。
2. 主体的产品、作品或行业意象。
3. 都没有时，用中性的抽象线条，或去掉这一层。

不要用 Jessy 所在机构的建筑或标志物。

## Prompt 模板

```text
A delicate architectural line drawing of <场景，写清具体建筑或物件>.
Fine technical pen sketch with thin, even, mid-gray ink lines on a pure white background,
like an architect's elevation illustration printed on a premium business card.
Window grids drawn with light hairlines. No shading fills, no color, no sky, no clouds,
no water, no reflections, no people, no text, no letters, no signature, no border.
Composition anchored to the bottom edge, subjects fill the lower two thirds,
the tallest elements on the right half, plenty of empty white space at the top-left.
```

Jessy 版式把线稿放在右下角，所以高的元素放右半边、左上留白，左列文字下方保持干净。

## 生成与处理

```bash
python3 scripts/gen_illustration.py --prompt-file prompt.txt --out work/raw.png --aspect 3:2
python3 scripts/lineart.py work/raw.png work/lineart.png --ink "#6C675E"
```

- 生成脚本走 OpenRouter，模型用 `--model` 或 `JESSY_CARD_IMAGE_MODEL` 指定；也可以用其他图像 Skill 出图。
- 生成后先看原图：出现文字、签名、水印或人像就重生成。
- `lineart.py` 把白底黑线转成透明墨线：`--ink` 定颜色（暖灰 `#6C675E` 适合米白纸色），
  `--black` / `--white` 调线条浓淡（默认 4.7 / 78）。输出自动裁到内容边界。
- 在 spec 里作为 `image` 块，加 `decor: true`；贴边出血时加 `bleed: true`，透明度 0.3–0.4。
