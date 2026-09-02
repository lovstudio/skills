# Skill Group Composition

## Nearby Skills Inspected

| Skill | Classification | Decision |
|---|---|---|
| `lov-event-curator` | not composed | 策划活动内容与嘉宾问题，不涉及平台发布或曝光诊断 |
| `lov-event-poster` | not composed | 生成活动海报图，不涉及后台分类设置 |
| `lov-fill-web-form` | upstream atom（可选） | 可从知识库预填报名表；本 Skill 聚焦诊断，不做自动填表 |
| `lov-media-publisher` | not composed | 负责微信视频号/B站视频发布，不涉及活动行；同为 ego-browser 模式，是设计参照 |
| `ego-browser` | runtime dependency | 继承已登录会话读取活动页 JS 上下文，是本 Skill 的执行基础 |

## Atomic Handoffs

```text
（可选）lov-event-curator
  活动策划文案、嘉宾问答稿
              |
              v
（可选）lov-event-poster
  活动宣传海报
              |
              v
lov-publish-event-onto-hdx      ← core atom，本 Skill 的职责
  诊断活动行分类/标签配置，给出修复建议
              |
              v
用户在主办方后台手动修改 Category 和 Tag
              |
              v
本 Skill 回读验证排名变化
```

## Overlap Decisions

无重叠：没有其他 Skill 拥有"读取活动行活动 ativityJson + 诊断分类可见性 + 给标签建议"这个完整输出契约。

## Composition Decision

**Single Skill**。诊断、建议、回读验证是同一用户可见结果的三个阶段，共享同一个活动 URL 状态，无需拆分为独立 Kit 模块。ego-browser 是运行时依赖，不是独立可组合阶段。
