# 算法演示台 · Algorithm Theater · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

把算法、数据结构或信息流程做成「逐步演示」的可交互可视化。输入是算法概念或
示例数据，输出是自包含单文件 HTML，支持播放/暂停、逐帧前进后退、变速与键盘
演示，每帧附一句中文解说与伪代码高亮。

## Owner

- 手工川工作室（Lovstudio）
- 联系方式：https://lovstudio.ai

## License / Terms

MIT。产出的 HTML 与模型可直接用于学习、教学与演示；引用时保留来源说明即可。

## Use Case

- 受众：算法学习者、讲师、汇报者
- 输入：算法名/概念描述，或示例数据
- 任务：把 KMP、快速排序、Dijkstra、背包、拓扑排序等建模为逐帧步骤，产出
  可离线打开的演示页

## Deployment Geography

本地 python3 运行两个脚本；产物为浏览器可直接打开的 HTML（file:// 即可），
无云端依赖。

## Requirements / Dependencies

- python3（运行 `validate_viz.py` / `build_viz.py`）
- 无凭证、无 npm、无外部 CDN

## Known Risks and Mitigations

- 帧逻辑凭想象编写与实际不符 → 规范要求先在算法上真实跑一遍再逐帧记录；
  校验器强制引用一致性（节点 id、边 id、codeLine）。
- 帧数过多演示疲惫 → 校验器对 >60 帧告警，规范建议 5–40 帧。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Step model specification](references/step-model.md)
- [Demo engine contract](references/demo-guide.md)

## Skill Output

- 类型：自包含单文件 HTML（内联 CSS/JS 与数据）+ 帧模型 JSON 中间产物
- 布局：sequence / network / matrix / bars
- 帧：每帧 active / settled / values / note / codeLine
- 校验：`validate_viz.py` error=0，headless 浏览器无报错

## Skill Version

0.1.0

## Ethical Considerations

产物用于教学与演示，不采集私密数据。用户提供的真实业务数据仅在其本人项目内
使用；算法逻辑以公开教科书定义为基准。

## LovStudio Evidence

### User Cases

见 [`cases/cases.json`](cases/cases.json)。案例为真实执行记录：
输入来自「手工川图解算法」项目 `src/lib/algorithms.ts` 的二分查找、拓扑排序、
冒泡排序模式，经本 Skill 建模 → `validate_viz.py` → `build_viz.py` → headless
渲染验证。

### Dimension Map

见 `skill-card.yaml` 的 `dimensions`：correctness / effectiveness / efficiency，
均已 verified。

### Pricing Basis

见 [`pricing-card.yaml`](pricing-card.yaml)。免费，作为 Lovstudio 学习产品线的
开源能力对外提供；进入商业培训或需要 SLA 时复评。

### Distribution

- free: github / lovstudio（已备好，未声明发布）
- paid: workbuddy / skillpay（未使用）
