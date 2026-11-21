---
name: lov-gjkj-cli
description: >
  共绩算力 CLI：用随附的 lov-suanli-cli 查询与操作共绩算力 Open API 与大模型云服务（83 个接口），默认只读，写操作和计费调用先确认。
  Use for 查共绩算力任务/存储/账单、suanli API.
license: MIT
compatibility: >
  Portable Agent Skills format. Node.js 20+ (the bundled CLI, SDK and Swagger proxy use only Node built-ins); Python 3.8+ for
  scripts/gjkj_cli.py; network access to openapi.suanli.cn and api.suanli.cn. Credentials come from the user's environment
  variables or the macOS Keychain (services suanli-token, suanli-llm-key) and are never stored in this Skill.
metadata:
  author: lovstudio
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  tags:
    - cli
    - api
    - suanli
    - gpu-cloud
---

# 共绩算力 CLI · Suanli CLI

用随附的 `lov-suanli-cli` 查询和操作共绩算力（suanli.cn）的 Open API 与大模型云服务：资源、弹性部署与 Job 任务、
节点、费用、对象存储与集群存储、裸金属，共 83 个接口。CLI 与 SDK 由 `lov-cli2anything` 的 suanli.cn 适配器从官方公开文档生成，
14 个只读接口已用真实密钥实测。本 Skill 在它外面加上 Agent 用的安全规则：默认只读，写操作与计费调用逐次征得用户同意，密钥只从环境变量或钥匙串读。

## Triggers

### Activate when

- 「查一下共绩算力上我有哪些任务 / 存储卷 / 账单」「看看共绩有哪些可用区域和卡型」。
- 「用共绩 API 创建（或停止、扩缩）一个弹性部署任务」「给这个任务改节点数」（写操作，需逐次确认）。
- 「打开共绩算力的 Swagger」「共绩 API 怎么调」「列出共绩算力的接口」。
- Query or operate the suanli.cn (共绩算力) Open API: tasks, storage, billing, bare-metal, LLM models.

### Do not activate when

- 重新生成或扩展 CLI 本身（新接口、新版本文档）→ `lov-cli2anything`（suanli.cn 适配器），生成后按 [references/regenerate.md](references/regenerate.md) 更新本 Skill。
- 别的云平台、或者只是在聊算力行业 → 不适用。
- 用户没有共绩算力账号或密钥，又要求绕过鉴权、借用他人凭据 → 拒绝。

## User Profile (cross-session)

每次运行读取 `skill.yaml` 声明的 `user-profile/v1`。本 Skill 只持久化工作偏好（`skills.lov-gjkj-cli.records`：Swagger 端口、
默认输出是否带完整 envelope、常用区域），从不保存密钥、账号或查询结果。用户直接说出的长期偏好用
`scripts/profile_store.py record --confirm` 写回并报告路径。详见 [references/user-profile.md](references/user-profile.md)。

## Skill Group Composition

见 [references/skill-composition.md](references/skill-composition.md)：`lov-cli2anything` 是上游生成器；本 Skill 独占「在对话里安全地调用共绩算力 API」这一结果。

## Hard gates

1. **只读优先。** 未经用户就这一次调用明确同意，不执行写操作（`W`）与计费调用（`$`，如 `llm-chat-completions`）。
   先 `--dry-run` 把方法、地址、请求体给用户看，得到原话同意后用 `gjkj_cli.py run --approved "<用户原话>" -- …`。
   同意只对这一次调用有效；创建任务、购买裸金属、开存储等会产生费用的操作，复述金额或规格后再确认。
2. **密钥不入文件、不入对话。** 只从环境变量（`SUANLI_TOKEN`、`SUANLI_LLM_API_KEY`、`SUANLI_PRIVATE_KEY_FILE`、
   `SUANLI_PLATFORM_PUBLIC_KEY_FILE`）或钥匙串（`suanli-token`、`suanli-llm-key`）读；`doctor` 只报长度。用户把密钥贴进对话时，
   提醒他在控制台作废重建，并改用钥匙串命令自己输入。
3. **结果如实。** 返回 `code` 不是 `0000` 时原样给出 code 与 message 并按 [references/errors.md](references/errors.md) 解释，
   不把失败说成成功；接口只有文档证据（未实测）时说明这一点。
4. **不越权。** 团队账号下开发者角色不能建或删密钥；需要控制台操作（建密钥、充值、开通）时请用户本人去做。

## Workflow (MANDATORY)

### Step 0: 解析环境

```bash
export SKILL_DIR="/path/to/lov-gjkj-cli"
python3 "$SKILL_DIR/scripts/gjkj_cli.py" doctor
```

- `node` 缺失或 `operations ≠ manifest_operations` 时停下报告。
- 某个凭据 `keychain_length` 为 0 且环境变量未设：按 [references/auth.md](references/auth.md) 让用户自己建密钥并存进钥匙串；
  长度明显偏短（如个位数）说明存错了，让用户用 `-U` 覆盖重存。

### Step 1: 找到命令

```bash
python3 "$SKILL_DIR/scripts/gjkj_cli.py" ops --group 存储            # W 写 · $ 计费 · E 加密请求体 · V 已实测
python3 "$SKILL_DIR/scripts/gjkj_cli.py" run -- <command> --help     # 该命令的参数
```

常用查询与参数见 [references/commands.md](references/commands.md)；调用顺序（先查资源再建任务等）见 `assets/cli/api-graph.json`。

### Step 2: 调用

- 只读：`python3 "$SKILL_DIR/scripts/gjkj_cli.py" run -- storage-get-regions`（默认只输出 `data`；`--envelope` 输出完整响应）。
- 写操作与计费：先 `--dry-run` → 给用户看 → 用户原话同意 → `run --approved "<原话>" -- <command> --data '<json>'`。
- 加密接口（`E`）需要 `SUANLI_PLATFORM_PUBLIC_KEY_FILE`；RSA 签名模式需要 `SUANLI_PRIVATE_KEY_FILE`，见 [references/auth.md](references/auth.md)。

### Step 3: 汇报

- 结论先行：查到了什么、做了什么；列表类结果给数量与关键字段，不倾倒整段 JSON。
- 写操作汇报变更前后状态，并回查一次（详情或列表接口）确认已生效。

### Swagger（可选）

```bash
python3 "$SKILL_DIR/scripts/gjkj_cli.py" swagger --port 4790   # 后台运行，只监听 127.0.0.1；用 ego-browser 打开 http://127.0.0.1:4790
```

浏览器里不填 token，代理从环境变量或钥匙串取密钥并现场签名；代理默认拒绝写操作。调用关系图在 `/drilldown.html`。

## Dependencies

- Node.js 20+；Python 3.8+；网络可达 openapi.suanli.cn、api.suanli.cn。
- 用户本人的共绩算力 Open API 密钥；大模型接口另需大模型 API Key 且账户有余额。

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、Skill 专属记录、个人 Preferences、品牌/用户 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存用户与品牌的共享资料，`skills.<skill_id>.records` 保存本 Skill 的持久化记录。
- 用户直接说出的长期偏好或品牌事实，通过 `scripts/profile_store.py` 原子写回 Profile，并在结果中报告保存路径。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
