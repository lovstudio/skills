« 2026-11-21 一次真实视频发布的记录（个人创作者账号，ego-browser 2.2.1 的 Page API，视口 1500×741、DPR 2）。
平台前端会改版，这里的每条都要能被当场的快照推翻——以页面为准，本文只用来省掉从零摸索的那几轮。
写明「本次读到 / 本次点过」的指 2026-11-21 这次运行；标 **未实测** 的没有走通或没有走到。
class 名带构建哈希后缀（如 `container-sGoJ9f`），下一次构建就会变，片段里一律按前缀 `[class*=...]` 或可见文字定位。 »

# 抖音视频发布页结构与可复用探针

| 页面 | 地址 | 怎么到 |
| --- | --- | --- |
| 创作者中心首页 | `https://creator.douyin.com/creator-micro/home` | 登录后落地页 |
| 上传页 | `https://creator.douyin.com/creator-micro/content/upload` | 首页「作品发布」卡片里的「发布视频」按钮同页跳转（2026-11-21 本次点过，由此核实入口） |
| 发布表单 | `https://creator.douyin.com/creator-micro/content/post/video?enter_from=publish_page` | 上传页提交视频后自动跳转 |
| 作品管理 | `https://creator.douyin.com/creator-micro/content/manage` | 侧边栏「内容管理」；**直链和重载都可用**（本次读到） |
| 上传说明 | `https://creator.douyin.com/creator-micro/content/quality_statement?enter_method=click` | 上传页「了解上传规则详情」，新标签页打开 |

## 和另外三个平台的差别

- **普通 DOM**：没有 wujie，没有 shadow root，`document.querySelector` 直接可用。组件库是 Semi Design
  （`semi-input`、`semi-select`、`semi-modal`、`semi-radio`），业务 class 带哈希后缀。
- **标题和简介是两个字段**：标题 `input`，简介是 editor-kit 富文本（`.editor-kit-container[contenteditable=true]`，
  每行一个 `.ace-line`），不是视频号的 `.input-editor`、B 站的 Quill，也不是小红书的 tiptap。
- **标题和简介在预览里拼成一段**：右侧预览读到的是「标题 + 空格 + 简介」，两处写同一句就会重复出现，见下文「简介」。
- **话题最多 5 个**，第 6 个点了不生成节点、只闪一下提示，见下文「话题」。
- **两个独立封面槽**（竖 3:4、横 4:3），默认都是视频首帧。
- **发布按钮是普通 `button`**，能按文字查到，不像小红书藏在 closed shadow root 里。
- **网页端没有「原创」控件**；声明类只有「自主声明」一个单选弹窗。

## 登录：扫码或验证码，交给用户

未登录打开 `creator.douyin.com` 是登录页：「扫码登录」二维码（抖音 App 扫一扫）和「验证码登录 / 密码登录」。
没有同机免扫的快捷登录，直接 `task.handOff()` 交给用户，不代填手机号、验证码或密码。本次用户扫码后约 45 秒归还控制权，
`task.waitForControl()` 正常 resolve。

登录后首页可能先弹「欢迎体验新版首页，新增智能创作能力」引导（`[role=dialog]`，按钮「1/2」「跳过」「下一步」），
它会挡住「发布视频」的点击（`<path> intercepts pointer events`）。点「跳过」即可，不涉及任何设置。

账号名读首页卡片（昵称和「抖音号：…」各一行），发布表单右侧预览里是 `@昵称`。

## 上传

上传页只有一个文件输入（本次读到）：

```text
input[type=file]  accept="video/x-flv,video/mp4,video/x-m4v,video/*,.flv,.avi,.wmv,.webm,.ts,.mp4,.mpeg4,.mov,.m4v,.mpg,.mkv,.m4"
祖先 DIV.container-drag-* < DIV.container-* < .semi-tabs-pane-active
```

断言只有一个再提交：

```js
const n = await page.evaluate(() => document.querySelectorAll('input[type=file]').length)
if (n !== 1) throw new Error('file input count ' + n)
await page.setInputFiles('input[type=file][accept*="video"]', [VIDEO_ABS_PATH])
```

**提交视频后立刻弹出浏览器定位权限请求**（本次 `setInputFiles` 那一轮就报
`A browser permission prompt for location access has appeared. The user now controls this task space`）。这是硬停：
通知用户按隐私优先点「拒绝」（地点可以在表单里按名称搜），`task.waitForControl()` 等归还，不 `takeOverTaskSpace()`。
用户处理后页面已在发布表单上，视频照常在传。

上传进度文案 **未观测到**：30 MiB 的片子，接手后第一次读表单时已经没有进度条，只有底部一句「点击发布后，如作品还在上传中，
请勿关闭页面，等待上传发布完成。」。大文件的进度、转码提示长什么样，下次遇到再记。

发布表单上同时有好几个文件输入（本次读到），**都不是**上传页那个：

| 用途 | 判据 |
| --- | --- |
| 重新上传视频 | `accept` 以 `video/` 开头，祖先含 `preview-button-*`（右侧「重新上传」） |
| 封面裁剪（表单主体） | `accept="image/png,image/jpeg,image/jpg"`，祖先 `cropUploadWrapper-*` |
| 封面编辑器「上传封面」 | 编辑器里 `[class*=selectArea] input.semi-upload-hidden-input`，见「封面」 |
| 封面编辑器「生成参考图」 | 同样的 `accept`，祖先 `list-*`，**不要用** |

`-replace` 结尾的 `semi-upload-hidden-input-replace` 是替换用的孪生 input，也不要用。

## 标题：真点击 + `insertText`，读 `value` 和计数器

```text
input.semi-input[placeholder="填写作品标题，为作品获得更多流量"]   maxLength = -1
计数器：同一个 .semi-input-wrapper 里的 .semi-input-suffix，文本「n/30」
```

本次写法：`page.click(选择器)` → `page.keyboard.insertText(标题)`，约 1.2 秒后读到 `value` 为整句、计数器 `17/30`，
下一轮（已失焦）复读不变。上限 30 只来自计数器，没有撞过线，超了页面怎么提示 **未实测**。

## 简介：editor-kit，按 `.ace-line` 逐行回读

```text
.editor-kit-container.editor-comp-publish[contenteditable=true][data-placeholder="添加作品简介"]
  > .ace-line > [data-line-wrapper] > span[data-leaf] > span[data-string]
计数器：.toolbar 下的 div，文本「n / 1000」
```

- 写：`page.click(编辑区)` → `keyboard.insertText(第一行)` → `keyboard.press('Enter')` → `insertText(第二行)`。
  两行 17 + 17 字读到 `35 / 1000`，**换行计 1**。
- 整段替换：点进编辑区后 `keyboard.press('ControlOrMeta+a')` 再 `insertText(新文本)`，本次走通，只替换编辑区内容。
- 读：逐个 `.ace-line` 取 `innerText`，去掉 `​`（每行末尾都有一个 `data-enter` 零宽字符）和 NBSP；
  话题节点要先从克隆里删掉再取正文，见下文的整表读取。

### 标题和简介别写同一句

右侧「预览视频」里读到的是 `标题 + " " + 简介`。本次先把冻结钩子两行整段写进简介、第一行同时当标题，预览读到：

```text
一张照片，能只用旋转的圆画出来吗？ 一张照片，能只用旋转的圆画出来吗？
想用你自己的照片，也做一条同款吗？
```

改成「标题 = 第一行，简介 = 第二行 + 话题」后预览是一整句。从别的平台继承两行钩子时就这么拆，并在终稿确认里列为平台适配。

## 话题：「#添加话题」+ 联想项**按名称全等**点选，最多 5 个

1. 光标放到简介末尾：点编辑区 → `keyboard.press('ControlOrMeta+End')`；需要另起一行就再按一次 `Enter`。
2. 点工具栏 `[class*=toolbar-button]` 里文字为「#添加话题」的按钮：在光标处插入一个 `#`，焦点留在编辑区。
3. `keyboard.insertText(话题名)`，联想列表挂在 `.mention-suggest-mount-dom` 里。
4. 每一项是 `div.tag-hash-*`，名称在 `span[class*=tag-hash-view-name]`，热度在 `span[class*=tag-hash-view-count]`
   （如 `5356.3万`、`0`）。**按名称 span 全等找行**，行是名称 span 的 `parentElement.parentElement`。
5. 等列表稳定：连续两次（间隔约 0.5 秒）读到的名称序列相同、且含目标名，再取 rect；断言 `elementFromPoint` 落在这一行、
   且命中处所在行的名称就是目标名，真鼠标点一次。
6. 下一轮读 `[data-mention="#"]` 节点：新增一个、文本为 `#名称`（两侧各有一个 NBSP），节点本身 `contenteditable=false`。

本次踩过的两个坑：

- **按容器直接子元素找候选会点错**：`.mention-suggest-item-container-*` 下面只有一个包住整张列表的 `div`，它的第一行文字
  恰好是第一项的名字。拿它的中心点去点，落在列表中部，生成的是「#傅里叶级数计算」而不是「#傅里叶级数」，而断言
  `wrapper.contains(hit)` 照样为真。必须按名称 span 定位到行。
- **点的时候列表还在刷新**：第 6 个「Agent」点下去没生成节点，列表随即换成按「A」检索的结果（爱情、安全……），
  看上去像点击时机不对。装上提示记录器重试才读到真正原因，见下条。

### 第 6 个话题只闪一下「最多可添加5个话题」

第 6 个话题点了候选后：不生成节点，输入的 `#Agent` 留在简介里成了**纯文本**，前端只闪出一句「最多可添加5个话题」，
截图里看不到。点之前在页面里装一个 `MutationObserver` 记录新增节点文字，才能抓到这种一闪而过的提示：

```js
await page.evaluate(() => {
  window.__dyLog = []
  window.__dyObs?.disconnect()
  window.__dyObs = new MutationObserver((ms) => { for (const m of ms) for (const n of m.addedNodes) {
    const t = (n.innerText || n.textContent || '').trim()
    if (t && t.length < 120) window.__dyLog.push({ at: Date.now(), t })
  } })
  window.__dyObs.observe(document.body, { childList: true, subtree: true })
})
// …点击之后
const log = await page.evaluate(() => window.__dyLog.map((x) => x.t))
```

话题数在预检里就卡住：`check_copy.py --platform douyin` 超过 5 个报 error `topics_too_many`。

### 删掉选错的话题或残留的纯文本

- 话题节点是原子节点：光标在末尾时第一下 `Backspace` 删掉节点后的空格，第二下删掉整个节点（本次读到节点数 1 → 0）。
- 没生成节点的 `#Agent` 是 6 个普通字符：先 `Escape` 关掉联想，点编辑区 → `ControlOrMeta+End` → `Backspace` × 6。
- 删完读一次节点集合、逐行正文和计数器（本次：5 个节点、`50 / 1000`）。

计数器把话题连同 `#` 一起算进去：17 字正文 + 换行 + 5 个话题读到 `50 / 1000`。

### 不要碰的东西

- 简介下方「推荐」一排话题 chip（本次是 `#网页设计`、`#初学ps` 之类，与片子无关）：点了就会加进话题，占掉 5 个名额。
- 「官方活动」卡片：会把作品挂到活动上，用户没要求就不点。
- 「快速填写」按钮：没试过，可能覆盖标题和简介。

## 封面：竖 3:4 + 横 4:3 两个独立槽

表单主体「设置封面」一行（本次读到）：

```text
[class*=coverControl]  > [class*=cover-]（缩略图，文字「选择封面」）+ [class*=cover-tip]「竖封面3:4」
[class*=coverControl]  > …                                        + [class*=cover-tip]「横封面4:3」
[class*=recommendContainer]「Ai智能推荐封面」：平台生成的候选，右下角带「AI」角标
```

- 两个槽默认都是视频首帧。本期首帧是黑场，留默认就等于没有封面；右侧「发文助手」提示「横/竖双封面缺失」。
- 「Ai智能推荐封面」是平台用 AI 生成的图，不是批准封面，不要点。
- 点槽位缩略图打开编辑器 `.dy-creator-content-modal-content`：顶部「设置竖封面 / 设置横封面」两个 tab；左栏
  AI封面 / 模板 / 贴纸 / 标题 / 文字 / 滤镜；中间是裁切框和视频帧时间轴，时间轴右侧「上传封面」；右栏「竖封面预览（3:4）」；
  底部「封面检测」「完成」「设置横封面」。
- 「上传封面」对应的 input：`[class*=selectArea] input.semi-upload-hidden-input`
  （`accept="image/png,image/jpeg,image/jpg,image/bmp,image/webp,image/tif"`）。同一弹窗里还有一对 accept 完全相同的 input
  属于左下「生成参考图」，选错会把封面当成 AI 参考图。
- 只看不改时用右上角 `svg[class*=close]` 关闭：本次关掉后两个槽仍是「选择封面」，没有保存任何东西。

### 已实测的上传顺序（2026-11-21，前后换过两轮封面）

**第一次设置（两个槽都还是「选择封面」）**：编辑器是两步式，顶部「设置竖封面 / 设置横封面」是步骤条
（激活项 class 含 `step-active`），底部按钮「封面检测 / 完成 / 设置横封面」。

1. 点「竖封面3:4」槽的缩略图（先断言 `elementFromPoint` 落在缩略图里）→ 等 `.dy-creator-content-modal-content` 出现；
2. 断言激活步骤是「设置竖封面」、`[class*=selectArea] input.semi-upload-hidden-input` 恰好 1 个，`setInputFiles` 传 3:4；
3. 截图：批准封面铺满裁切框，右侧「竖封面预览（3:4）」网格里标题完整；
4. 点底部「设置横封面」进入第二步。页面顶部闪出「已优先同步竖封面底图和素材。效果不满意？一键清空素材」——
   平台先把竖封面底图搬到了横封面画布上；
5. 断言激活步骤是「设置横封面」、预览是「横封面预览（4:3）」，再传 4:3。新图整张盖掉同步过来的底图，画布显示的就是 4:3 原图；
6. 点「完成」（断言命中后真鼠标点一次）。弹窗关闭，两个槽缩略图换成新地址、「选择封面」字样消失，
   槽上方先显示「封面检测中70%」，约十几秒后变成「封面效果检测通过」，「发文助手」显示「封面检测通过 / 暂未发现封面低质问题」。

**已经设过封面后再换**：点哪个槽就只打开那个槽，编辑器变成单槽模式——标题只有「设置竖封面」或「设置横封面」，
没有步骤条（按 `step-active` 断言会落空），底部按钮是「重新检测 / 取消 / 完成」。断言标题与预览文字
（「竖封面预览（3:4）」/「横封面预览（4:3）」）后照样用 `selectArea` 那个 input 上传，新图整张替换旧图，不会叠层。

- **上传后画布更新可能要 8 秒左右**：第二轮换横封面时，`setInputFiles` 之后 4 秒截图仍是旧图，8 秒时才换成新图；
  `input.files` 读到的一直是空数组，不能当证据。等够时间再截图，没变也不要重复上传，先再等一轮。
- 验收以截图为准：裁切框里是批准封面、两种信息流预览卡片（右侧「预览封面/标题」里的「横封面 / 竖封面」切换）标题和人像完整、
  槽上方「封面效果检测通过」。

## 合集

一行两个 `semi-select`：类型「合集」+「请选择合集」。本次账号没有合集，「请选择合集」展开后只有「不选择合集」。
创建合集的入口与表单、合集名上限 **未实测**；需要新建合集时按 SKILL.md 的合集口径先问用户。

## 自主声明：单选弹窗，默认不添加

点「请选择自主声明」打开 `.semi-modal.semi-modal-small`「对作品内容添加声明」，单选（本次读到原文）：

```text
内容由AI生成
内容为个人观点或见解
内容为转载信息
内容含营销推广信息
虚构演绎，仅供娱乐
无需添加自主声明
```

按钮「取消」「确定」。点「取消」关闭后表单仍显示「请选择自主声明」（本次读到）。按作者 2026-10-01 偏好不选「内容由AI生成」，
保持未添加；含生成素材时在终稿确认里写明「含生成素材，按偏好未标注」，由用户当次决定。2026-11-21 自主声明留空照样发布成功，没有被拦下。

## 扩展信息

- 「添加标签」：类型 `semi-select`（选项 位置 / 影视演艺 / 小程序 / 标记万物，默认「位置」）+ 输入框「输入地理位置」。
  用户没要求就不填；按名称搜索地点的写法 **未实测**。
- 「关联热点」：「点击输入热点词」，用户没要求不填。

## 发布设置：单选是 checkbox 实现的

三组单选都是 `label[class*=radio-] > input[type=checkbox].radio-native-*`，选中态读 `input.checked`（本次默认值）：

| 组 | 选项（input.value） | 默认 |
| --- | --- | --- |
| 谁可以看 | 公开（0）/ 好友可见（2）/ 仅自己可见（1） | 公开 |
| 保存权限 | 允许（1）/ 不允许（0） | 允许 |
| 发布时间 | 立即发布（0）/ 定时发布（1） | 立即发布 |

用户没要求就保持默认。定时发布的时间控件 **未实测**。

表单里还有隐藏的「付费视频」开关、售价和付费标题（`maxLength 28`，默认 `@昵称的付费视频`），尺寸为 0，不要碰。

## 一次读完整个字段表

本次在页面上跑通，终稿确认与提交前复读都用它：

```js
const form = await page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 }
  const t = (e) => (e ? (e.innerText || e.textContent || '') : '').replace(/[​]/g, '').replace(/ /g, ' ')
  const leaf = (s) => [...document.querySelectorAll('body *')].find((e) => e.childElementCount === 0 && e.textContent.trim() === s && vis(e))
  const title = document.querySelector('input[placeholder="填写作品标题，为作品获得更多流量"]')
  const ed = document.querySelector('.editor-kit-container[contenteditable=true]')
  const topics = [...ed.querySelectorAll('[data-mention="#"]')].map((e) => t(e).trim())
  const lines = [...ed.querySelectorAll(':scope > .ace-line')].map((l) => {
    const c = l.cloneNode(true); c.querySelectorAll('[data-mention]').forEach((m) => m.remove()); return t(c).trim()
  })
  const radios = {}
  for (const g of ['谁可以看', '保存权限', '发布时间']) {
    let row = leaf(g); while (row && !row.querySelector('label[class*=radio-]')) row = row.parentElement
    radios[g] = row ? [...row.querySelectorAll('label[class*=radio-]')].filter((l) => l.querySelector('input').checked).map((l) => t(l).trim()) : null
  }
  const covers = [...document.querySelectorAll('[class*=coverControl]')].map((c) => {
    const img = c.querySelector('img')
    return { slot: t(c.querySelector('[class*=cover-tip]')).trim(), label: t(c).split('\n')[0].trim(), img: img ? img.src.split('?')[0].slice(-60) : null }
  })
  const sel = [...document.querySelectorAll('.semi-select')].filter(vis).map((e) => t(e).trim())
  const counter = (re) => [...document.querySelectorAll('body *')].filter((e) => e.childElementCount === 0 && re.test(e.textContent)).map((e) => e.textContent.trim())[0]
  return {
    url: location.href,
    account: t([...document.querySelectorAll('body *')].find((e) => e.childElementCount === 0 && /^@/.test(e.textContent.trim()) && e.getBoundingClientRect().x > 1080)).trim(),
    title: title.value, titleCounter: title.closest('.semi-input-wrapper').querySelector('.semi-input-suffix').innerText,
    descLines: lines, descCounter: counter(/^\d+\s*\/\s*1000$/), topics, covers,
    collection: sel.slice(0, 2), declare: leaf('请选择自主声明') ? '未添加' : 'see page', radios,
    errors: [...document.querySelectorAll('[class*=error], .semi-form-field-error-message')].filter(vis).map((e) => t(e).trim()).filter(Boolean),
  }
})
```

- `account` 取右侧预览里 `@` 开头的那一行，只适用于本次 1500 宽的视口；视口变窄时先截图确认预览栏位置。
- `covers[].img` 是缩略图地址尾部。两个槽默认是同一个首帧地址；上传批准封面后应各自换成新地址，且「选择封面」字样消失。
- `declare` 只区分「未添加」与已选；选了别的项时去页面上读原文。

## 发布

主提交是表单底部的普通 `button`，文字「发布」（`button[class*=primary]`，旁边是「暂存离开」）。表单滚在顶部时它在视口外
（本次读到 `y=1285`、视口高 741），按 [浏览器工作流](../browser-workflow.md)「视口外的按钮」：
第一轮 `scrollIntoView({ block: 'center', behavior: 'instant' })`，第二轮重读 rect，断言在视口内、`elementFromPoint` 命中、
`disabled === false`，真鼠标点一次（本次 `(452, 645)`）。

点之前装上提示与请求记录器（`MutationObserver` 记新增节点文字，再包一层 `fetch` / `XMLHttpRequest`），本次点完读到：

```text
提示：正在发布 → 发布成功 / 分享给朋友
请求：POST /web/api/media/aweme/create_v2/?read_aid=2906&…   返回 {"item_id":"<作品 ID>","status_code":0}
页面：跳到 https://creator.douyin.com/creator-micro/content/manage?enter_from=publish
```

`item_id` 就是作品 ID。提示、接口返回和跳转都只证明提交成功，状态以作品管理列表为准。点之前同一页还会请求
`/aweme/v1/open/publish/limit_app_groups/`（「同时发布到」其他应用的授权列表，本次为空），不用理会。

本次没有出现任何确认弹窗，自主声明留空也没有被拦下。

## 作品管理：回读与查重

`https://creator.douyin.com/creator-micro/content/manage`，重载后等「作品 (n)」和 `[class*=video-card-info]` 出现再读。
每张卡片的文字依次是：时长 → 「标题 + 空格 + 简介 + 话题」一段 → 编辑作品 / 设置权限 / 作品置顶 / 分享 / 删除作品 →
发布时间 → 状态（`[class*=info-status]`）→ 数据。卡片里没有作品链接。

```js
const r = await page.evaluate(() => ({
  head: (document.body.innerText.match(/作品 \(\d+\)/) || [''])[0],
  cards: [...document.querySelectorAll('[class*=video-card-info]')].map((c) => {
    let card = c
    for (let i = 0; i < 4 && card.parentElement; i++) { card = card.parentElement; if (/\d\d:\d\d/.test(card.innerText.split('\n')[0])) break }
    return { text: card.innerText.split('\n').slice(0, 10).join(' | '), status: c.querySelector('[class*=info-status]')?.innerText.trim() ?? null }
  }),
}))
```

本次：提交前「作品 (3)」、没有本期条目（查重）；提交后约 1 分钟重载读到「作品 (4)」，第一张就是本期：

```text
00:54 | 一张照片，能只用旋转的圆画出来吗？ 想用你自己的照片，也做一条同款吗？ #傅里叶级数 #傅里叶变换 #数学之美 #数学可视化 #AI创作 | 编辑作品 | … | 2026年11月22日 00:00 | 审核中
```

状态原文「审核中」→ `platform_pending`。很早的作品没有状态节点（`status: null`），不要把 null 当成已发布。

## 账号探针跟着预览栏变

右侧预览栏在「预览视频」时显示 `@昵称`，切到「预览封面/标题」后只显示昵称（没有 `@`），整表读取里的 `account` 就会读成空串。
空串时去首页卡片或切回「预览视频」再读，不要把空串当成账号不符。
