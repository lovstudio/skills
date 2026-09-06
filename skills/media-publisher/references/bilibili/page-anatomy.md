« 2026-08-18 在真实投稿页实测（EP.01 `BV1vzbv6eERS`、EP.02 `BV1vrbv6AEYP`）。
平台前端会改版，这里的每条都要能被当场的快照推翻——以页面为准，本文只用来省掉从零摸索的那几轮。 »

# B 站投稿页结构与可复用探针

入口 `https://member.bilibili.com/platform/upload/video/frame`，编辑已投稿件走
`?type=edit&bvid=BVxxx`。

## 和视频号最大的差别：这是普通 Vue 应用

没有 shadow DOM，没有 wujie 微前端，`document.querySelector` 直接可用。
不要把视频号那套 `DOM.getDocument({ pierce: true })` 穿透遍历套过来，多余。

但**换来另一个坑**：Vue 的双向绑定不吃合成事件。

## 写值必须用原生 setter

`input.value = x` + `dispatchEvent(new Event('input'))` **不会**更新 Vue 的模型。
表现是页面上看得见字，但计数器不动、提交时报「还没有输入 XXX」。观测实例：
建合集连报三次「还没有输入合集标题」，计数器停在 `0/20`。

```js
const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set
setter.call(i, '')
i.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'deleteContentBackward' }))
setter.call(i, VALUE)
i.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: VALUE }))
i.dispatchEvent(new CompositionEvent('compositionend', { bubbles: true, data: VALUE }))
i.dispatchEvent(new Event('change', { bubbles: true }))
```

`inputType` 不能省——Vue 的 `v-model` 修饰符和平台自己的输入过滤都会读它。

### 标题字段是例外：原生 setter 写得进去，但会在 ~100ms 内被悄悄revert 回文件名

2026-08-19 EP.04 实测：标签、简介用上面的原生 setter 套路都稳定生效，唯独标题字段
（`input[placeholder="请输入稿件标题"]`）写入后**立即读回是对的，但过 100ms 再读就变回了
上传时的原始文件名**（定时读 0ms/100ms/1100ms 三个点位实测复现）。推测是这个输入框绑定了
「未被用户真正编辑过就用文件名兜底」的 watcher，只认真实用户交互，合成事件骗不过它。

唯一稳的写法是**真操作**：三击选中全部文本 → 真键盘删除 → `Input.insertText` 插入：

```js
const r = titleInput.getBoundingClientRect()
const x = r.x + r.width/2, y = r.y + r.height/2
await cdp('Input.dispatchMouseEvent', { type:'mousePressed', x, y, button:'left', clickCount:3 })
await cdp('Input.dispatchMouseEvent', { type:'mouseReleased', x, y, button:'left', clickCount:3 })
await cdp('Input.dispatchKeyEvent', { type:'keyDown', modifiers:2, key:'a', code:'KeyA' }) // Ctrl+A
await cdp('Input.dispatchKeyEvent', { type:'keyUp',   modifiers:2, key:'a', code:'KeyA' })
await cdp('Input.dispatchKeyEvent', { type:'keyDown', key:'Backspace', code:'Backspace' })
await cdp('Input.dispatchKeyEvent', { type:'keyUp',   key:'Backspace', code:'Backspace' })
await cdp('Input.insertText', { text: TITLE })
```

写完必须等 ≥1 秒再读一次确认没有反弹，不能只信写入瞬间的读回。这条坑只在标题字段观测到，
简介/标签/分区/合集用原生 setter 没有类似问题，不要不分青红皂白全改成真键盘。

## 同一次 `js()` 里读回的计数器是旧值

写完值在**同一个** `js()` 里读 `n/N` 计数器，拿到的是 Vue `nextTick` 刷新前的旧值。
`0/20` 因此是**假失败**：上面那三次「失败」里，第三次其实已经成功了，只是读得太早。

判据：写和读必须分成两轮 `js()` 往返。误判的代价是去改一个没坏的写入逻辑。
诊断办法是 dump 容器的 `outerHTML` 看真实的 `<p class="input-max-tip">8/20</p>`。

## 简介是 Quill，不是 contenteditable 裸写

`document.execCommand('insertText', false, 多行文本)` 会把多行**吞成首行**
（观测：736 字 → 22 字）。拿 Quill 实例以用户来源写入并主动失焦：

```js
const q = document.querySelector('.ql-container').__quill
q.setText(text, 'user')
q.blur()
```

实例挂在 `.ql-container` 的 `__quill` 双下划线属性上。写入必须下一轮读取
`.ql-editor > p` / `.ql-editor.innerText` 或 `q.getText()`，与冻结全文逐字比较；只看编辑器里
出现文字不代表提交模型已更新。2026-08-30 实测首次提交公开 `view.data.desc` 为空，按上述
`setText(text, 'user') → blur → 下一轮回读` 修正后才真正发布简介。

## 计数器探针不要用 innerText 匹配

用 `innerText.match(/\/2000/)` 扫全页会命中 `<style>` 标签里的 CSS 文本
（观测：读到 `51`，而编辑器里实际有 736 字；顺手 dump 出 1.4 MB 输出）。
直接读 `.ql-editor` 的 `innerText.length`，或把探针限定到计数器自己的容器。

## 标签：三个独立的坑

1. **平台会按账号名自动猜标签**。账号「手工川」自动带出 `手工`/`生活记录`/`记录`。
   填字段前先清空已有标签，不要在脏状态上追加。
2. **部分标签是话题专用、禁止自定义添加**。toast 原文「当前tag为话题专用，不允许自定义添加」。
   2026-08-18 实测被拒：`DeepSeekHarness`、`独立开发者`、`插件开发`。
   优先点推荐 chip `.hot-tag-item`，那些一定能加。
3. **`svg.close` 和 `.hot-tag-item` 都不吃合成 click**。`.click()` 与
   `dispatchEvent(new MouseEvent('click'))` 都静默无效（观测：报告 `removed: 12`，标签一个没少）。
   必须真鼠标：

```js
const r = el.getBoundingClientRect()
const x = r.x + r.width / 2, y = r.y + r.height / 2
await cdp('Input.dispatchMouseEvent', { type: 'mousePressed',  x, y, button: 'left', clickCount: 1 })
await cdp('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 })
```

## 投稿后标签回读：`view` 接口不含 tags

投稿页标签节点只证明编辑表单当时有值。发布后用标签专用公开接口回读：

```bash
curl -s 'https://api.bilibili.com/x/tag/archive/tags?bvid=BVxxx'
```

验收字段是 `data[].tag_name`。公开页的第二条证据是
`.video-tag-container a.tag-link`；链接应带 `from_source=video_tag`。B 站会重排标签顺序，
所以把预期值与两个来源都规范化成名称集合再比较，不按投稿顺序比较。

不要用 `/x/web-interface/view` 是否含 tags 判断——这个接口不返回标签；也不要因为简介里没有
`#AI #Agent ...` 就判断 tags 丢失，B 站把简介与标签作为两个独立字段展示。标签接口和公开页
节点都命中完整集合时，结论是 tags 已发布，无需重新编辑或投稿。

## 按钮落在视口外时，坐标点会静默丢

视口实测 1496×731，而这些按钮实测在视口下方：合集弹窗「完成」y=813、
「立即提交」y=1006、「立即投稿」y=1380。坐标点击打在视口外，不报错也不生效。
2026-08-19 EP.04 确认这条不止管主按钮：推荐标签 `.hot-tag-item`（如"原创"）在长页面
里同样会落到 y>1000 的视口外，用 `document.querySelector` 读到的 rect 一样是「看得见但点
不中」，现象和按钮完全一样——**任何要点的元素都先 `scrollIntoView` 再用刷新后的 rect**，
不要因为它是小标签就跳过这步。

```js
el.scrollIntoView({ block: 'center' })
// 必须重新读 rect，用**新**坐标点
const r = el.getBoundingClientRect()
if (r.y < 0 || r.y + r.height > window.innerHeight) throw new Error('still clipped')
```

## 原创声明不是独立控件，是"原创"标签

skill 正文里「原创权益弹窗」那套写法是**视频号**的，B 站没有对应的独立「自制/转载」
勾选组件——2026-08-19 EP.04 实测整页搜「自制」「转载」「声明原创」「版权」全部
`indexOf === -1`。用户要求"原创要勾选"时，实际能做的操作是把推荐标签列表（标题正下方
「推荐标签：」那一行）里的 `原创` chip 点进正式标签，跟其他 `.hot-tag-item` 一样的坑
（真鼠标 + 视口内坐标）。不要因为找不到「原创声明」字样就报告缺失或去改创作声明
（那个是 AIGC 内容标注，字段默认「内容无需标注」，跟原创无关，别混）。

## 上传页有两个 `accept=.mp4` 的 file input

按祖先链区分，不要取第一个：

| 祖先链包含 | 用途 |
| --- | --- |
| `upload-wrp` | **主上传区**，用这个 |
| `york_videoup_wrapper` / `micro-app` | 壳层，传进去没反应 |

## 封面是两个独立的槽

这是本平台最容易误报成功的地方。

| 槽 | 比例 | 渲染在哪 |
| --- | --- | --- |
| 首页推荐封面 | 4:3 | 首页推荐位 |
| 个人空间封面 | 16:9 | **合集列表、个人空间、信息流** |

一次上传**只落到当前激活的编辑画布**，另一个仍是平台自动抽的视频帧。
`.cover-img` 的 `backgroundImage` 只反映 4:3 那个，表单显示「封面设置」也只证明 4:3 有图。

**唯一可信验证**是投稿后拉一次公开接口，看 `pic` 字段并把图下载下来看：

```bash
curl -s 'https://api.bilibili.com/x/web-interface/view?bvid=BVxxx' | python3 -c \
  'import json,sys; print(json.load(sys.stdin)["data"]["pic"])'
```

`pic` 反映的是 **16:9 槽**。弹窗内的预览只代表当前槽，不是发布结果。
2026-08-18 就是靠这条抓到「两期封面都只改了 4:3」：EP.01 的 `pic` 是 1080×607 纯黑，
EP.02 的 `pic` 是随机抽的一帧。

补 16:9 必须激活对应的编辑画布 wrapper 后直传；具体结构和恢复顺序见下文。不要依赖同步弹窗，
`双比例同步改动` 应保持关闭。**重传同一个文件可能因哈希不触发变化；关掉封面弹窗也不等于提交**，
改完仍要重新点「立即投稿」。

## `captureScreenshot` 在封面编辑器里出全白图

改用页内 canvas 抠图再 `Read`：

```js
const c = document.createElement('canvas')
c.width = img.naturalWidth; c.height = img.naturalHeight
c.getContext('2d').drawImage(img, 0, 0)
return c.toDataURL('image/jpeg', 0.9)
```

## 管理页直链会被重定向

`upload-manager/all` 和 `/season` 直接 `goto` 都会跳回 `/platform/home`。
要从侧边栏点进去：「内容管理」→「合集管理」，落在 `/upload-manager/ep`。

## 合集选择要精确匹配

列表里可能同时存在多个同前缀合集（观测：`手工川DSH实战`、`科技与社会 | 手工川工作室`、
`技术分享 | 手工川工作室`）。用 `text === 目标名`，不要用 `includes`。

## 表单控件的真实类名（自研组件库，不是 antd）

2026-08-18 在 EP.03 投稿时因为**猜类名**把分区、合集、封面三项全填不进去，
最后靠用户手填收场。这里把实测的结构钉死。

| 字段 | 容器 | 入口（点这个） | 当前值读这里 |
| --- | --- | --- | --- |
| 分区 | `.video-human-type` | `.select-controller` | `p.select-item-cont` 的文本 |
| 合集 | `.video-season` | `.season-enter` | `.season-enter-text` 的 **`title` 属性** |
| 封面 | `.cover-main` | `.cover-main .edit-text` | `.cover-main .cover-img` 的 `background-image`（仅证明 4:3） |

不存在的东西（我全试过）：`.choose-btn`、`.ant-select-*`、`.ant-cascader-menu-item`、
`.ant-form-item`、`[role="combobox"]`、`.category-item`。B 站创作中心是自研组件库 +
`data-v-*` scoped CSS，套 antd 选择器一个都命中不了，而且**查不到不报错**，
表现为「点了没反应」，很容易被误读成时机没到而空等几轮。

编辑页（`?type=edit&bvid=`）的分区控件带 `select-controller-disabled`：**已投稿件不能改分区**，
不要在编辑页重试分区，那不是定位失败。

### 反模式：`querySelectorAll('*')` + `innerText.includes(标签名)`

这是上面三项全灭的直接原因。祖先容器的 `innerText` 含整页文本，所以第一个命中永远是
最外层 `div`，`closest()` 从那里往上找必然拿到导航栏。观测实例：找「分区」拿到
`y = -134`、文本 `"主站\n试试更多AI创作工具吧…"`，CDP 就照着负坐标点了出去。

定位一律走**叶子节点 + 文本全等**，拿到 label 之后**用上表的容器类名**，不要靠 `closest()` 猜：

```js
const label = Array.from(document.querySelectorAll('h3.section-title-content-main'))
  .find(el => el.textContent.trim() === '分区')          // 全等，不是 includes
const ctrl = label.closest('.video-human-type').querySelector('.select-controller')
```

同理，**读回值不要用 `innerText.split('\n')` 取相邻行**：DOM 顺序与视觉顺序不一致，
同一次会话里把合集依次读成「商业推广」「付费合集协议」「手工川-dsh-ep03-…-v0.1」（视频文件名），
三次全错且都不像错的。合集读 `.season-enter-text[title]`。

### 封面的 file input 在弹窗打开前不存在

主文档里 `input[type=file]` 只有 3 个：两个 `.mp4`（见上文「两个 accept=.mp4」）和一个 `.txt`
（字幕）。**没有任何 `accept=image` 的输入**，`DOM.getDocument({pierce:true})` 也一样查不到——
不是藏起来了，是还没挂载。必须先点 `.cover-main .edit-text` 打开封面编辑器，
弹窗里才会出现图片输入。

而 `span.edit-text` 不是 `<button>`，`querySelectorAll('button')` 按文本找「添加封面」找不到；
它和 `.hot-tag-item` 一样只吃 CDP 真鼠标。顺序固定为：
`scrollIntoView` → 按新 rect 发 CDP mousePressed/mouseReleased → 等弹窗 → 再查 file input。

### 封面素材去 `output/covers/<ep>/` 拿，不要抽视频首帧

项目里每期都有 `lov-channels-cover` 产出的 `cover_3x4.png` / `cover_4x3.png`，
另有 `output/deliverables/手工川-dsh-<ep>-封面-1440x1080-v*.png`。找不到 16:9 时
正确动作是**指出缺口**（那套只产 3:4 和 4:3），不是 `ffmpeg -vframes 1` 抽首帧顶上——
首帧是片头静帧，当封面等于没有封面。EP.03 线上 16:9 是 1440×810 的正式封面（人像 + 标题），
和抽帧完全是两回事。

## 封面 16:9 槽切换的正确入口（2026-08-30 EP.04 纠正）

右侧「首页推荐 / 个人空间」两个 `div.button` **只切换右侧效果预览，不切换上传目标**；
`button active` 只能证明预览卡片变了，把它当编辑槽证据会让 16:9 仍保留视频抽帧。

真正的两个编辑目标是 `.cover-editor-panel-canvas > div` 包住的 `#editor_4_3` 与
`#editor_16_9`。wrapper 的 `active / inactive` 才是当前上传目标状态：上传 4:3 前确认第一个
wrapper active；再点击第二个 inactive wrapper / canvas，回读其 class 变 active 后上传 16:9。
弹窗可能只有一个可见 `span.upload-text`，图片 file input 也只有打开编辑器后才挂载，因此每次
上传都必须先证明正确 wrapper 已激活，不能按第几个上传按钮猜槽位。

`双比例同步改动` 保持关闭。两张图上传后同时截图 `#editor_4_3` 与 `#editor_16_9` 的 canvas，
再点 `div.button.submit`「完成」。如果先前把素材传错槽，最安全的恢复是点「取消」丢弃本次未保存
图层，重新打开编辑器，按 4:3 wrapper → 上传 → 16:9 wrapper → 上传 → 双 canvas 截图 → 完成
的顺序重做；不要在未知激活状态上继续叠图。

投稿后仍用 `view.data.pic` 验收 16:9，并下载目视核对。投稿成功落地页会遮住编辑表单；需要修正时
从内容管理进入同一 BV 的编辑页，修完再次「立即投稿」，不得新建重复稿件。

## 立即投稿提交：先做一次语义点击，遮挡时再交用户（2026-08-30 修订）

- 点「立即投稿」会弹「封面制作」弹窗（4:3 / 16:9 封面效果确认），点「确定」后提交。
- 「立即投稿」按钮常被预渲染 `bcc-dialog`、视频预览 `canvas`/`vp-nd-b`、素材容器 `materials` 遮挡，
  `elementFromPoint` 命中遮挡元素，CDP 真鼠标点击落到遮挡上，按钮的 React onClick 不触发。
- **不要 `display:none` 弹窗/预览容器去「透传」**——那会破坏 React 状态，导致「立即投稿」的
  onClick 彻底失效（本 EP 踩过：隐藏弹窗后点「立即投稿」无任何反应，页面停留投稿页）。
- 终稿确认后先把主按钮滚入视口，刷新 rect，按可见名称做一次语义/直接点击；出现加载、跳转、
  成功页或提交态后立刻停止点击，只进入回读。
- 只有检查 `elementFromPoint` 后确认真实遮挡、且一次点击没有触发任何提交态时，才把「立即投稿」
  与封面确认弹窗交给用户。不要无条件手动交接，也不要隐藏遮挡层或盲目重复点击。
