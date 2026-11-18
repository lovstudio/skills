---
name: lov-jessy-style-card-design
description: >
  克隆 Jessy 名片的横版设计与信息层级：左上主色姓名配双语职务，右上品牌标，方块图标联络行，右下地标线稿衬二维码，背面主色铺底居中 Logo；换成当前主体的品牌与真实资料，输出双面 PNG 与 HTML。Use when “Jessy 式名片”“clone the Jessy card design”.
license: MIT
compatibility: >
  Portable Agent Skills format. Python 3.9+ standard library for rendering,
  plus headless Chrome, Chromium or Edge. Optional: ImageMagick 7 for line art,
  OpenCV (opencv-python) for QR checks, OPENROUTER_API_KEY for generated landmark line art.
depends_on:
  - lov-branding-consistency
metadata:
  author: lovstudio
  version: "0.2.0"
  display_name: Jessy 名片设计 · Jessy Card Design
  card_standard: lovstudio/skill-card/v1
  content_class: microcopy
  tags:
    - business-card
    - design-cloning
    - layout-template
    - brand-assets
    - qr-verification
---

# Jessy 名片设计 · Jessy Card Design

克隆 Jessy 那张横版机构名片的版式与信息层级，把当前主体的真实资料和品牌资产放进去：
正面回答“这个人是谁、怎么找到他”，背面只做品牌识别。产出正面、背面、正反拼图三张 PNG
和一个可直接在浏览器打开的自包含 HTML。

Jessy 名片上的姓名、机构标识、主色、建筑插画和联系方式属于她和她的机构，不成为新名片的默认值。
版式规则见 [Jessy 版式](references/jessy-style.md)；配色、Logo、线稿都随当前主体。

## Triggers

### Activate when

- “按 Jessy 那张名片的样式给我做一张。”“Jessy 式名片，换成我们的品牌。”
- “照上次 Jessy 那版的结构，给同事也做一张。”
- “Make me a card in the Jessy layout.” / “Clone the Jessy card design for our brand.”

### Do not activate when

- 不指定参考、只想要一张名片：交给 `lov-business-card`。
- 参考的是 Iris 名片：交给 `lov-iris-style-card-design`。
- 参考的是另一张名片：本 Skill 只锁 Jessy 版式。只要视觉分析或复刻 prompt 时交给 `lov-visual-clone`；
  要沉淀成可复用版式时，照本 Skill 的结构另建 `lov-<名字>-style-card-design`，渲染器可以直接复用。
- 要用 Jessy 本人或她机构的身份做名片：本 Skill 只做当前主体自己的名片。
- 印刷拼版、出血、CMYK 文件：本 Skill 只出屏幕版，印刷另走印刷流程。

## Runtime context

每次运行先读 [skill.yaml](skill.yaml) 声明的字段：

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" read --skill-id lov-jessy-style-card-design --pretty
```

解析顺序：当前请求 → 项目上下文 → `skills.lov-jessy-style-card-design.records` → 共享 preferences →
`user` / `brand` / `workspace` Profile → 安全默认值。`records.never_print` 里的信息永远不上名片。
当前名片的主体优先：给同事或合作方做时，用对方提供的资料，不把操作者本人的身份带进去。

用户明说要长期记住的事实或偏好（“以后名片都不印手机号”“文件名前缀用 X”）用
`profile_store.py record --skill-id lov-jessy-style-card-design --path <field> --value '<json>' --confirm`
保存，并报告保存路径；推断的内容只用于本次。名片上的新写文字（职务译名、口号）按
`lov-branding-consistency` 审校；用户给定的姓名、品牌名、网址、地址保持原样。

## Hard rules

1. **版式照 Jessy，身份全换。** Jessy 名片上的姓名、机构 Logo、建筑插画、联系方式、二维码与机构主色一律不进成品。
2. **只用官方资产。** Logo 与二维码只用主体品牌目录里的源文件，不重绘，不让生成模型画；主色取自主体 Logo。
3. **不编事实。** 职务、电话、邮箱、地址、账号名只来自 Profile、用户确认或已有物料。没有来源的行直接删掉，
   成品里不印占位；英文职务译文、推断出的名称在交付说明里标【待确认】。
4. **不需要也不保存 Jessy 的原图。** 版式已写进 [Jessy 版式](references/jessy-style.md)。用户为了比对再给原图时，
   工作副本只放私有临时目录，用完删除，不进成品、案例、提交或上传。
5. **二维码必须回读。** 最终 PNG 缩到 1/3 仍能解码，且与源二维码是同一载荷。
6. **只起草，不外发。** 随名片发出的消息只给草稿并写明“未发送”。
7. **不覆盖。** 输出已存在时渲染器拒绝覆盖；改版就升版本号（v0.1 → v0.2）。

## Workflow

### Step 0: 准备

```bash
export SKILL_DIR="<lov-jessy-style-card-design 的安装目录>"
```

渲染需要 Chrome、Chromium 或 Edge（自动查找，也可 `--chrome` 或 `CHROME_PATH` 指定）。
线稿处理需要 ImageMagick 7 的 `magick`；二维码回读需要 OpenCV；生成线稿需要 `OPENROUTER_API_KEY`。
缺哪项就在对应步骤说明，不影响其余步骤。

### Step 1: 确定主体与资料

先确认这张名片是谁的、代表哪个品牌，再按 [Jessy 版式](references/jessy-style.md) 的槽位清单建映射表：
槽位 → 主体内容 → 来源（Profile / 用户确认 / 已有物料 / 推断待确认）。

- 主色：主体 Logo 的主色，同时用于姓名、图标底块和背面铺底。
- 右上品牌标：主体的彩色横版 Logo；背面居中 Logo：白色版（个人品牌或主品牌）。
- 双语职务：中文职务一行、英文对应一行；英文译名标待确认。
- 联络行：只放有来源的，2–4 行最合适；地址写成“城市 + 地址”前缀对。
- 二维码：主体指定的官方码，先用 `verify_qr.py` 解码确认去向（只报 host）。
- 地标线稿：主体主要据点的地标或天际线。
- 背面口号与网址：主体已有的口号；没有就只留网址。

只有 `user.name` 缺失才问一个问题；其他缺口删行或标待确认，不停工。

### Step 2: 地标线稿

```bash
python3 "$SKILL_DIR/scripts/gen_illustration.py" --prompt-file ./illustration-prompt.txt --out ./work/raw.png
python3 "$SKILL_DIR/scripts/lineart.py" ./work/raw.png ./work/lineart.png --ink "#6C675E"
```

选题与 prompt 见 [地标线稿](references/illustration.md)。生成图必须无字、无 Logo、无人像；看一眼原图，
有文字或签名就重生成。也可交给 `baoyu-image-gen` 等图像 Skill 出图，再用 `lineart.py` 转成透明墨线。
主体没有明确据点或不想要这一层时，删掉线稿块，版式仍然成立。

### Step 3: 写 spec 并渲染

复制 [Jessy 版式模板](assets/jessy-style.card.json) 起步：坐标与字级保持模板值，换掉文字、颜色和素材；
内容长短变化时按 [Jessy 版式](references/jessy-style.md) 的“内容变化时怎么调”微调。
字段含义见 [版式 spec](references/layout-spec.md)，素材路径相对 spec。

```bash
python3 "$SKILL_DIR/scripts/render_card.py" ./card.json --out-dir "<输出目录>" --version v0.1
```

退出码：0 正常；3 已出图但版式检查报了越界、重叠或溢出（修 spec 后用 `--force` 重渲染）；
2 输出已存在被拒绝；1 出错（看 `error`）。

### Step 4: 验收

1. 看图：正面、背面、正反拼图逐张看。遮住文字，对照 Jessy 版式的骨架表逐项核对区块位置与色彩分工。
2. 二维码：

   ```bash
   python3 "$SKILL_DIR/scripts/verify_qr.py" "<正反拼图.png>" --expect-same-as "<源二维码.png>"
   ```

   默认在 1、0.66、0.5、0.33 四个尺度解码；失败就加大二维码或白边后重渲染。
3. 文字逐行对照映射表的来源；HTML 内嵌全部素材，渲染器已拦截私有路径与账号标识。
4. 用户给过 Jessy 原图做比对时，删除工作副本。

### Step 5: 交付

1. 结论先行：做好了什么、文件在哪（单面 PNG、正反拼图、HTML）。
2. 槽位映射：每个槽位换成了什么、来自哪里。
3. 待确认：没印上去的信息、译文、推断出的名称。
4. 限制：屏幕版 RGB、未加出血；字体随本机，换机器渲染可能略有差异。
5. 需要回给对方时，附一条随图发出的消息草稿，写明“未发送”；来自微信的，用 `lov-wdb-cowork`
   读到的说话样本定语气。
6. 用户要改：只改 spec，升版本号重渲染并重新验收。

## Composition

相邻 Skill 的分工与交接见 [能力组合](references/skill-composition.md)：`lov-iris-style-card-design` 是同族的
另一套版式；资料与语气可由 `lov-wdb-cowork` 从微信会话取出；线稿可由图像 Skill 提供；本 Skill 只对名片成品负责。

## Dependencies

- Python 3.9+（渲染器、线稿、插画脚本只用标准库）。
- Chrome / Chromium / Edge（headless 截图与版式检查）。
- 可选：ImageMagick 7、opencv-python、`OPENROUTER_API_KEY`。

## Validation

```bash
python3 scripts/validate_skill.py .
python3 scripts/render_card.py assets/jessy-style.card.json --out-dir /tmp/jessy-template --version v0.1
python3 scripts/render_card.py cases/shougongchuan-2026-11-18/card.json --out-dir /tmp/jessy-replay --version v0.1
```

模板和案例都应输出 3240×1944 的正面、背面和 3240×3888 的拼图，且 `issues` 为空。

## 通用反馈闭环

用户对本 Skill 驱动的产物提修改意见时，先判断是只针对这张名片（只改 spec 重渲染），还是可复用的规则
（先改本 Skill 的说明、模板或脚本，升版本、校验、确认安装副本，再回到这张名片）。可复用改动完成后停下等用户下一步，
不自动提交、发布或外发。
