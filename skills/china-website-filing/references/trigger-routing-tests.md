# Trigger routing tests

| Prompt | Expected route | Reason |
| --- | --- | --- |
| “备案前检查一下域名实名和材料” | `filing-readiness` | 目标是提交前准备，不是审核状态。 |
| “继续 ICP 备案，看看短信核验到哪了” | `icp-filing` | 目标是接入商、工信部与管局链路。 |
| “备案通过了，部署并绑定域名” | `domain-cutover` | 已满足 ICP 上游门，目标是上线验收。 |
| “继续公安备案，最终提交前让我确认” | `public-security-filing` | 目标是全国互联网安全管理服务平台申请。 |
| “每天检查备案状态，没变化就静默” | `filing-monitor` | 目标是有历史比较和通知策略的周期巡检。 |
| “给网站生成隐私政策和服务条款” | non-trigger → `lov-legal-pages` | 不涉及备案状态、权威页面或上线门。 |
| “把桌面 App 打一个生产包” | non-trigger → `lov-dev-to-prod` | 不是网站备案或备案后域名开放。 |

自动测试验证每个正向短语和非触发条件存在于对应模块；语义路由仍由宿主模型结合上下文完成。
