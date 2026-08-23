---
name: lov-china-website-filing
description: >
  面向中国大陆网站的一站式备案与上线 Skill Kit：当用户说“办 ICP 备案”“做公安联网备案”“备案后绑定域名”或 "handle China website filing" 时，按权威页面完成材料、审核、域名切换、合规展示与巡检留痕。
license: MIT
metadata:
  author: LovStudio
  version: "0.2.0"
  card_standard: lovstudio/skill-card/v1
  tags:
    - china-website-filing
    - icp
    - public-security-filing
    - domain-cutover
    - compliance-monitoring
  compatibility: "Portable Agent Skills format. Python 3.8+; browser control and authenticated authority/provider sessions are optional but required for live filing operations."
  dependencies: []
---

# lov-china-website-filing — 中国大陆网站备案与上线

把备案准备、ICP、备案后上线、公安联网备案和持续巡检收敛为一条有证据、可暂停、可恢复的流程。每一步以政府或接入商权威页面为准；验证码、承诺、最终提交和额外安全评估始终保留人工授权。

## Product contract

- **输入**：主办者类型与证件信息、网站服务名称、域名、接入商/云资源、上线目标、已有订单或备案号。
- **输出**：准备清单、状态快照、材料缺口、需用户执行的动作、备案/上线验收结果，以及追加式巡检记录。
- **不承诺**：不保证监管审核通过或时限；不把搜索结果、缓存记录、短信或接入商中间状态冒充最终权威结果。

## Triggers

### Activate when

- 用户说“给公司网站做 ICP 备案”“继续公安联网备案”“备案通过后部署并绑定域名”“每天检查备案状态”或“网站底部加备案号”。
- User asks to "handle China website filing", "prepare an ICP filing", "submit a public security filing", or "monitor a mainland website filing".
- 用户给出备案订单、域名、云服务商控制台或全国互联网安全管理服务平台页面，希望代理完成一段或整段流程。

### Do not activate when

- 只生成隐私政策或服务条款页面；交给 `lov-legal-pages`。
- 只做普通网页表单预填，且不需要备案状态机、权威证据或提交门控；可交给 `lov-fill-web-form`。
- 只做通用生产构建、应用商店发布、ICP备案查询以外的法律意见，分别交给生产、发布或法律专业能力。
- 域名或服务器完全位于中国大陆境外，且用户没有中国大陆 ICP、接入或公安联网备案目标。

## User Profile (cross-session)

每次运行读取 `skill.yaml` 声明的 `user-profile/v1` 上下文，包括用户、品牌、工作区和 `skills.lov-china-website-filing`。解析顺序为：当前请求、当前项目、Skill 记录、共享偏好、品牌/用户 Profile、安全默认值。

只有用户直接说明并希望以后复用的品牌或备案偏好，才通过 `scripts/profile_store.py record --confirm` 持久化。证件号码、手机号、验证码、Cookie、密钥和扫描件内容不得写入 Profile 或 Skill 源码。完整约定见 [User Profile contract](references/user-profile.md)。

## Skill Kit Modules

运行前读取 `kit.yaml`，并按目标加载以下模块：

- `$SKILL_DIR/skills/filing-readiness/SKILL.md` — 主体、域名、接入资源、材料和业务类型准备。
- `$SKILL_DIR/skills/icp-filing/SKILL.md` — ICP 申请、接入商审核、短信核验与管局结果。
- `$SKILL_DIR/skills/domain-cutover/SKILL.md` — 备案通过后的部署、DNS、TLS 与 ICP 展示验收。
- `$SKILL_DIR/skills/public-security-filing/SKILL.md` — 公安联网备案及安全评估分支。
- `$SKILL_DIR/skills/filing-monitor/SKILL.md` — 权威状态巡检、差异比较、通知与完成门槛。

主流水线 `mainland-website-launch` 的顺序固定为：

```text
filing-readiness → icp-filing → domain-cutover
                 → public-security-filing → filing-monitor
```

模块可单独运行，但跨阶段交接必须携带域名、主体/服务名称、权威入口、当前状态、证据时间和下一动作。

## Skill Group Composition

先读 [组合记录](references/skill-composition.md)。相邻 Skill 只能作为显式、可选的制品级交接；本 Kit 不把任何 sibling Skill 当作隐藏依赖。

## Workflow (MANDATORY)

**必须按以下顺序执行。**

### Step 0: Resolve root, context, and authoritative sources

1. 使用 `SKILL_DIR`，否则从当前 Skill 上下文推断根目录；验证五个模块、`references/`、`scripts/filing_record.py` 和 `assets/filing-record-template.md`。
2. 读取 Profile，但不要把私人路径或证件信息复制进输出或源码。
3. 阅读 [权威规则](references/official-rules.md)、[状态词表](references/status-taxonomy.md) 和 [提交门控](references/authority-gates.md)。
4. 对会变化的规则、页面字段、时限或地方要求，运行时重新打开官方/接入商权威页面核验；不要仅凭本 Skill 的快照。

### Step 1: Classify the filing scenario

确定以下事实，缺少且会改变路线时最多问一个聚焦问题：

- 主办者是单位还是个人；服务是网站、APP、小程序还是仅 API。
- 首次备案、新增服务、接入备案、变更、注销，或仅办理公安联网备案。
- 域名注册人实名是否与主办者匹配；接入资源和服务器是否在中国大陆。
- 网站是否已公网开放、是否有用户发布/评论/群组/直播/信息分享、算法或生成式 AI 等能力。

把结论写为 `verified`、`user-stated`、`inferred` 或 `unknown`，不要把推断写成已核验事实。

### Step 2: Create or resume the evidence ledger

首次运行可执行：

```bash
python3 "$SKILL_DIR/scripts/filing_record.py" init \
  --path ./website-filing-record.md \
  --subject "示例主办者" --service "示例服务" \
  --domain example.cn --provider "示例接入商"
```

已有记录时先运行 `check` 和 `compare`，读取最后一条权威状态。台账只保存必要的公开标识和脱敏证据摘要；不保存 Cookie、验证码、完整证件号或扫描件。

### Step 3: Run the selected module or pipeline

- 完整上线走 `mainland-website-launch`。
- 仅 ICP 走 `icp-only`。
- 已取得 ICP 后上线并办公安备案走 `post-icp-launch`。
- 单点任务可直接进入对应模块，但先验证上游门槛，例如没有 ICP 通过证据就不得执行大陆网站域名切换。

浏览器操作优先复用用户当前已登录会话。登录、验证码、短信核验、扫码、人脸、电子签名、责任书、安全评估结论和最终提交都按 [提交门控](references/authority-gates.md) 处理。

### Step 4: Record authoritative evidence

每次状态观察后追加一行：

```bash
python3 "$SKILL_DIR/scripts/filing_record.py" append \
  --path ./website-filing-record.md \
  --time 2026-08-14T10:00:00+08:00 \
  --authority "接入商备案订单详情" \
  --stage icp --status authority-review \
  --domain-status held-off \
  --action "等待管局审核" \
  --evidence "订单详情显示已提交管局"
```

先比较上一条记录。状态无变化且无需动作时保持静默，只追加记录；状态变化、人工阻塞或新动作出现时才通知用户。通知渠道由当前宿主和用户明确要求决定，不在 Skill 内硬编码。

### Step 5: Apply completion gates

- **ICP 完成**：工信部查询或管局/接入商权威结果明确显示审核通过，并能读取对应服务备案号。
- **上线完成**：预期域名真实解析、HTTPS 可用、页面内容与备案服务一致、ICP 号在首页底部展示并链接工信部系统；旧域名只在用户授权后解绑或替换。
- **公安备案完成**：全国互联网安全管理服务平台或属地公安权威结果明确显示审核通过，并取得公安备案号。
- **全流程完成**：上述门槛均满足，公安号与图标已按平台代码在网站展示并完成线上回读；额外安全评估若适用，也必须有单独的真实状态。

未达到门槛时使用 `pending`、`blocked-user-action`、`rejected` 或 `partially-verified`，不得称“已完成”。

### Step 6: Close browser work and report

按照所用浏览器控制能力的标签页规则收尾：保留需要用户登录/验证码/确认的 handoff 页面，关闭本次新开的无关页面，避免关闭用户原有标签页。

最终只报告：最新权威状态、与上次相比的变化、证据入口与时间、下一动作、已更新记录。对于无变化且无需动作的定时巡检，遵守用户的静默策略。

### Step 7: Validate the Skill source

维护本 Skill 时运行：

```bash
python3 scripts/validate_skill.py .
python3 -m unittest discover -s tests -v
```

同时验证一个中文触发、一个英文触发、一个非触发，并运行至少一次 `mainland-website-launch` 的离线台账演练。

## Dependencies

- Python 3.8+ 标准库，用于确定性的台账脚本。
- 实时办理时需要网络、浏览器控制能力，以及用户已登录的政府/接入商会话。
- PyYAML 仅用于运行 Skill Creator 自带的源校验器。
- 无外部 sibling Skill 硬依赖；无凭据时仍可生成准备清单和离线台账。

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
