# 卡片蓝图与交付契约

本 Skill 不自己排版：图形由 `card_figures.py` 生成，卡片由 `lov-mobile-infographic`
渲染和审计。这里规定两边之间的交接。

## 卡片结构（从上到下，顺序固定）

| 区块 | 内容 | 来源 |
| --- | --- | --- |
| 大标题 | **恋爱指数分析**（固定，不随对象变） | 文案 |
| 定位标签 | 分析对象：<昵称> | 请求 |
| 结论框 | **全卡唯一结论**，一句，可被反驳 | 作者判断 |
| 56 天的对话地图 | 日历矩阵：上半个色块＝对方、下半个＝自己，深浅＝条数，空格子＝没聊天 | `figure-matrix.svg` |
| 聊天里到底在聊什么 | 两条堆叠横条（按比例）＋ 8 周趋势折线（工作／情感两条线） | `figure-composition.svg`、`figure-weekly.svg` |
| 同一段时间里的两个人 | 2–5 条两两对照（回话速度、谁先开口、谁收尾、深夜、语音…），每条一行 | `card-data.json` |
| 记录里没有出现的话 | 反证块：关键词命中为 0 或只出现一次的事实 | `card-data.json` |
| 口径行 | 样本、分母、周期、时区、语义模型与一致率 | `card-data.json.accuracy` |
| 附录 | 数据来源与信息图呈现两个来源行（页面标题＋完整网址） | 固定 |
| 末行 | 仅供参考 | 固定 |

规则：

- **全卡只留一个结论**：标题讲主题，结论讲判断，二者不要重复。
- 语义占比必须与**模型名与一致率**同时出现，且写明「工作内容不计入情感」。
- 分母必须写明是「有文字的消息」的条数：图片、语音、表情不计入语义分母。
- 一致率低于门槛时，卡面要直接写「低于门槛、占比仅供参考」，而不是只放一个数字。
- 矩阵与构成图都用同一时间窗；卡片上写清起止日期。

## 图形契约

三张 SVG 都以内容宽 904px（1080 画布、左右安全区 88px）为坐标，使用宿主卡片的 CSS 变量上色：

```css
.matrix svg { display: block; width: 100%; height: auto; }
.matrix text { font-size: 26px; fill: var(--muted); }
.matrix text.mx-strong { fill: var(--ink); font-weight: 600; }
.matrix text.mx-accent { fill: var(--accent-ink); font-weight: 600; }
.matrix .mx-empty { fill: var(--soft-line); }
.matrix .cp-work { fill: var(--primary); }    /* 工作 */
.matrix .cp-love { fill: var(--accent); }     /* 情感 */
.matrix .cp-life { fill: #9BA8BC; }           /* 生活 */
.matrix .cp-none { fill: #DED8CE; }           /* 无内容 */
```

注入方式：在卡片的对应区块里留 `<!--MATRIX-->`、`<!--COMP_SIDE-->`、`<!--COMP_TREND-->`
三个标记，把 SVG 文本原样贴进去（不要用脚本二次转义）。

文字上色的硬约束：深色块（工作）与橙色块（情感）上不放文字，百分比标签一律排在色块**下方**的纸面上，
否则对比度审计会失败，读者也看不清。

## 交付前必须过的门

1. `verify_figures.py`：SVG 标签 0 重叠、0 溢出、0 越界、0 被自身视口裁切。
   内联 SVG 会裁掉 viewBox 之外的内容，所以末位刻度这类靠边标签必须单独查
   （`clipped_in_svg`），卡片级审计看不见这种裁切。
2. `lov-mobile-infographic` 的 `audit --strict --human-review passed`。
3. 原尺寸 + 320px 缩略图各回读一次，确认标题与结论仍可辨识。
4. 卡面自查：无账号、无库路径、无表名、无真实姓名与联系方式；引语已截断。
5. 口径自查：每个数字都有单位与分母；语义占比带模型与一致率；「工作不计入情感」在卡面可见。

## 交付物

```text
<project>/
├── card.html / card.png / card.audit.json     # 卡片三件套（由 lov-mobile-infographic 产出）
├── metrics.json                               # 互动量化
├── matrix.json                                # 日历矩阵数据
├── labels.jsonl / accuracy.json               # 语义标注与校准
├── composition.json                           # 话题构成
├── figures/                                   # 三张 SVG
├── verify.json                                # 几何复核
├── brief.md                                   # 论证与证据表
└── source.md                                  # 原始输入与归一化说明
```
