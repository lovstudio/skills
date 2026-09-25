# Agent Skills 管理最佳实践：当你已经有 100+ Skills 之后

最初安装 Agent Skill 时，体验通常很好：看到一个有用的就装一个，模型也大致知道什么时候调用。等数量超过一百，系统会悄悄进入另一个阶段：相似能力开始互相抢触发，过期 Skill 仍在生效，用户记不住自己装过什么，升级时也不知道会影响谁。

这已经不是“如何写好一个 `SKILL.md`”的问题，而是一个完整的资产治理问题。

本文给出一套面向 100+ Agent Skills 的管理方法，覆盖盘点、作用域、分组、启停、去重、路由、评测、版本化和退役。它既适用于个人长期积累的 Skill 目录，也适用于团队维护的 Skill Marketplace。

截至 2026 年 7 月 13 日，最直接的产品治理依据是 [Anthropic《Skills for enterprise》](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise)；OpenAI 和 Agent Skills 开放标准补充了上下文预算、作用域、渐进披露和用户侧安全边界。工程实现则可以直接对照 Microsoft APM 的包管理实现和 NVIDIA `skills` 的开源治理流水线。

## 先纠正一个概念：安装、可用、候选和激活不是一回事

当 Skill 很少时，这四种状态常被混在一起；超过一百后，必须拆开：

| 状态 | 含义 |
| --- | --- |
| Installed | 已经存在于本地、工作区或 Registry 中 |
| Enabled | 当前用户、项目和权限允许使用 |
| Candidate | 当前请求经过过滤和检索后进入候选集 |
| Activated | Agent 已加载完整 `SKILL.md` 并开始执行 |

正确目标不是把已安装数量压回十几个，而是允许 Registry 持续增长，同时严格控制每次请求进入 Candidate 和 Activated 状态的数量。

一句话概括：

> 大目录，小候选集；先治理资产，再治理路由。

## 权威资料到底给出了什么答案

[Anthropic 企业指南](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise)明确指出，每个 Skill 的名称与描述都会竞争模型注意力；同时加载过多时，Claude 可能选错或漏掉相关 Skill。官方建议：

- 按任务类型或组织角色路由到不同 Skill 集合；
- 新 Skill 同时进行隔离测试和共存测试；
- 发生触发冲突时收窄描述或合并重叠 Skill；
- 维护包含用途、Owner、版本、依赖和评测状态的内部 Registry；
- 使用 Git、固定版本、回滚和完整性校验管理发布；
- 长期低质量或工作流已经失效的 Skill 应当退役。

[OpenAI《Build skills》](https://learn.chatgpt.com/docs/build-skills)公开了 Codex 面对大量 Skills 时的实际处理：初始列表最多占上下文窗口的 2%，无法确定窗口时上限为 8,000 字符；超限后先缩短 description，仍然过多就省略部分 Skill 并给出警告。这说明“都装上，然后把所有描述交给模型”并不是可无限扩展的方案。

[Agent Skills 客户端实现指南](https://agentskills.io/client-implementation/adding-skills-support)定义了发现、作用域、同名冲突、目录过滤、激活和渐进披露；[描述优化指南](https://agentskills.io/skill-creation/optimizing-descriptions)则把触发测试变成了可重复流程。它们共同构成了跨客户端的最低实现基线。

## 开源世界的真实答案：还没有一个“全能管理器”

截至 2026 年 7 月，已经有很多 Agent Skills 目录、安装器和扫描器，但没有一个成熟开源项目同时解决目录、依赖锁定、语义路由、运行时权限、评测、签名和退役。目前最可靠的做法是组合多个专项项目，而不是把其中某一个误当成完整 SkillOps 平台。

| 开源实践 | 已经解决 | 没有解决 | 建议定位 |
| --- | --- | --- | --- |
| [Agent Skills 标准](https://github.com/agentskills/agentskills) | `SKILL.md` 规范、渐进披露、发现、冲突与激活基线 | Registry、安装、治理和评测 | 作为兼容性底座 |
| [Microsoft APM](https://github.com/microsoft/apm) | `apm.yml`、传递依赖、lockfile、内容哈希、SBOM、漂移检测和跨 Agent 安装 | Skill 语义安全、路由准确率和运行时沙箱 | 优先试点的包与锁定层 |
| [Vercel `skills` CLI](https://github.com/vercel-labs/skills) | 70+ 客户端、多种 Git 来源、项目/全局作用域、软链接、查找与更新 | Owner、依赖、权限、评测、冲突和退役 | 优秀安装体验，不是治理后端 |
| [GitHub CLI `gh skill`](https://cli.github.com/manual/gh_skill) | 预览、安装、更新、发布、Git ref/SHA 锁定与来源记录 | Bundle、Owner、语义路由和退役 | GitHub-only 团队可试点，但仍属公开预览 |
| [NVIDIA `skills`](https://github.com/NVIDIA/skills) | 200+ Skills 的上游 Owner、每日镜像、扫描、Skill Card、评测、基准与签名 | 通用管理界面与运行时路由 | 目前最值得照搬的企业治理样板 |
| [skills.sh](https://www.skills.sh/docs) | 大规模公开目录、安装热度、搜索与快照 | 个人本地的启停、Bundle、评测和生命周期 | 发现源，不是 100+ 私有 Skills 的管理器 |
| [OpenAI Plugins](https://learn.chatgpt.com/docs/build-plugins) | 用一个 Plugin 组合多个 Skills/MCP/Hooks、版本与安装策略、插件级启停 | 跨客户端 Registry 和通用路由 | 值得借鉴的角色/领域 Bundle 模式 |

[OpenSkills](https://github.com/numman-ali/openskills) 等项目证明了跨 Agent 加载的可行性，但把所有名称和 description 平铺进 `AGENTS.md` 仍会遇到上下文竞争；它更适合兼容层，不是百级目录的路由答案。`anthropics/skills` 和 OpenAI 的开源仓库则主要是内容或 Plugin 示例；其中旧 [openai/skills](https://github.com/openai/skills) 已明确废弃并迁往 [openai/plugins](https://github.com/openai/plugins)，都不应被误当为独立的 Skills 管理后端。

### 包管理优先看 Microsoft APM，不要自己重写 lockfile

[Microsoft APM](https://github.com/microsoft/apm) 是当前最接近“Agent 包管理器”的开源项目。它把 Skills、prompts、plugins 和 MCP servers 放进同一份 manifest，支持传递依赖，并用 `apm.lock.yaml` 记录精确来源、内容哈希和已解析依赖树。它还提供 SBOM 导出和漂移检测，这些都比只保存一个 Git URL 更接近软件供应链的正常做法。

但 APM 的边界也非常清楚：`apm-policy.yml` 决定“允许安装什么”，Agent harness 决定“安装后允许执行什么”。安装 allowlist 不能代替对文件写入、Shell、网络和对外发布的运行时审批。而且 [APM 治理文档](https://microsoft.github.io/apm/enterprise/governance-guide/) 明确把 lockfile 治理称为稳定能力，同时把组织策略引擎标为 early preview。因此可以先采用 manifest、lock、audit 和 SBOM，生产策略门应固定 APM 版本并保留自己的运行时授权。

### 治理流水线直接借鉴 NVIDIA

[NVIDIA 公开目录](https://github.com/NVIDIA/skills) 不是可直接部署的通用 Registry 产品，但它已经用开源代码展示了 200+ Skills 如何治理。截至 2026 年 7 月 13 日，`main` 中可数到 229 个顶层 `SKILL.md` 与 33 个产品组件注册文件；产品团队保持上游所有权，中央 Catalog 每日镜像，并有孤儿目录清理和大量删除人工闸门。数量会继续变化，这里的重点是治理方式，不是静态排名。

它的 [Trust Pipeline](https://docs.nvidia.com/skills/agent-skill-trust-pipeline) 更值得照搬。一个可发布 Skill 不只有 `SKILL.md`，还应带有：

```text
SKILL.md
skill-card.md        # Owner、许可证、用途、地域、输出和风险
evals/*.json         # 可重复评测集
BENCHMARK.md         # 评测结果
skill.oms.sig        # 对整个目录的分离式签名
```

发布顺序是：收窄用途和权限 → 扫描 → 修复或记录接受的风险 → 完成 Skill Card → 评测 → 对确切目录签名 → 消费端验签。[NVIDIA 签名指南](https://docs.nvidia.com/skills/signing-agent-skills)特别强调，签名只证明“收到的是已审查制品”，不证明它本身安全；所以扫描、人工评审、评测与签名必须同时存在。

## 经过开源选型后的推荐组合

下表不是项目的绝对排名，而是面向“100～1000 个 Skills、本地优先、同时服务个人与小团队”的适配度。加权为：需求适配 25%、开发体验 15%、维护活性 15%、交付质量 15%、可控性与许可 10%、安全 10%、运维 10%。

| 模块 | 候选 | 加权分 | 结论 |
| --- | --- | ---: | --- |
| 包、依赖与锁定 | Microsoft APM | 90 | 首选试点；策略引擎仍固定版本 |
| 包、依赖与锁定 | Vercel `skills` CLI | 82 | 安装 UX 很强，但治理字段与依赖模型不足；若要 fork，先核验仓库授权文本 |
| 资产目录与搜索 | Git/YAML + SQLite FTS5 | 93 | 100～1000 规模的默认选择，索引可随时重建 |
| 资产目录与搜索 | Backstage | 74 | 只在组织已有内部开发者门户时接入 |
| 准入扫描 | [Cisco AI Defense Skill Scanner](https://github.com/cisco-ai-defense/skill-scanner) | 90 | 首选；已有递归扫描、跨 Skill 重叠和触发词检查 |
| 准入扫描 | [NVIDIA SkillSpector](https://github.com/NVIDIA/SkillSpector) | 85 | 68 种漏洞模式、SARIF 和本地/外部 LLM；适合第二意见 |
| 准入扫描 | [Snyk Agent Scan](https://github.com/snyk/agent-scan) | 78 | 适合盘点 Skills + MCP；数据外发与大规模 API 限制使其不适合做开放 Registry 核心 |
| 路由与输出评测 | [Promptfoo](https://www.promptfoo.dev/docs/guides/test-agent-skills/) | 91 | 首选；已支持 `skill-used` / `not-skill-used` 和近邻 Skill 边界测试 |
| 高风险动态评测 | [Inspect AI](https://inspect.aisi.org.uk/) | 85 | 用于沙箱、工具审批和长轨迹任务，不必覆盖每个 Skill |
| 运行时观测 | OpenTelemetry + [Langfuse](https://langfuse.com/docs) | 92 | 产品化首选；核心开源，但要核对企业功能边界 |
| 运行时观测 | OpenTelemetry + [Phoenix](https://arize.com/docs/phoenix) | 91（内部） | 适合隔离部署；Elastic License 2.0 限制对外托管同类服务 |

任何扫描器都只能作为线索生成器，不是安全证明。Cisco 和 NVIDIA 都明确承认可能存在误报与漏报；“没有发现”不等于“可以无审批启用”。高风险 Skill 仍需要人工检查实际脚本、权限、网络边界和预期输出。

对只有几百个 Skills 的目录，[SQLite FTS5](https://www.sqlite.org/fts5.html) 已经提供 BM25、字段权重、短语和 trigram 子串检索。它应先索引 ID、`when`、正向示例、description 和 tags；`not_when`、权限不匹配和依赖缺失应当做硬过滤，而不是交给向量相似度降权。只有真实评测证明词法召回不足时，才增加 sqlite-vec 或 LanceDB；只有进入多租户、高 QPS 和大量运行轨迹时，才值得运维 Qdrant。

权限策略也应递进引入。个人或小团队先用可审查的 YAML/JSON 规则做确定性过滤；只有当身份、仓库、数据级别和环境组成动态 ABAC，并且需要集中下发、单元测试和 decision log 时，再引入 [Open Policy Agent](https://www.openpolicyagent.org/docs/)。OPA 返回授权决定，但仍然需要 Runtime 真正拦截执行。

## 100+ Skills 的目标架构

结合上述开源实践，一个可持续的 Skill 系统不是四个孤立页面，而是一条可审计的供应链和运行时链：

```text
上游 Git / 内部仓库 / 公开目录
  ↓
APM：manifest、依赖解析、lockfile、哈希、SBOM
  ↓
隔离区：Cisco Scanner → 人工评审 / Skill Card → Promptfoo 评测 → OMS 签名
  ↓
Registry：保存全部 Skill、Owner、版本、关系、风险和评测状态
  ↓
Scope / Bundle：按用户、项目、角色、权限和风险硬过滤
  ↓
Router：FTS5 召回少量候选、可选向量补充、重排和置信度闸门
  ↓
Runtime：只加载命中的 Skill，并对写入、Shell、网络和发布执行审批
  ↓
OpenTelemetry：记录候选、命中、用户改选、成功、成本和延迟，回流到评测集
```

实际请求可以走下面这条链路：

```text
用户目标
  ↓
确定性过滤：项目 / 平台 / 权限 / 价格权益 / 文件类型 / 风险
  ↓
FTS5 词法召回，评测证明必要时再加向量补充
  ↓
相邻能力重排，并保留“都不适用”
  ↓
高置信度：自动选
候选接近：展示差异或只追问一个问题
  ↓
加载完整 Skill 与依赖
  ↓
执行 → 记录 → 评测 → 修订或退役
```

确定性过滤必须放在语义检索之前。例如用户没有专业版权益，就不应把专业版 Skill 交给模型竞争；当前项目不是 Tauri，就不应暴露只服务 Tauri 的 Skill；具有外发或写入副作用的能力，也应先经过权限和风险策略。

## 第一步：建立唯一的 Skill Registry

文件夹不是管理系统。超过一百个 Skill 后，至少要维护一份机器可读的 Registry。它可以来自数据库、JSON、YAML 或生成式索引，但必须有唯一事实来源。

建议字段如下：

```yaml
id: legal.contract-review
display_name: 合同审查
workflow: legal-review
variant: professional
owner: legal-automation
scope: [workspace, legal-team]
status: approved
version: 2.3.1
when: 用户需要识别合同风险并形成修改建议
not_when: 用户只需要格式转换或逐字翻译
risk: write-with-approval
depends_on: [pdf, documents]
alternative_to: [legal.contract-review-basic]
last_eval: 2026-07-01
```

其中只有一部分属于标准 `SKILL.md` frontmatter；Owner、状态、关系和评测结果更适合放在外部 Registry。不要为了统一而把所有治理字段都塞进 description。

Registry 至少要回答七个问题：

1. 这个 Skill 解决什么用户结果？
2. 谁负责维护？
3. 哪些用户、项目和平台可以使用？
4. 它依赖哪些工具、MCP Server 或其他 Skills？
5. 它与哪些 Skill 重叠、互斥、替代或存在版本关系？
6. 最近一次触发与输出评测是什么时候？
7. 出问题时应该回滚到哪个版本？

## 第二步：用作用域和 Bundle 缩小默认集合

100+ Skills 不应组成一个默认全开列表。建议至少建立这些作用域：

- **系统级**：所有场景都适用、经过严格审核的基础能力；
- **用户级**：个人长期使用的写作、研究、办公偏好；
- **项目级**：只在特定仓库、客户或业务环境中启用；
- **角色级**：开发、设计、法务、财务、运营等工作包；
- **会话级**：只为当前任务临时启用，结束后自动释放；
- **仅显式调用**：部署、发布、发消息等高副作用 Skill，不允许模型自行触发。

Bundle 不是把目录重新分个类，而是一个可执行的启用策略。例如“前端开发”Bundle 可以包含代码审查、组件设计、浏览器验证和部署检查，但不应该带上合同审查、财务报表和社交媒体发布。

Claude API 当前每次请求最多挂载 8 个 Skills，这是具体平台限制，不是行业统一标准。真正的原则是：随着候选增加持续测量 Recall 和误触发，性能开始下降就停止扩张当前 Bundle，并转为上层路由。

## 第三步：把重复、变体和依赖关系分开

很多 Skill 混乱并不是重复，而是没有标明关系。

建议至少维护五类关系：

| 关系 | 处理方式 |
| --- | --- |
| Equivalent | 能力、输入、输出和副作用一致，合并并保留旧 ID 别名 |
| Variant | 同一工作流的免费版、专业版或不同执行模式，归到一个 Workflow 下 |
| Alternative | 目标相同但提供商、成本或质量不同，由策略选择 |
| Depends on | 当前 Skill 需要先激活另一个 Skill 或工具 |
| Supersedes | 新版本替代旧能力，旧项进入弃用期 |

是否合并不能只看名称或向量相似度。只有在输入前提、交付结果、权限、副作用和评测表现都等价时，才应真正合并。

例如 `Contract Review` 与 `Contract Review Pro` 更适合表达为同一个“合同审查”Workflow 下的两个 Variant。系统先根据用户权益和风险要求选择 Variant，而不是让两个近义 description 去争抢同一个请求。

## 第四步：让 description 承担路由，而不是宣传

Agent 在启动时通常只看到 Skill 的 `name` 和 `description`。因此 description 应回答：

```text
做什么结果
何时必须使用
何时不要使用
用户可能怎样表达这个意图
与最相近 Skill 的区别
```

一个实用模板是：

```text
当用户需要完成【目标结果】，并且满足【前提】时使用。
包括【典型自然语言请求】。
不要用于【近邻但不同的场景】；这类请求应交给【相邻能力】。
```

[Agent Skills 描述优化指南](https://agentskills.io/skill-creation/optimizing-descriptions)建议围绕一个 Skill 准备约 20 条触发测试，其中正向和负向各 8～10 条，并重点使用容易混淆的近邻负样本。因为模型行为存在随机性，同一请求还应重复运行，而不是只测试一次。

## 第五步：建立“单 Skill + 共存 + 端到端”三层评测

一百个 Skill 最大的风险不是某一个 Skill 完全不能用，而是新增一个后，旧 Skill 的触发被悄悄抢走。

每个 Skill 至少需要五组请求：

- 应该触发；
- 不应该触发；
- 与相邻 Skill 容易混淆；
- 不需要任何 Skill；
- 需要多个 Skills，且存在顺序或依赖。

评测也应分三层：

### 1. 检索层

- 正确 Skill 是否进入候选集；
- Recall@K；
- 权限或平台不匹配的 Skill 是否被提前过滤；
- 语义重复项是否占满候选位置。

### 2. 路由层

- Top-1 选择准确率；
- 不该调用时的拒绝准确率；
- 相邻 Skill 混淆矩阵；
- 用户改选率和澄清率。

### 3. 执行层

- 端到端任务成功率；
- 是否遵循 Skill 的强制步骤；
- 副作用是否经过审批；
- Token、延迟和失败后的回退表现。

Anthropic 建议每个 Skill 至少提交 3～5 个代表性查询，并同时进行隔离与共存测试。实际管理 100+ Skills 时，3～5 条适合作为最低上线门槛；高频或容易冲突的 Skill 应扩展到约 20 条正负与近邻样本。

不要给所有产品套一个固定合格分数。先记录现有系统的基线，再把“新增 Skill 不得显著降低相邻能力表现”设成发布门槛。

[Promptfoo 的 Agent Skills 评测指南](https://www.promptfoo.dev/docs/guides/test-agent-skills/) 已经把这个门槛做成可执行断言：正向请求断言 `skill-used`，近邻请求同时断言目标 Skill 被用且兄弟 Skill `not-skill-used`，最后再检查输出是否真正变好。对 Codex，它通过成功读取对应 `SKILL.md` 推断使用轨迹；因此这个信号很实用，但不应被误当成所有客户端都有的一等调用事件。

## 第六步：给 Skill 建立完整生命周期

每个 Skill 都应该经历同一条状态机：

```text
draft → reviewed → evaluated → approved → active
                          ↓
                needs-fix / quarantined
                          ↓
                 deprecated → retired
```

对应的管理动作是：

1. **创建**：先解决一个窄而明确的工作流；
2. **审查**：检查脚本、网络访问、文件范围、凭据和提示注入风险；
3. **评测**：跑单独触发、近邻冲突和输出质量测试；
4. **发布**：固定版本并记录 Owner、依赖和回滚版本；
5. **监控**：记录激活、成功、误选、用户切换和审批情况；
6. **修订**：修改 description、instructions 或路由关系后重新回归；
7. **退役**：保留迁移提示、旧 ID 映射和可回滚版本，再从默认候选集中移除。

生产环境不要无条件引用 `latest`。Skill 的脚本和指令都可能改变执行轨迹，升级应当和软件发布一样经过审查、评测与灰度。

## 用户有 100+ Skills 时，管理界面应该长什么样

用户不应该面对一张 100 张卡片的墙，也不应该先理解 Skill、Tool、MCP 和 Plugin 的技术差异。

一个真正有帮助的管理界面至少包含：

- **当前任务推荐**：只展示一项首选和少量备选，并说明推荐理由；
- **当前已激活**：明确本次会话到底加载了哪些 Skills；
- **Bundle 管理**：按工作、角色和项目一键启停；
- **最近使用与收藏**：让高频能力不依赖重复搜索；
- **待处理状态**：更新可用、权限缺失、评测失败、已弃用；
- **重复与冲突建议**：提示可能的 Variant、Equivalent 或 Supersedes 关系；
- **影响说明**：展示是否读文件、写入、联网、发布或需要审批；
- **显式调用入口**：自动路由失败时，用户可以直接指定 Skill。

[OpenAI Skills API](https://developers.openai.com/api/docs/guides/tools-skills)还给出了消费级产品的重要边界：不要让终端用户任意挂载未经审核的开放 Skills 仓库，而应由开发者审核后映射成边界清楚的产品工作流，高影响动作继续保留明确审批。

换句话说，用户侧的核心对象应该是“我要完成什么”，而不是“我应该装哪个技术组件”。

## 已经堆到 100+，现在具体怎么收拾

如果目录已经失控，可以按以下顺序迁移，不需要一次重写全部 Skills。

### 阶段一：冻结和盘点

1. 暂停新增默认启用项；
2. 将当前目录、版本与启用状态提交到 Git；
3. 导出所有 Skill 的名称、描述、路径、来源和最近使用情况；
4. 将来源不明、解析失败或存在高风险脚本的 Skill 暂时隔离；
5. 标记没有 Owner、没有版本或长期无人维护的条目。

### 阶段二：先处理最危险的混乱

1. 按用户结果而不是技术名聚类；
2. 找出名称相似、description 重叠和触发互抢最严重的前十组；
3. 将套餐、提供商和执行模式改成 Variant 或 Alternative；
4. 为被替代 Skill 建立 `supersedes` 和旧 ID 映射；
5. 重写高频 Skill 的 `when / not_when`。

向量聚类可以帮助发现疑似重复，但只能生成待审列表，不能自动删除。ACL 2026 的 [ToolScope](https://aclanthology.org/2026.acl-long.1573/)证明重叠名称和描述确实会损害工具选择，但这项研究的对象是 Tools；把它迁移到完整 Agent Skills 属于有依据的架构推断，不是自动合并许可证。

### 阶段三：建立小激活集

1. 先创建 3～8 个最常用的角色或项目 Bundle；
2. 把低频、高风险和强副作用 Skill 改成仅显式调用；
3. 在语义检索前加入权限、平台、项目和依赖过滤；
4. 默认只向重排器提供少量候选，并允许返回“都不适用”；
5. 低置信度时追问一个能真正区分候选的问题。

3～8 是迁移起点，不是行业标准。实际数量必须由自己的召回、误选、成本和任务成功率决定。

### 阶段四：把治理变成持续流程

1. 新 Skill 没有 Owner、风险审查和共存评测就不能进入默认 Bundle；
2. description、版本、依赖或权限变化后自动跑回归；
3. 定期查看零使用、低成功率和高改选率 Skill；
4. 给每次退役保留迁移说明和回滚窗口；
5. 将生产误选样本持续加入近邻负样本集。

## 真正落地时的分阶段路线

以“已经有 100～1000 个 Skills，但还没有统一控制面”为前提，一名熟悉现有目录的工程师可以这样分期：

| 阶段 | 交付物 | 粗略投入 |
| --- | --- | ---: |
| 0. 冻结与基线 | 导出现有目录、Git 固定、来源/权限/最近使用盘点 | 2～3 天 |
| 1. 可管理 MVP | APM 试点、Registry Schema、SQLite FTS5、Bundle、Cisco 准入门与基础 Promptfoo 回归 | 1 人 2～4 周 |
| 2. 团队生产化 | Owner 审批、Skill Card、锁版与回滚、OpenTelemetry + Langfuse、使用反馈回流 | 再增 2～4 周 |
| 3. 高合规供应链 | Inspect AI 沙箱、OMS/Sigstore 签名、OPA 动态策略、OCI/ORAS 制品 | 再增 2～5 周 |

这些是工程估算，不是开源项目的官方承诺。对小于 1000 个 Skills 的本地系统，Git、SQLite、CI 和现有 Agent 可以让基础设施增量成本接近零；真正的持续成本来自评测的模型调用、扫描/签名流水线、观测数据保留和 Owner 的复审时间。

## 最常见的七个反模式

1. **全量默认开启**：安装数量直接等于候选数量；
2. **只做分类页**：分类帮助浏览，却不参与运行时过滤；
3. **只接向量搜索**：通用检索器未必理解能力边界；
4. **用价格档位复制 Skill**：免费版和专业版争抢同一个意图；
5. **创建万能 Mega Skill**：内部路径过多，同样会产生选择歧义；
6. **永远使用 latest**：更新后无法复现，也没有快速回滚；
7. **没有 Owner 和退役机制**：目录只能增长，不能修剪。

[ToolRet](https://aclanthology.org/2025.findings-acl.1258/)在四万多个工具上的研究说明，普通信息检索模型在工具召回上仍可能表现很差。它提醒我们：搜索只是路由的一层，不能代替结构化元数据、权限过滤、共存评测和失败回退。

## 一份可以直接采用的验收清单

当系统拥有 100+ Skills 时，至少应能回答：

- [ ] 所有 Skill 是否都有稳定 ID、Owner、版本和状态？
- [ ] 是否区分 Installed、Enabled、Candidate 和 Activated？
- [ ] 是否存在项目、用户、角色和仅显式调用作用域？
- [ ] 是否记录 Equivalent、Variant、Alternative、Depends on、Supersedes？
- [ ] 每个高频 Skill 是否有正向、负向和近邻触发样本？
- [ ] 新 Skill 是否跑过与现有 Skills 的共存回归？
- [ ] 路由前是否先按权限、平台、项目和风险过滤？
- [ ] 系统是否允许判断“无需任何 Skill”？
- [ ] 用户是否能看到为什么选择、当前激活和如何切换？
- [ ] 高副作用 Skill 是否默认显式调用或需要审批？
- [ ] 生产版本是否可固定、审计和回滚？
- [ ] 低质量、过期和无人维护的 Skill 是否能真正退役？

## 最后的判断

管理 100+ Agent Skills，重点已经不再是继续写更多 `SKILL.md`，而是建立一条软件供应链和一个小型操作系统：APM 负责包、依赖与锁定，Registry 负责资产，Scope 与 Bundle 负责边界，Router 负责选择，Runtime 负责按需加载和授权，Eval、Observability 与 Lifecycle 负责让系统可以持续演进。

后台目录可以很大，但每次请求进入竞争的候选必须足够小；用户可以拥有上百个 Skills，但不应该被迫记住上百个名字。

真正成熟的 Skill 系统，不是“什么都有”，而是始终知道：**现在该启用什么、为什么启用、出了问题如何回滚、不再需要时怎样退出。**
