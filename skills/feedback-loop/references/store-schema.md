# 账本字段 v1

账本默认位于 `~/.feedback-loop/`，由 `FEEDBACK_LOOP_HOME` 或 `--store` 覆盖。
事件与结果都是追加式 JSONL；统计时按 `event_id` 合并。

## 目录

```text
~/.feedback-loop/
├── config.json      # 账本 schema、创建时间、版本
├── events.jsonl     # feedback-event/v1
├── outcomes.jsonl   # feedback-outcome/v1
└── reports/         # 生成的报告
```

## 事件 feedback-event/v1

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `schema` | 是 | 固定 `feedback-event/v1` |
| `id` | 是 | `fb-<UTC 紧凑时间>-<4 位十六进制>` |
| `ts` | 是 | UTC ISO8601 秒级时间戳 |
| `local_date` | 是 | 本地日期，用于分组 |
| `host` | 是 | `codex`、`claude`、`cursor`、`openclaw`、`generic` |
| `session_id` | 是 | 宿主会话或线程标识 |
| `cwd` | 否 | 任务工作目录 |
| `channel` | 是 | `explicit` 或 `passive` |
| `polarity` | 是 | `positive`、`negative`、`mixed`、`neutral` |
| `intensity` | 是 | 1–5 整数 |
| `kind` | 是 | 协议中的 kind 枚举 |
| `confidence` | 是 | 0–1，被动信号小于 1 |
| `evidence` | 是 | 去敏后的用户原话片段，最多 240 字符 |
| `scope` | 是 | `task`、`skill`、`reference`、`root-prompt` |
| `scope_target` | 否 | 具体 Skill、reference 或文件 |
| `status` | 是 | 闭环状态 |
| `created_by` | 是 | 记录者，如 `lov-feedback-judge` |
| `note` | 否 | 判定说明 |

示例行：

```json
{"schema":"feedback-event/v1","id":"fb-20260911T020000-ab12","ts":"2026-09-11T02:00:00Z","local_date":"2026-09-11","host":"codex","session_id":"demo-session","cwd":"~/work/demo","channel":"explicit","polarity":"positive","intensity":4,"kind":"praise","confidence":0.95,"evidence":"做得很棒","scope":"task","scope_target":"","status":"captured","created_by":"lov-feedback-judge","note":""}
```

## 结果 feedback-outcome/v1

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `schema` | 是 | 固定 `feedback-outcome/v1` |
| `event_id` | 是 | 指向事件 id |
| `ts` | 是 | 结果记录时间 |
| `status` | 是 | 闭环状态 |
| `action` | 否 | 实际动作 |
| `artifacts` | 否 | 被改动的文件或产物路径列表 |
| `verification` | 否 | 回读与验证方式 |
| `actor` | 是 | `agent` 或 `user` |
| `note` | 否 | 补充说明 |

示例行：

```json
{"schema":"feedback-outcome/v1","event_id":"fb-20260911T020000-ab12","ts":"2026-09-11T02:05:00Z","status":"verified","action":"保留该写法并写入项目规则","artifacts":["~/work/demo/AGENTS.md"],"verification":"重跑任务并回读输出","actor":"agent","note":""}
```

## 状态值

`captured`、`triaged`、`change-proposed`、`change-applied`、`verified`、
`declined`、`deferred`。

## 去重与删除

- 同 `session_id`、同 `evidence`、同 `kind` 且发生在 10 分钟内视为重复，只保留一条。
- 删除以 `status: declined` 加 `note: tombstone` 的结果记录表达，历史事件不修改。
