# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [0.16.0] - 2026-10-30

2026-10-30 发《易七猫对话手工川》B 站横版：04:50 前后填完表，停在「立即投稿」前等终稿确认。约 16 小时后用户回「确认投稿」，
这时 ego-browser 任务空间 5 已被结束、归还给用户（`ownership: "user"`），按 ego-browser「只在用户明确要求时 claim」又问了一轮，
用户回「继续」才接手，之后只点了一次「立即投稿」。当晚经作者同意把 Ego Lite 从 0.6.1.13 升到 0.6.2.5，重启后同名空间的
编号从 5 变成了 1。下面的读数都来自这次运行的会话记录。

### Added

- 浏览器工作流新节「等待终稿确认时任务空间被结束」：
  - 报错原文与判据，并和用户接管（`The user has taken control`）分开：任务结束后 `takeOverTaskSpace()` 接不回来；
    这次旧写法 `useOrCreateTaskSpace(5)` 没报错，错出在随后第一条 `js()`；
  - 先用 `listTaskSpaces()` 按名称只读确认归属和当前编号。条目里只有 `recentTabTitles`，没有 URL；
  - 没有现成授权时只问一次（接手，或用户自己点），得到明确同意才 `claimTaskSpace(id)`；
  - 接手后用 `task.tabs()` 认领原投稿页（这次 `label: null`、`openedBy: "unknown"`，要 `adopt`），整表重读、查同标题稿件，
    一致才提交一次；有出入不写不提交，要用户处理时 `handOff()` 而不是 `finish()`；
  - 接手后的轮次用 Page API（`taskSpace(id)` + `task.page('p1')`，收尾 `task.finish({ keep: [] })`），附这次跑通的写法；
    旧写法在 claim 之后没有试过；收尾后空间仍在：接手的投稿页是 `openedBy: "unknown"`，按指南 v2.2.0 受保护，
    `keep: []` 关不掉整个空间，`finish()` 不要重复调；
  - 别的长时间等待之后遇到同一报错也照此处理，只是没有现成授权。
- 浏览器工作流「编号不跨重启」：经作者同意升级 Ego Lite（0.6.1.13 → 0.6.2.5）重启后，同名空间的编号从 5 变成 1。
  停下等过用户回话之后，或 Ego Lite 重启、升级之后，复用、takeOver 或 claim 前先 `listTaskSpaces()` 按名称找当前编号，
  再用 `recentTabTitles` 核对；编号对不上或有多个同名空间就停下问作者。「跨 heredoc 轮次用 `task.id` 复用」限定在同一次
  Ego Lite 运行内，控制权一节的 takeOver 加了指向。重启后拿旧编号调用会报错、指错还是新建空间，没有验证。
- 同节「确认那一问顺带授权接手」：评估结论是可以，省掉多出来的那一轮。依据是用户对写明了接手的问句直接答确认，就是
  ego-browser 要求的明确要求。授权要同时满足四条：触发（报错出在回复后第一次动原空间）、目标（问句里的编号与按名称
  查到的当前编号一致，归属仍是 user）、答复（直接确认，没有附带改动或条件）、范围（只读核对加一次提交，不写进 Profile，不延到下一个平台）。
  缺一条就退回只问一次。

### Changed

- SKILL.md「提交前由用户确认终稿」：问句里写明空间编号（名称自己记下）、「若已被结束，确认也算让我接手」和接手后只核对、
  不改字段，并给出例句。这一条要写进问句本身，宿主有回复按钮时确认按钮发出的话也带上；按名称查到的编号变了也要单独问。
  第 10 步与「收口错误」的 `awaiting_confirmation` 一条加了指向；README 的终稿确认一段同步。

## [0.15.0] - 2026-10-29

2026-10-29 发「超越之旅」宣传短片竖版到小红书时，前四次点「发布」都没有反应：话题 12 个，超过上限 10 个。前三次被判成
点击没生效，其间交给过用户；第四次之前在页面里装上提示与请求记录器，才读到点击后约 0.1 秒闪出的提示「最多支持添加10个话题」，
这次点击也没有发出发布请求。删到 10 个话题后，第五次点击发布成功。下面的读数都来自这次运行的会话记录。

### Changed

- `check_copy.py`：小红书话题上限由「未实测」改为 10 个，超了报 error `topics_too_many`，提示里带页面原文和「只闪一下提示、
  看上去像没点上」的症状；B 站标签超限的提示不变。新增 3 条单测。
- 小红书约束：文案限制表的话题行改为 10 个；从其他平台继承话题时，填之前先减到 10 个，取舍优先沿用同期别的平台已确认的版本，
  并列入终稿确认（话题出自用户文本时 `auto` 也要停下）。
- SKILL.md：小红书最小适配加上「话题减到 10 个以内」；发布按钮一条和「点了没反应且没报错」一条加上「被前端校验拦下、只闪了一下
  提示」这种情况；第 11 步小红书「发布」改为截图前先装记录器；预检注释和第 9 步写明话题 ≤10。README 的平台表同步。

### Added

- 小红书 page-anatomy「点了「发布」没反应」：截图前装提示与请求记录器（这次跑通的写法），点完按记录判断是改字段、去笔记管理回读
  还是交接；不换点法连点，也不在读记录之前交接。
- 发布栏宿主 `xhs-publish-btn` 的属性能读：`submit-text`、`submit-disabled`、`submit-loading` 等，点之前可断言没有禁用；它们分不清
  左右两个按钮，坐标仍按截图取。
- 用 tiptap 编辑器实例删掉已插入的话题：`deleteRange` 连同前面的分隔空格，删后按 `data-topic`、逐段正文和计数器回读。
- 发布请求 `POST /web_api/sns/v2/note` 的返回里有笔记 ID（`data.id`）和 `share_link`，约束文档里「笔记 ID 与公开链接的取法未实测」
  随之改写；这个返回和成功页一样只证明提交成功，状态仍以笔记管理列表为准。

## [0.14.0] - 2026-10-12

用户 2026-10-12 要求：Skill 里加上按偏好免终稿确认，并把 0.13.0 评审时列为范围外的观测也写回。观测仍来自同日
发《背包九讲》的会话记录；写入后由独立 Agent 对照会话记录与全文复核过一轮，冲突和说过头的地方已改。

### Added

- 按 Profile 偏好免终稿确认（SKILL.md 新节）：
  - 读 `skills.lov-media-publisher.records.auto_publish`，每个平台 `auto` 或 `confirm-final`，没登记即
    `confirm-final`。是否自动只看平台值；`source`、`rule` 只作记录，写入或撤销时三处一起改；
  - 当次请求里的说法不写进 Profile，也不能据此免掉确认；
  - `auto` 只免掉「停下等回复」：预检、字段全表回读、完整性门禁、封面验收、单次提交、列表与公开接口回读都照旧，
    只作用于 `publish`，不覆盖草稿、定时和小红书的「暂存离开」；
  - 原来写「交用户决定」的事项在 `auto` 下逐项归类：生成内容标注按偏好不标、B 站「原创」chip 未出现就不加、
    小红书「新建话题」照常点、没要求地点就不填，都在发布后报告写明；
  - 退回确认的条件：当次另有说法、账号不符、用户写的文本被平台改写或被 agent 跨平台适配、需要新建合集或合集归属待定、
    用户要求的设置做不到、用户接管期间改过表单（只为登录或权限弹窗交接不算）；必填项未通过与用户仍持有控制权按原规则处理；
  - 同步改了终稿确认一节的标题与首段、第 10/11 步、状态契约、生成内容标注与 B 站原创 chip 两段、README、
    `publish-gates.md`、`browser-workflow.md` 提交分支、`description-template.md`、B 站与小红书的约束和 page-anatomy。
- `check_copy.py`：小红书同时传正文和话题时，按「正文（不算换行）+ 话题名（不含 `#`）」估计数器下限，超过 1000 报 warn
  `description_with_topics_over_limit`。依据是 32 字正文加 7 个话题读到 `71 /1000`；`#`、空格、换行的计法没拆开核对，
  所以只当下限。新增 5 条单测。
- 视频号登录态失效：`openOrReuseTab` 返回时 URL 仍是创建页、快照只有 `svg_root`，`auth_data` 返回 `errCode: 300333`、
  没有 `wujie-app`，约 20 秒后重读 URL 才是 `login.html`（是返回后才重定向还是读数滞后没有区分）。快捷登录点一次后
  4 秒仍在登录页，34 秒时已回到创建页；改为轮询 URL 约 40 秒再决定交接。`auth_data` 这组参数第二次跑通。
- 视频号列表页：发表后 3 秒仍是创建页、17 秒时已在列表页；重载后 6 秒读 DOM，`js()` 挂了十几秒后报
  `Runtime.evaluate timed out`，约 1 分钟时 `wujie-app` 还没挂出，约 85 秒时已挂出，约 120 秒时读到卡片全文。新增按描述
  前缀找卡片的片段，并写明没读到卡片不等于没有条目；`[class*=post-feed-item]` 只在挂出前跑过，未核实。
- 浏览器工作流：横向滚不过去的区域只为截图临时放宽视口（记原值、`try/finally` 恢复、恢复后核对、期间不点击）；
  页面刚重载时 `js()` 超时不算失败。

### Changed

- 视频号放宽限制：记录 2026-10-12 页面原文「上传时长8小时内，大小不超过20GB」，预检覆盖参数从 `--max-gb 20`
  改为按十进制折算的 `--max-gb 18.6`（与 B 站、小红书同口径），命令补上 `--platform wechat-channels`；
  SKILL.md、README、`check_video.py` 注释同步。
- SKILL.md 第 8 步：「视频号和 B 站都存在多个 accept 相同的 file input」改为只说 B 站；视频号的视频与封面
  input 按 `accept` 区分，封面 input 只在编辑器打开后出现。

## [0.13.0] - 2026-10-12

本版条目来自 2026-10-12 账号「手工川」发《背包九讲》的三平台观测（视频号 → B 站 → 小红书），证据是《背包九讲》项目的
`output/reports/v0.2/publish-report.md` 与会话记录。写入后由独立 Agent 回到会话记录逐条核对过，把说过头的地方都改回了
证据范围内；只观测到一次、只看到入口没有操作过、或靠推断的，原文都注明了。

### Added

- `check_copy.py`：视频号短标题新增 6 字下限。页面原文「标题至少6个字」，4 字的「背包九讲」触发，6 字的
  「背包问题九讲」通过，5 字没有试过。新错误码 `short_title_too_short`，报告 `limits` 多一个 `short_title_min`，
  新增 4 条单测。SKILL.md、README、`publish-gates.md`、视频号 page-anatomy 的短标题口径同步改为 6–16 字。
- 视频号内容列表卡片的操作原文：「置顶 分享 弹幕管理 评论管理 修改描述和封面 可见权限 删除」。描述和封面
  至少有事后修改的入口，但这次只读到入口、没有操作过。可逆性的表述改为「视频本身换不了，修改入口未实测，
  按不可逆处理」，同步改了 SKILL.md、README、`publish-gates.md` 和 B 站约束里的对比段；小红书的报告口径不再写
  「同视频号口径」，改为直接按不可逆说明。
- 小红书「封面预览在视口外」：视口 900 宽时预览面板在 x≈937 之外，横向滚不过去，`captureBeyondViewport`
  截图只有底色。新增做法：语义切到「封面预览」tab 并回读激活态，记下原视口，临时 `Emulation.setDeviceMetricsOverride`
  放宽到 1440×900 截图，`finally` 里恢复并断言视口回到原值。
- B 站分区下拉：列表在 `.drop-list-v2-content-wrp` 里自己会滚，被裁掉的项 rect 照样正常，对 rect 中心做
  `elementFromPoint` 命中的是外层容器（这次在点击前被文本断言拦下）。新增「先滚列表自身 → 下一轮断言在可见区内且
  命中文本全等 → 点一次」的片段，SKILL.md 第 9 步同步并与创作声明的 `bcc-select` 分开写；另记录「知识」落库为
  `tid 122 / 野生技能协会`，不是选错。
- 浏览器工作流新增「js() 返回数组时包成对象」：顶层直接返回数组在 B 站投稿页两次得到 `null`，同日视频号页正常。
  小红书 page-anatomy 的话题回读、可见错误两段，以及 B 站 page-anatomy 的 `archives` 回读片段，都改成包对象。

### Fixed

- 小红书封面第 1 步：当前封面缩略图改成了带 `background-image` 的 `div.default.column`，旧探针只找
  `img` / `canvas`，报 `no thumbnail near 设置封面`。改为先找 `.cover-plugin-preview .cover > .default.column`
  （排除「智能推荐封面」的 `artistic-bg` 卡片），找不到再退回旧结构（回退分支这次没走到）；滚动与读 rect 拆成两轮，
  并把尺寸核对从注释改成代码断言。后面的悬停、`.cover-edit-entry`、编辑器、上传、语义 `.click()`「完成」、
  评估文案都与 2026-10-02 一致。
- 小红书正文比对：`insertText('A\nB')` 生成两个 `<p>`，`innerText` 读回 `A\n\nB`，原来按 `innerText` /
  `bodyWithoutTopics` 整串比对会误判。字段表新增按直接子 `<p>` 逐段取文本的 `paragraphs`；正文一节、字段表判读和
  `publish-gates.md` 的正文行都改为逐段比对，`bodyWithoutTopics` 只作诊断。
- 小红书原创声明片段 a：原来在同一轮里滚动并读 rect，缺开关时返回 `null`。改成实跑用过的两轮写法（a1 只滚动并读
  状态，a2 重读 rect、断言命中 `.d-switch` 再点），缺卡片或开关时返回 `{ error }`。
- 小红书话题联想项片段补上实跑用过的 `scrollIntoView({ block: 'nearest' })`、坐标取整和 `elementFromPoint` 命中断言。

### Changed（按 2026-10-12 实测更新的记录）

- 小红书：
  - 上传中原文 `上传中 47%`、`当前速度`、`剩余时间` 可作 `uploading` 判据（上传进行中写字段没有单独验证）；
  - 标题计数器 `4 / 20`（`check_copy.py` 的标题依据同步改写）；
  - 正文计数器包含话题文本（32 字正文 + 7 个话题读到 `71 /1000`）；
  - 第一个话题节点后平台自动补 `&nbsp;`，第二个话题前不用再插空格；7 个话题的联想都照常弹出；
  - Range 收 caret 的写法跑了 7 次都落在末尾；
  - 原创声明开关与须知弹窗按 a1 / a2 / b 的顺序跑通；
  - 定时开关同为 `.d-switch-simulator`；
  - 合集一行只有「创建合集」时，推断账号没有合集（未另行核实）；
  - 默认第一帧可能是全黑，这时必须上传批准封面；
  - 这次提交视频后没有弹定位权限请求；
  - 发布按钮在 900×765 视口的参考坐标；
  - 笔记管理 tab 是 `.tab-item`，激活态为 `tab-item--active`；
  - 重载后页面要十几到三十秒才渲染，约 4 秒时整页还是空的；
  - 「审核中」在发布后约 2 分钟内消失，具体时刻没观测到。
- 小红书 page-anatomy 文件头与 platform-constraints 的执行优先级都把 2026-10-12 的读数算进实测证据。

## [0.12.0] - 2026-10-12

本版条目来自 2026-10-11 账号「手工川」发《跳出局部最优》时的观测（先发视频号，再发 B 站）。写入前，独立 Agent
都回到会话记录逐条核对过证据；只观测到一次的现象，原文里都注明了。

### Fixed

- B 站创作声明：2026-10-11 观测到它已是必填项，初始为空，不再默认「内容无需标注」。留空投稿会被「请添加创作声明」
  拦下，现在要在终稿确认前主动选好并回读，字段表不能写「未添加」。被拦后允许再点一次的判据也写进了文档。
  同步改了 SKILL.md、`publish-gates.md` 和 B 站 page-anatomy。
- B 站主上传框：它的祖先链同时含 `upload-wrp` 和壳层类名，原表格照字面读会把它排除掉。判据改为「含 `upload-wrp`、
  `accept` 含 `mp4`、恰好命中一个」。
- `check_copy.py`：视频号话题软上限从 5 改为 10，与描述模板「5–10 个」和用户确认的样本一致，并新增两条单测。
- 视频号 page-anatomy 里指向浏览器工作流的悬空引用，改为指向「描述换行与话题空行」。

### Added

- 视频号：
  - 页面不显示账号名时，用 `auth_data` 只读接口核对账号；0×0 的「不是管理员」节点是预渲染误报。
  - 合成写入描述、之后没有真键入时，手机预览可能停在旧文案：用一组真空格加 Backspace 让预览同步。
    新增「描述预览」门禁，「一次读完字段表」也加了预览这一行。
  - 内容列表前面可能有置顶卡片，回读不能只扫前几张。
  - 「合集沿用上一条」：从列表的「合集 (N)」分页反查；合集下拉按 Esc 关不掉，要再点一次 `.post-album-display`。
- B 站：
  - 自定义标签靠回车创建，作为「Enter 需用户确认」的第二个限定例外。
  - 推荐标签不一定有「原创」：没有时在字段表记「未出现」，交用户决定。
  - 宽 toast 探针会误命中常驻文案，标签被拒以 `.tag-container` 为准。
  - 合集下拉与「创建并加入」的选择器；新建后直接选中，这一点与视频号相反。
- 浏览器工作流：`completeTaskSpace(task.id)` 不传第二个参数会抛 `requires { keep: boolean }`。

## [0.11.1] - 2026-10-06

2026-10-06 账号「手工川」发 15 分钟横版时的观测；浏览器视口约 900×765，比文档默认的 1496×731 窄。

### Fixed

- 视频号原创：主复选框点开「原创权益」弹窗后按「取消」，界面未勾而 `input.checked` 仍为 `true`。改为以「声明原创」`.form-item` 内的 `.ant-checkbox-checked` 判断当前状态，最终验收要求 class 与属性同时为真；字段表片段新增 `originalClass`。SKILL.md 原创段、`publish-gates.md` 字段表与原创声明步骤同步
- 视频号「发表」：同一个 `js()` 里 `scrollIntoView({block:'center'})` 后立刻读 rect 拿到滚动中途的值，点击静默落空。改为 `behavior:'instant'` → 等约 1 秒 → 下一轮重读 rect → 断言 `shadowRoot.elementFromPoint` 命中按钮 → 只点一次；按钮只认自身文本全等「发表」且宽度 > 0，排除隐藏弹窗里宽 0 的「直接发表」（原创推销分支）
- 提交点了没反应时，先在另开的标签页重载内容列表确认没有本次条目，才允许重试一次；不要把创建页导航走，表单会丢（SKILL.md 第 11 步与收口错误、`publish-gates.md` 单次提交）
- B 站标题：三击 + 全选 + Backspace + `Input.insertText` 后 `value` 已是新标题，计数器却停在文件名长度 `30/80`。补一组 End / 空格（`text: ' '`）/ Backspace 真按键再失焦后变为 `70/80`。标题验收改为必须满足下一轮计数器 `n === value.length`，附限定在标题附近的计数器探针
- B 站窄视口：左侧固定导航 `.cc-nav-wrp` 盖住表单左侧约 200px，页面可横向滚动，标签关闭图标的点击落到了导航上。每次 CDP 点击前先 `scrollLeft = 0`（远右的热门 chip 用 `inline:'center'`），再断言 `document.elementFromPoint` 命中目标
- `browser-workflow.md`「视口外的按钮」：保留原片段，补充滚动与读 rect 分两轮、现读视口尺寸的修正

### Changed

- `check_copy.py` 的 B 站话题专用标签名单加入 `vibecoding`（toast「当前tag为话题专用，不允许自定义添加」）；`AI编程` 作为替代被接受。新增 4 个单测
- B 站标签文档：计划里的标签已作为热门 chip 出现时（如 `深圳`、`手工艺`）点 chip，不手打

## [0.11.0] - 2026-10-02

### Added

- 小红书封面上传路径实测走通（2026-10-02，手工川-南头古城招募共创宣传片 v0.9）：真鼠标先移到附近、再移到缩略图（「设置封面」区第一个 >60px 的 img/canvas，约 113×151），约 0.9 秒后挂出 `.cover-edit-entry`；断言 `elementFromPoint` 命中后真鼠标点一次打开「设置封面」编辑器（裁剪 / 模版 / 贴纸 / 文字 / 滤镜，默认 `无模板`）；唯一的 `input[type=file][accept*="image"]` 提交批准 3:4 封面；对「完成」按钮元素语义 `.click()`；回读「封面效果评估通过，未发现封面质量问题」并在「封面预览」截图验收
- `browser-workflow.md`：`waitForAgentControl(task.id)` 正常 resolve 为 `undefined`，即控制权已归还（2026-10-02 观测）

### Changed

- SKILL.md 封面段、第 9 步小红书条目、`publish-gates.md` 小红书字段表与槽位表、README 对比表：小红书封面从「上传未实测、交用户手动上传」改为编辑器上传；保留兜底——浮层没挂出、命中断言失败或点一次编辑器没开就停下交接，不重试、不换点法
- 小红书「完成」按钮在 888px 宽视口里部分出界（x 840–908），坐标真鼠标点 x=874 关不掉编辑器，明确要求用语义 `.click()`

### Fixed

- 视频号话题写入顺序：改为「caret 收到末尾 →（非首个）`typeText(' ')` → 点 `#话题` → 不再挪 caret → `typeText(名称)` → 等约 1 秒断言 `span.topic` +1」。旧顺序在点按钮后再收 caret 到末尾，2026-10-02 描述末尾有 `"\n"` 文本节点，caret 落在换行之后，第二个话题成了纯文本 `" #深圳"`。新增「caret 紧跟 `#`」断言片段与失败清理写法；2026-08 与 2026-10-02 两次观测都保留在 `wechat-channels/page-anatomy.md`

## [0.10.0] - 2026-10-01

### Added

- add Xiaohongshu (小红书) video-note publishing
- 新增 --platform xiaohongshu：上传页限制 20GB / 4 小时、推荐 MP4 / MOV、无码率要求；标题 20 / 正文 1000 字预检
- 新增 references/xiaohongshu/page-anatomy.md 与 platform-constraints.md：tiptap 正文、# 候选话题、原创声明两步、地点搜索、封闭 shadow 的 XHS-PUBLISH-BTN、笔记管理状态回读，未实测项逐条标注
- 小红书不进默认队列：只说「发小红书」时只发小红书；继承终稿时标题按 20 字重派生、正文去掉行内话题，成片仍走平台成片映射门禁
- 小红书的 draft / schedule 在证实前也先确认终稿（暂存离开与发布同在一个封闭 shadow 宿主）
- 生成内容标注默认不勾（作者 2026-10-01 偏好）：三平台保持无需标注，确认含生成素材时在终稿确认里提示由用户当次决定，平台强制标识不移除
- 文件名平台标识：长标识子串匹配、短标识（xhs / rednote / b站）字母边界匹配，新增中文标识，修复长标识漏检
- check_copy：小红书正文行内 # 提醒；合集上限未知时报 warn collection_limit_unknown 而非阻断
- 视频号视频标注选项更新为 7 项；B 站补创作声明下拉动画坑、改标题后分区被重猜、审核期间经创作中心接口回读

## [0.9.2] - 2026-09-27

### Fixed

- `check_video.py` 的码率建议改为按平台判定：视频号保留 ≤10 Mbps 的 `video_bitrate_high` / `video_bitrate_unknown` 警告；B 站投稿页没有码率上限且会重新转码，不再报码率警告。
- 长视频或大文件把预检警告当门槛、先重压再上传的例外限定为视频号；B 站直接上传渲染母版，只有页面真的返回转码失败才进入重压方案。
- 容器建议按平台判定：视频号仍只推荐 MP4（`container_not_mp4`）；B 站按投稿页推荐接受 MP4 / MOV / MKV，其他容器报 `container_not_recommended`。
- 重压后的复检命令显式传 `--platform`，避免 B 站成片按视频号口径复检。

### Added

- 预检 JSON 新增 info 级 `notes`，人读输出显示为「提示」；B 站输出 `video_bitrate_no_platform_cap`。
- B 站约束记录 2026-09-27 投稿页原文（只限大小与时长，粉丝 ≥1000 账号 64G，无码率要求），以及 20 Mbps / 2.08 GB / 13:47 母版被误重压到 9 Mbps 的教训。

## [0.9.1] - 2026-09-06

### Fixed

- 生成内容标注按用户明确的素材来源说明和可核实制作证据判断，不再由 AI 话题、产品演示或辅助剪辑/字幕/调色推断。
- 记录乐元现场分享误标教训；未知来源先查证，实际生成/合成素材再按适用平台规则判断，保留平台自身标识。

## [0.9.0] - 2026-09-06

### Changed

- 默认平台队列固定为微信视频号 → B 站；当前请求明确指定的平台与顺序覆盖默认。
- 视频号动作及列表回读完成后再处理 B 站；前一平台阻塞时先处理具体问题，不擅自改序。
- 删除未指定平台时的泛问及 Manifest 中重复询问默认目的地的字段；条目状态查询保持原平台范围。

### Fixed

- 根据 2026-09-06 实测，跨域 iframe 的微信快捷登录无可点击 ref 时，先用最新浏览器截图定位并执行一次 `click([x, y])`，回读创建页与账号；仅真实阻塞时交接，保留原控制权和提交确认规则。

## [0.8.0] - 2026-09-01

### Added

- gate platform-specific video variants before upload
- reject sibling-platform filenames unless the user explicitly overrides reuse
- validate the project-approved output orientation without assuming every Bilibili video is horizontal
- route missing target-platform files back to lov-media-creator before opening the publisher

## [0.7.0] - 2026-08-31

### Added

- parallelize uploads and form completion with actionable handoffs
- prefer Volcengine TTS for user handoffs with a system-voice fallback
- freeze and expose exact video and cover paths before opening the publisher

## [0.6.4] - 2026-08-30

### Fixed

- correct Bilibili dual-cover canvas targeting
- persist Quill descriptions with user-source input and blur
- verify public title, description, cover, and tags on the same BV

## [0.6.3] - 2026-08-26

### Fixed

- verify published Bilibili tags
- read the Bilibili tag API and public tag nodes as an unordered exact-name set

## [0.6.2] - 2026-08-26

### Fixed

- make short-video descriptions hook-first
- preserve user-published copy across platforms and prevent duplicate submission after manual publish
- treat user-selected collections as frozen state instead of reopening the old empty field table

## [0.6.1] - 2026-08-24

### Fixed

- move global feedback policy to the shared instruction layer
- keep the Bilibili chapter timeline gate domain-specific and remove the duplicated all-Skill policy

## [0.6.0] - 2026-08-24

### Added

- add reusable feedback gate and Bilibili chapter timeline requirement
- classify user corrections before continuing, optimize reusable guidance first, invalidate prior confirmation, and require verified clickable Bilibili chapter timestamps

## [0.5.3] - 2026-08-23

### Fixed

- preserve user-edited platform descriptions
- freeze description provenance before unrelated form mutations and strengthen generated-copy quality gates

## [0.5.2] - 2026-08-21

### Fixed

- 补充视频号跨域iframe登录与B站立即投稿遮挡经验
- add guarded handoff for cross-origin wechat login iframe; note bilibili submit button occlusion (2026-08-21 EP.02)

## [0.5.1] - 2026-08-21

### Fixed

- 原创默认勾选 + 合集默认询问 + 文案以用户手改为准
- SKILL.md 原创段改为创作者账号默认勾选（用户连续多期要求后仍未自动勾）；合集默认询问归属；描述/标题以用户手改最终版为准，不在终稿确认时展示旧版

## [0.5.0] - 2026-08-18

### Added

- 把两平台的控件定位判据前置成硬规则，补齐视频号描述写法与 B 站表单真实选择器
- SKILL.md 平台差异从三条扩到四条，新增「控件类名一律从 page-anatomy 抄，不许猜」：两边都是自研组件库，antd 猜测全不命中且查不到不报错，表现为点了没反应
- SKILL.md 发布完整性门禁新增封面素材来源：从 output/covers/<ep>/ 与 output/deliverables 取，B 站 16:9 是已知缺口，禁止 ffmpeg 抽首帧顶替
- references/bilibili/page-anatomy.md 补分区/合集/封面的真实选择器表（.video-human-type / .video-season / .cover-main），以及封面 image input 在弹窗打开前不挂载、编辑页分区 disabled 不可改
- references/bilibili/page-anatomy.md 记下定位反模式：querySelectorAll('*') + innerText.includes 必然先命中最外层容器，读回值不许用 innerText 取相邻行
- references/wechat-channels/page-anatomy.md 同步定位反模式，给出 shadow root 内叶子节点 + 文本全等的写法
- references/description-template.md 新增视频号描述五条硬要求（系列全称开场、博主介绍式语气、不泄露制作术语、平铺直叙、客套收尾），与项目 AGENTS.md 的重复记录合并到此处
- SKILL.md frontmatter 把 compatibility 提到顶层，description 补齐中文触发措辞并避免折行切断 Use when

## [0.4.0] - 2026-08-18

### Added

- 从 lov-publish-wechat-channels 升级为双平台发布器 lov-media-publisher，新增 Bilibili 适配
- 新增 references/bilibili/page-anatomy.md：Vue 应用不吃合成事件（必须用原生 value setter 且 inputType 不能省）、计数器要下一轮 js() 才读得到真值、简介是 Quill 实例、svg.close 与 .hot-tag-item 只吃 CDP 真鼠标、主上传区按 upload-wrp 祖先链锚定
- 新增 references/bilibili/platform-constraints.md：16 GB / 10 小时硬限制、标题 80 与简介 2000、合集创建 20 字但编辑表单 50 字、话题专用标签的实测拒绝名单、稿件发布后可编辑
- 记录 B 站封面是两个独立槽（4:3 与 16:9），列表/空间/信息流用的是 16:9，唯一可信验证是公开接口的 pic 字段
- 记录合集撞字数上限时的判据：先分别读创建表单与编辑表单的 maxLength，默认用系列全称，降级用短名必须有实证
- scripts/check_video.py 与 scripts/check_copy.py 新增 --platform，硬限制与文案规则按平台取；check_copy.py 另增 --title 与 --collection-stage
- 新增 skill.yaml 与 references/skill-composition.md，通过 lov-skill-creator 的源校验

### Changed

- references/browser-workflow.md 与 references/publish-gates.md 去平台化，只保留两平台都成立的部分；平台专有内容下沉到 references/wechat-channels/ 与 references/bilibili/
- 视频号专有的页面结构与约束移到 references/wechat-channels/ 子目录
- 发布门禁按可逆性分口径：视频号不可逆，B 站可编辑但改完要重新点「立即投稿」

## [0.3.0] - 2026-08-17

### Added

- 发布前必须由用户确认终稿，并把实测的平台约束与页面结构沉淀成门禁
- 新增 awaiting_confirmation 状态：publish 在字段表全项通过后停下，发系统通知与语音播报，把终稿（含被平台改写的字段）交给用户确认后才提交
- 新增 scripts/check_copy.py：离线预检短标题 16 字上限与禁用逗号、合集 10 字上限且不可修改、描述里的纯文本 # 不算话题
- 新增 scripts/notify_user.py：系统通知 + 语音播报，用于扫码与终稿确认两个卡点；通知失败不阻塞发布
- 新增 references/page-anatomy.md：wujie shadow root 结构、控件定位表、穿透定位文件输入、预渲染弹窗按可见性过滤、一次读完字段表的探针
- 封面槽位数改为按 .cover-tips 实测，不再假设固定两个；实测当期只有一个 3:4 槽，4:3 无上传入口
- 记录 ego-browser helper 签名坑：handOffTaskSpace/waitForAgentControl 需传 id，captureScreenshot 收路径字符串

## [0.2.0] - 2026-08-15

### Added

- 记录平台转码拒绝后的重压方案与浏览器交互修复
- 新增 references/encoding-recipes.md：CRF 抽样定码率预算、2-pass 重压参数与重压后验证
- 禁止交出控制权后自行 takeOverTaskSpace 抢回，交出时通知并后台轮询
- 补充 contenteditable 描述区的清空重建写法，避免过期 caret 产生脏文案
- 话题必须由「#话题」按钮生成标签节点，纯文本 # 不算通过
- 视口边缘按钮改用元素自身 scrollIntoView + click，坐标点击会静默失效
- 封面按每个比例独立居中裁切，新增近黑边带检测，禁止填充留黑条
- 重发场景禁用文件名/时长/首帧做指纹，改用提交时间、标题、话题或新封面

## [0.1.0] - 2026-08-14

### Added

- add complete publish metadata and cover safety gates
- verify original terms and final checkbox state before submission
- preserve the review page when requested and prevent duplicate submit attempts

## [0.0.3] - 2026-08-11

### Fixed

- Switch 发布流程到 ego-browser task space
- 更新浏览器工作流为 ego-browser 的 snapshot/upload/回读步骤

## [0.0.2] - 2026-08-11

### Fixed

- 补齐发布器触发契约并通过 canonical source validation
- 将 metadata.tags 标准化为 YAML 列表
- 保留标准 compatibility 元数据并加入 Triggers/non-trigger 条件

## [0.0.1] - 2026-08-11

### Fixed

- 确保重发时沿用已确认的标题、描述、话题和原创设置并逐项回读
- 补充子 frame/shadow DOM 上传控件的动态定位回退
- 将原创审核中等列表状态明确归类为 platform_pending
