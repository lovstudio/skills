# 竞品调研 · Competitor Research · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

对用户点名的产品、公司或开源仓库，交付结论先行、每个判断都能回溯到证据的竞品调研报告。
覆盖四个模块：差异对比、血缘溯源（是否 fork、拷贝或改写）、含金量、投资视角。开源对象用
随包 `scripts/repo_evidence.py` 从 GitHub 数据与全量 Git 历史取证。

## Owner

- Team: Lovstudio
- Contact: https://lovstudio.ai

## License / Terms

MIT。调研只使用公开资料；用户需自行遵守被调研平台的服务条款。

## Use Case

- Audience: 需要判断竞品、开源项目来源与价值的产品负责人、开发者、投资与研究人员。
- Supported input: 两到五个点名对象（`OWNER/REPO`、官网域名或公司名）与具体问题。
- Expected task: 回答“区别是什么”“是不是基于某项目做的”“含金量如何”“有没有投资价值”。

## Deployment Geography

global。在支持 Agent Skills、具备网页检索能力的宿主中运行；脚本在本地 shell 执行。

## Requirements / Dependencies

- 运行时：Python 3.8+（仅标准库）、git；`facts` 子命令需要已登录的 `gh` CLI。
- Skill 依赖：`lov-branding-consistency`（报告属于读者可见文本）。
- 凭据：只使用用户已有的 `gh` 登录，本 Skill 不存储任何凭据。

## Known Risks and Mitigations

| 风险 | 缓解 |
| --- | --- |
| 把启发式热度指标写成“刷星”断言 | 指标只作相对比较；抽样不可用时记为无法核实 |
| 检测失效时把“没查到”写成“无关系” | 拒绝部分或浅克隆；`--source-all-history`；强制反向对照；证据不足写“无法判断” |
| 同名包或山寨站点混入 | Step 1 先确认对象唯一标识，核对包维护者与仓库链接 |
| 投资视角被读成投资建议 | D 模块固定免责声明，不给买卖、仓位、估值目标或收益预期 |
| 维护者个人信息泄露 | 脚本不输出邮箱；不追查个人身份 |

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Research playbook](references/research-playbook.md)
- [Skill group composition](references/skill-composition.md)

## Skill Output

- 类型：竞品调研报告（对话内或 Markdown 文件），以及 `facts`、`history`、`loc`、`lineage` 的 JSON 证据。
- 参数：模块 A–D；`--star-sample`、`--alias`、`--source-all-history`、`--term`、`--identifier`。
- 验收：每个数字都能在证据账本找到来源与绝对日期；血缘结论与证据等级一致并做过反向对照；
  没能核实的项单列并保留原始错误；D 模块含免责声明。

## Skill Version

0.1.0

## Ethical Considerations

只使用公开资料与用户授权访问的页面，不绕过登录、付费墙或反爬措施。不断言无证据支撑的造假
行为，不输出维护者邮箱或追查个人身份。投资视角只做业务与技术尽调，不构成投资建议。

## LovStudio Evidence

### User Cases

见 [`cases/cases.json`](cases/cases.json)：两个热门开源仓库的区别、血缘、含金量与投资视角，
三轮追问共用同一证据账本；2026-11-15 用 `repo_evidence.py` 重跑，正反对照均通过。

### Dimension Map

| 维度 | 状态 | 证据摘要 |
| --- | --- | --- |
| 血缘判定准确 | verified | 源为疑似来源仓库：0/308 文件、0 标识符提交；源为起源提交点名的仓库：19/709 文件相同、2 个提交命中 |
| 指标可复现 | verified | fork/star、每千 star issue、贡献者数与人工一致；合并别名后的维护集中度一致，并补出遗漏的零提交月份 |
| 证据诚实 | verified | stargazer 404 / edges 为空、OSSInsight 500、PyPI 同名包均单列为无法核实 |
| 回答可用 | partial | 三轮均结论先行、用户没有纠正；没有明确验收评价 |
| 取证效率 | verified | 四个子命令替代十余条手工命令；lineage 在数百个提交的仓库上约 3 到 4 秒 |

### Pricing Basis

见 [`pricing-card.yaml`](pricing-card.yaml)。首版免费：方法论加只读取证脚本，没有独占数据或托管成本。
积累三个以上已验收案例或加入付费数据源时复评。

### Distribution

| 渠道 | 类型 | 状态 |
| --- | --- | --- |
| 本地安装 | local | 已安装并校验 |
| lovstudio | free | pending（2026-11-16 准备登记为 0 Credits 免费条目；目录合并、详情页与安装均未核验） |
| github | source | private-source（公开副本是聚合仓库 `lovstudio/skills` 的镜像） |
| workbuddy | — | 未发布，未选择 |
| skillpay | — | 未发布，未选择 |
