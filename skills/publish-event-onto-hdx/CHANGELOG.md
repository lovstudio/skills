# Changelog

## [0.4.0] - 2026-09-04

### Added

- record the SaveEvent category-wipe mechanism and the UEditor image replacement procedure
- add a mandatory editbase re-submit guard and post-write readback step
- resolve the Tag edit-entry question: no backend form exposes it
- add README install command and two new usage examples

## 0.3.0

修正 0.2.0 中「分类字段位置未确认」的空缺，并订正一处更严重的错误：Agent 曾把
推想出的页面路径当成实测结果写入文档。

- **定位分类标签字段（实测）**：`/myevent/edit?view=editbase&id=<id>`。关键是
  `view=editbase` 参数——0.2.0 只试了裸 `/myevent/edit?id=`，表单不完整因而误判
  「无分类字段」。
- **字段名订正**：实际是「分类标签」四字连写、**单选**（页面原文「可最多选择 1 个
  分类标签」）。此前搜索的「活动分类」「活动标签」在页面中不存在。
- **定位方式**：该页 `.edit-btn` 共 2 个，分类标签是第 0 个；纯 SVG 图标无文字，
  文本搜索必然漏掉，必须按 class 查。组件 scope `data-v-f6186597`。
- **新增关键区分**：「分类标签」（单选，控制分类归属）与 `ativityJson.Tag`
  （多值关键词）是两个不同字段。实测：改分类标签为 AI 后 `Tag` 与 `UpdateDate`
  均未变。0.1.0–0.2.0 的「标签替换建议」把两者混为一谈，前提有误，已订正。
- **记录失效路径**：`/myevent/manage?id=<id>` 返回 404。此路径曾在一次交付中被
  当作已验证结果写入文档，实为编造。
- **新增防幻觉约束**：未在当次会话真正打开读取过的页面一律标注「未确认」。

## 0.2.0

修正首版中两个未经验证就写下的断言。

- **修正错误的后台路径**：首版声称分类字段在「主办方中心 → 编辑活动 → 活动分类 / 活动标签」。
  实测 `/myevent/edit?id=<id>` 表单（滚动 8 屏，全文 1053 字符）**不含分类与标签字段**，
  概览页和推广页也没有。该路径已删除，改为标注「位置未确认」并给出运行时查找顺序。
  （0.3.0 补注：真实原因是缺 `view=editbase` 参数，而非字段不存在。）
- **修正 Step 0 死循环**：首版对「帮我发布新活动」会索要一个尚不存在的 `event/<id>` URL。
  现在先判断请求类型，创建类请求指向 `/createv3` 并说明本 Skill 不覆盖创建流程。
- **收窄路由描述**：移除 `发活动行` / `publish event on hdx` 等会招揽创建类请求的触发语，
  description 改为聚焦曝光诊断。
- **新增「后台路径（已实测）」章节**：记录实测路径与状态，含失效路径
  `/host/events`（重定向到首页）。
- **新增刷新与置顶机制**：`/myevent/promote?id=<id>&tab=8` 的刷新（曝光 +87%）与
  置顶（曝光 +200%，24 小时）是影响「综合排序」的直接杠杆，分类只解决可见性。

## 0.1.0

- Initial local Skill source.
