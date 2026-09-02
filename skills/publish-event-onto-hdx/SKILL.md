---
name: lov-publish-event-onto-hdx
description: >
  诊断活动行活动的曝光问题：读取分类与标签现状、核查分类页可见性与排名、给出标签与
  刷新置顶建议。Trigger: 活动行分类找不到、活动行标签、活动行排名、活动行曝光、
  hdx event visibility, hdx category not showing。
license: MIT
compatibility: >
  ego-browser（继承用户已登录的活动行会话）；Python 3.8+；无需额外凭据。
depends_on:
  - lov-branding-consistency
metadata:
  author: markshawn2020
  version: "0.3.0"
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
| ~~`/myevent/edit?id=<id>`~~（缺 view 参数） | — | 表单不完整，无分类字段 |
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
| 后台位置 | `edit?view=editbase` 的 `.edit-btn[0]` | 未确认在何处编辑 |

改「分类标签」不会改动 `Tag`。实测案例：用户把分类标签改为 AI 后，前台
`ativityJson.Tag` 仍是原值 `Agent,DeepSeek,Harness,工作流自动化`，`UpdateDate` 未变。
因此**基于 `Tag` 给「标签替换建议」时，必须先确认用户能在哪里编辑 `Tag`**，
不要假设改分类标签就能改 `Tag`。

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
2. **`Tag` 是否包含零曝光词？** → 对照上方分布给出建议，但**先说明 `Tag` 与
   「分类标签」是两个字段**，且 `Tag` 的编辑入口尚未确认，不要许诺能改。
3. **当前分类页排名如何？** → 查 `v`（热门点击）排序下的页面位置。

### Step 3: 输出诊断报告

向用户呈现：

- 当前 Category、分类标签、`Tag` 三者的值（明确区分后两者）
- 分类页可见性结论（可见/不可见/原因）
- 热门点击排序下的排名
- `Tag` 关键词建议，并说明其编辑入口尚未确认

如需改动分类，按「分类标签字段：已实测定位」一节的路径与选择器处理。
曝光问题还要评估「刷新与置顶」的配额。

**禁止编造观测结果。** 本 Skill 的历史教训：Agent 曾把从 DOM 片段推想出的
页面路径、`.edit-btn` 数量和字段位置当作实测结果写入本文件，路径实为 404。
凡未在本次会话真正打开并读取过的页面，一律标注「未确认」，不得写成已验证。

### Step 4: 验证（可选）

用户完成后台修改后，重新读取 `ativityJson` 确认 Category 已变更，
并重新查排名，以回读结果报告最终状态。

### Step 5: 持久化

将本次诊断的活动 URL 和建议标签写入 profile records：

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" record \
  skills.lov-publish-event-onto-hdx.records.last_event_url "<url>" --confirm
```

## Dependencies

- `ego-browser` — 浏览器自动化，继承用户已登录状态
- Python 3.8+（仅 profile_store.py 使用）
