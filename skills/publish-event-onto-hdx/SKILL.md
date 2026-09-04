---
name: lov-publish-event-onto-hdx
description: >
  诊断并修改活动行已发布活动：核查分类页可见性与排名、替换详情正文配图，并守住
  后台保存会清空分类这一平台陷阱。Trigger: 活动行分类找不到、活动行分类没了、
  活动行排名、活动行曝光、活动行换海报、hdx category not showing, hdx category reset。
license: MIT
compatibility: >
  ego-browser（继承用户已登录的活动行会话）；Python 3.8+；无需额外凭据。
depends_on:
  - lov-branding-consistency
metadata:
  author: markshawn2020
  version: "0.4.0"
  card_standard: lovstudio/skill-card/v1
  content_class: microcopy
  tags:
    - huodongxing
    - event
    - seo
    - china-platform
---

# lov-publish-event-onto-hdx

帮助在活动行（huodongxing.com）完成活动的分类设置、标签优化和曝光排名核查。

## Triggers

### Activate when

- 用户说"帮我看看活动行上的活动""活动行里找不到自己""活动行分类没设"
- 用户说"活动行标签怎么设""活动行排名""活动行曝光"
- 用户说"活动行分类怎么没了""刚保存完分类就没了"
- 用户说"换掉活动行详情里的海报""替换活动行正文配图"
- 用户说"publish event on hdx""fix hdx category""hdx event not showing"
- 用户提供一个活动行活动链接，想知道为什么在分类页找不到

### Do not activate when

- 用户要**从零创建**一个新活动 → 本 Skill 不覆盖创建流程，见 Step 0 的分支处理
- 用户要发布其他平台内容（视频号、B站、小红书）→ 使用 `lov-media-publisher`
- 用户要生成活动海报或图文 → 使用 `lov-event-poster`
- 用户要策划活动流程或嘉宾问题 → 使用 `lov-event-curator`

## Key Knowledge

### 分类（Category）是曝光门禁

活动行前台所有分类导航页（IT互联网、创业、AI……）由 `Category` 字段控制，
**Category=0 的活动在任何分类页都不会出现**，这是最常见的曝光问题根因。

分类编号（从大规模抓取数据推断）：

| Category | 含义（推测）         | 占比 |
|----------|---------------------|------|
| 11       | IT互联网/AI/科技类  | 最多 |
| 12       | 生活方式/兴趣       | 次多 |
| 22       | 教育培训            |      |
| 14       | 行业培训/职场       |      |
| 0        | **未分类（不可见）** |      |

AI/技术类活动选 Category=11。

### 分类导航的 URL 机制

`/events?orderby=o&tag=AI&city=上海` 不是精确标签匹配，而是 Category + 标题 + 标签的混合检索。
不需要把标签精确写成导航词（如"IT互联网"），活动行全站无任何活动把"IT互联网"作为标签。

### 排序参数

| orderby | 含义     | 新主办方建议 |
|---------|----------|------------|
| o       | 综合排序 | 不利，按主办方权重（粉丝/金牌/历史）排 |
| n       | 最新发布 | 适合发布后短期冲量 |
| v       | 热门点击 | 最直观反映真实流量，用来自查排名 |
| r       | 最多参与 | 需要历史报名数支撑 |

### `Tag` 关键词分布（基于 3839 个活动的真实抓取）

**注意**：这些是 `ativityJson.Tag` 的多值关键词，与单选的「分类标签」是不同字段，
见下文「关键区分」。给建议前先确认 `Tag` 的编辑入口。

高频可用标签（括号内为全站使用量）：人工智能(194)、AIGC(105)、AI(44)、
AI赋能(41)、AI智能体(37)、Agent(33)、AI Agent(33)、AI应用(30)、大模型(24)

低效标签（等于零曝光）：Harness(1)、工作流自动化(2)、任何导航词如"IT互联网"(0)

## 后台路径（已实测）

2026-09-02 在真实账号上逐页读取的结果。**不要凭记忆推测路径。**

| 用途 | 路径 | 状态 |
|---|---|---|
| 主办方管理中心 | `/console/home` | 已验证 |
| 我的活动列表 | `/console/eventadmin` | 链接已确认 |
| 创建新活动 | `/createv3` | 链接已确认 |
| 编辑活动（完整表单） | `/myevent/edit?view=editbase&id=<id>` | 已验证，**含分类标签字段** |
| `/myevent/edit?id=<id>`（缺 view 参数） | — | **危险**：表单不完整，且保存会清空分类与主办方，见下节 |
| ~~`/myevent/manage?id=<id>`~~ | — | 404「该页面已经迷失了」 |
| 活动概览 | `/myevent/home?id=<id>` | 已验证，无分类/标签 |
| 推广（刷新/置顶） | `/myevent/promote?id=<id>&tab=8` | 已验证 |
| ~~`/host/events`~~ | — | 不存在，重定向到首页 |

### 分类标签字段：已实测定位

2026-09-02 实测确认，位于 `/myevent/edit?view=editbase&id=<id>`。

**「分类标签」是一个字段，四字连写，单选。** 页面原文：「分类标签可最多选择 1 个分类标签」。
不要搜「活动分类」或「活动标签」——那两个词在页面里不存在。

定位方式：该页 `.edit-btn` 只有 2 个，分类标签是**第 0 个**（`querySelectorAll('.edit-btn')[0]`）。
它是纯 SVG 图标按钮、无文字，因此**文本搜索必然漏掉，必须按 class 查**。
组件 scope 为 `data-v-f6186597`。

### 关键区分：「分类标签」≠ `ativityJson.Tag`

这是两个不同字段，不要混为一谈：

| | 分类标签 | `Tag` |
|---|---|---|
| 数量 | 单选，1 个 | 多值，逗号分隔 |
| 作用 | 决定分类页归属（对应 `Category`） | 站内搜索与长尾关键词 |
| 后台位置 | `edit?view=editbase` 的 `.edit-btn[0]` | **后台无录入入口（2026-09-04 实测）** |

改「分类标签」不会改动 `Tag`。实测案例：用户把分类标签改为 AI 后，前台
`ativityJson.Tag` 仍是原值 `Agent,DeepSeek,Harness,工作流自动化`，`UpdateDate` 未变。

`Tag` 的编辑入口问题已在 2026-09-04 结案：**两个编辑表单都没有该字段**，
页面全文搜不到「标签」「分类标签」「关键词」任一词作为可编辑项。它只在保存请求里被
表单模型回显（并且会被截断，见下节）。多值 `Tag` 最可能是发布时 `createv3` 流程写入的，
**但这一点未验证，不得当作结论告诉用户**。

因此**不要向用户承诺可以修改 `Tag`**。给标签建议时只能说明现状与影响，
或者建议在下次创建活动时于 `createv3` 流程里填好。

### 致命陷阱：基本信息页保存会静默清空分类（2026-09-04 实测）

**`Category` 不是一个可直接写入的字段，它由服务端从 `Setting.HdxTags`（分类标签）派生。**
两个保存入口提交的字段集不同，其中一个会把分类连根拔掉：

| | `/myevent/edit`（基本信息页） | `/myevent/edit?view=editbase` |
|---|---|---|
| 端点 | POST `/myevent/SaveEvent` | 连发 5 个 POST，末尾也是 `SaveEvent` |
| `Setting.HdxTags` | **整个 key 不存在** → 服务端写 null → `Category=0` | `Setting.HdxTags=<值>` → 分类正常 |
| `Organizers` | `Organizers= `（一个空格）→ 写 null | `Organizers=<orgId>` |
| `Tag` | **只提交最后一个关键词** → 多值被永久截断 | 回显当前值，不恢复多值 |
| `Category` | `Category=`（空） | `Category=0` 与 `Category=` 各出现一次，均被忽略 |

派生关系的证据：editbase 的 payload 里 `Category` 只有 `0` 和空值，但因为带了
`Setting.HdxTags=AI`，落库结果是 `Category:11`。所以**永远不要试图直接写 `Category`**。

`Tag` 截断在两个独立活动上复现：库里 4 个关键词，基本信息页只提交末位一个
（`Agent,DeepSeek,Harness,工作流自动化` → `工作流自动化`；
`AI,Agent,一人公司,创业复盘` → `创业复盘`）。截断后无法恢复。

**强制守则：任何一次从 `/myevent/edit` 基本信息页点「保存活动信息」之后，
必须立刻再去 `?view=editbase` 提交一次，并回读公开页确认三个字段。**
这与用户填了什么无关——只要走那个入口保存，分类必然归零。

### 另一个静默失败：必填字段加载为空

编辑页的必填字段（实测为「详细地址」）经常**加载成空值**。此时点保存
**一个网络请求都不会发出**——前端校验直接拦截，没有红框、没有 toast，
页面只是默默滚回该字段。

不要把「点了没反应」判断成保存成功，也不要判断成按钮坏了。诊断方法：

```js
// 在保存前 hook 住所有非 GET 请求；有 payload 说明校验通过，没有则是被拦截
window.__cap = [];
const of = window.fetch;
window.fetch = function (input, init) {
  const u = String(typeof input === 'string' ? input : (input && input.url) || '');
  const m = String((init && init.method) || 'GET').toUpperCase();
  if (m !== 'GET') {
    let b = init && init.body;
    if (b instanceof FormData) b = [...b.entries()].map(([k, v]) => k + '=' + String(v).slice(0, 240)).join('&');
    window.__cap.push({ url: u, body: typeof b === 'string' ? b : String(b) });
    return new Promise(() => {});   // 阻断：只观察，不写入
  }
  return of.apply(this, arguments);
};
```

同一段 hook 也是**在真正写入前预演一次保存**的标准手法：先阻断并读出 payload，
确认 `Setting.HdxTags` / `Organizers` / `Tag` 是否会被破坏，再决定要不要真的保存。

### 替换活动详情正文里的配图（UEditor）

活动详情正文是 UEditor，图片替换分三步，全部实测：

1. **上传**：POST `/ueditor/ue_handler?action=uploadimage`，字段名 `upfile`，
   上限 `imageMaxSize = 2048000`（约 2 MB，超了要先压）。
   返回 `{"state":"SUCCESS","url":"/file/ue/...jpg",...}`，
   对外完整地址是 `http://cdn.huodongxing.com` + 该 `url`。
2. **换 src**：编辑器 iframe 是 `#ueditor_0`。**必须同时改 `src` 和 `_src` 两个属性**——
   UEditor 序列化时读的是 `_src`，只改 `src` 会导致 `getContent()` 仍输出旧地址：

   ```js
   const d = document.getElementById('ueditor_0').contentDocument;
   const img = [...d.querySelectorAll('img')].at(-1);
   img.setAttribute('src', NEW_URL);
   img.setAttribute('_src', NEW_URL);   // 缺这行，改动不会进入 getContent()
   // 校验：window.UE.instants['ueditorInstant0'].getContent().includes(NEW_URL)
   ```

3. **保存**：走基本信息页的保存按钮——因此**必然触发上面的分类清空陷阱**，
   保存后必须补一次 editbase 提交。

### 曝光的另一条杠杆：刷新与置顶

`/myevent/promote?id=<id>&tab=8` 提供两个直接影响「综合排序」的机制（页面权益说明原文）：

- **刷新**：曝光量提升 87%，以「最新」标识在分类列表「综合排序」中展示（仅展示最新的 2 个）
- **置顶**：曝光量提升 200%，以「优选」标识在综合排序中展示 24 小时

两者都受账号等级配额限制（认证版每日刷新次数可能为 0，需升级或购买置顶卡）。
对新主办方而言，这是绕过「综合排序按主办方权重排」的可用手段——分类设置只解决
可见性，刷新和置顶才影响综合排序的位置。

## User Profile (cross-session)

读取 `user-profile/v1` 共享 Profile，从 `skills.lov-publish-event-onto-hdx.records`
取历史活动 URL 和标签选择记录。用户直接说出的品牌信息或常用标签，通过
`scripts/profile_store.py` 持久化到 `records` 命名空间。

## Skill Group Composition

见 `references/skill-composition.md`。

## Workflow

**按顺序执行；每步先读状态，再行动，再回读验证。**

### Step 0: 判断请求类型，再解析输入

**先分支，不要直接要 URL。**

- **已有活动做诊断** → 从用户消息或 `records.last_event_url` 取 `huodongxing.com/event/<id>`，进入 Step 1。
- **要从零创建新活动** → 本 Skill 不覆盖创建流程。明确告诉用户创建入口是
  `https://www.huodongxing.com/createv3`（主办方管理中心 → 创建活动），
  由用户自行创建；创建完成拿到活动 URL 后，再回到本 Skill 做曝光诊断。
  **不要向用户索要一个尚不存在的 URL。**

### Step 1: 读取当前状态

用 ego-browser 打开活动页，在页面 JS 上下文读取 `ativityJson`：

```js
(() => {
  const a = typeof ativityJson !== 'undefined' ? ativityJson : null;
  return JSON.stringify({
    id: a && a.Id,
    category: a && a.Category,
    tag: a && a.Tag,
    title: a && a.Title,
    updated: a && a.UpdateDate,
    visits: a && a.VisitNumber,
  });
})()
```

若页面被极验拦截（title 含"哎呀，访问太快了"），交接给用户完成滑块验证后继续。

### Step 2: 诊断

依次检查：

1. **Category 是否为 0？** → 必须在主办方后台设置分类，否则在所有分类页不可见。
2. **`Tag` 是否包含零曝光词？** → 对照上方分布说明现状，但**先说明 `Tag` 与
   「分类标签」是两个字段**，且后台无 `Tag` 录入入口（已实测），**不要许诺能改**。
3. **当前分类页排名如何？** → 查 `v`（热门点击）排序下的页面位置。

### Step 3: 输出诊断报告

向用户呈现：

- 当前 Category、分类标签、`Tag` 三者的值（明确区分后两者）
- 分类页可见性结论（可见/不可见/原因）
- 热门点击排序下的排名
- `Tag` 关键词现状说明，并明确后台无法修改

如需改动分类，按「分类标签字段：已实测定位」一节的路径与选择器处理。
曝光问题还要评估「刷新与置顶」的配额。

**禁止编造观测结果。** 本 Skill 的历史教训：Agent 曾把从 DOM 片段推想出的
页面路径、`.edit-btn` 数量和字段位置当作实测结果写入本文件，路径实为 404。
凡未在本次会话真正打开并读取过的页面，一律标注「未确认」，不得写成已验证。

### Step 3.5: 写入前确认（任何改动线上活动的操作）

活动行的活动是**已发布、有人报名的公开页面**，任何后台保存都是对外写入。
动手前用 `AskUserQuestion` 确认一次，问题里必须包含：要改哪个字段、改成什么值、
以及本次保存会顺带影响什么（分类被清空、`Tag` 被截断）。

改动前**先抄下当前的 `Category` / `Setting.HdxTags` / `Organizers` / `Tag` 四个值**，
作为回读比对的基线。用户没有明确同意就不要保存。

### Step 4: 写入后强制回读（不可跳过）

**只要本次流程点过 `/myevent/edit` 基本信息页的保存，就必须补一次
`?view=editbase` 提交**，否则分类已经归零。然后重新抓公开页 `ativityJson` 逐项比对：

| 字段 | 期望 |
|---|---|
| `Category` | 非 0，且与改动前一致（或为本次有意变更的值） |
| `Setting.HdxTags` | 非 null |
| `Organizers` | 非 null |
| `Tag` | 与基线一致；若已被截断，如实告知不可恢复 |

**「保存动作成功」不等于「线上正确」。** 以公开页回读为准，不以点击成功为准。
发现字段被清空要主动报告，不要等用户发现。

### Step 5: 持久化

将本次诊断的活动 URL 和建议标签写入 profile records：

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" record \
  skills.lov-publish-event-onto-hdx.records.last_event_url "<url>" --confirm
```

## Dependencies

- `ego-browser` — 浏览器自动化，继承用户已登录状态
- Python 3.8+（仅 profile_store.py 使用）
