# Skill Group Composition

## Nearby Skills Inspected

2026-09-06 根据实际入口的输入、输出与非触发条件核查。

| Skill | 分类 | 实际边界 |
| --- | --- | --- |
| frontend-design 0.2.0 | overlap | 已有视觉与产品交互方法，工作室整理版承接这项结果 |
| lov-frontend-design | core atom | 需求、代码与素材进入，输出可用前端及验收 |
| lov-branding-consistency | upstream atom | 可见文案的语境门禁，唯一声明的外部文案依赖 |
| lov-oh-my-landingpage | overlap | 品牌定位、商业叙事与转化为主时直接使用它 |
| lov-app-professional-design | not composed | 启动、缓存、数据桥与并发性能架构，排除仅视觉改动 |
| lov-better-css | not composed | CSS/Tailwind 清理，不能代替内容与交互设计 |
| lov-frontend | not composed | uni-app 网关请求封装，不是通用设计 |

## Atomic Handoffs

1. `lov-branding-consistency` 接收文案、受众与品牌上下文，交还文案或删除决策；它负责
   语境，本 Skill 负责落入组件后的排版、状态与交互。
2. Landing Page 已完成策略时可交接确认过的叙事、资产与约束。只有另有具体组件任务
   才使用本 Skill，不为一个完整落地页重复运行两套总控。
3. 核实的图像、音视频与正文以文件、元数据、使用范围交接。媒体制作与研究不成为
   隐藏 sibling 依赖，缺失能力按宿主解决或明确缺口。
4. 用户要求发布时交接源码、依赖、资产与验收给项目发布流程；渠道结果由发布流程
   验收，不能从本地构建推断已上线。

## Overlap Decisions

整理现有 `frontend-design` 方法，采用 `lov-frontend-design` ID、独立真源与 Profile。
保留旧安装；需要工作室维护版时明确选择新 ID。新包不依赖旧目录，不声称其他项目
官方发行。来源和许可边界见 `references/provenance.md`。

不扩展性能架构 Skill 或 uni-app 网关模块，二者名字相近但输出不同。完整品牌转化链
仍使用原 Landing Page Kit，局部产品界面与教学展示由本 Skill 负责。

## Composition Decision

Single Skill，instruction-first。语义、视觉、媒体与验收共同完成一个前端结果，按需
参考足够，不拆独立安装阶段。Profile 与校验脚本是确定性配套工具，不据此拆 Kit。
除可见文案门禁外不声明外部 sibling 必需依赖。
