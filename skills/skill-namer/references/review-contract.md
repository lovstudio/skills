# 命名结果清单

UTF-8 JSON，拒绝重复键、未知字段与不完整覆盖。
顶层字段为 `schema`、`scope_ids`、`rows`，可选 `author_prefixes`。
`schema` 固定为 `skill-naming-review/v1`。`scope_ids` 是完整范围的唯一标识列表；
使用原 catalog slug 或 runtime ID，整份清单采用同一种来源，不自动改写标识。

| 每行字段 | 内容 |
| --- | --- |
| id | 与范围清单一致的稳定标识 |
| before | name_zh、display_name 两个原始名称；新建或原字段缺失时为空字符串 |
| after | 同样两个字段，均为非空的推荐名称 |
| decision | rename / retain / review；待核实或待决冲突用 review |
| approval | 两个显示字段分别为 user / editorial / unresolved |
| approved | 仅保存用户已认可字段的精确原文；未认可的语言不写 |
| evidence | 非空字符串列表，定位实际能力与认可来源 |
| reason | 为何修改或保留的一句说明 |

`user` 必须有对应 `approved` 值并与 `after` 一致。认可值冲突报错；仅当前用户
明确改变偏好时才更新认可基准。未解决状态必须使用 `review`，审计返回非零。

工具针对双语配对清单；单语轻量请求可以文本交付，不编造英文认可。
脚本不核验 evidence 的语义与真实性，也无法知道 scope_ids 是否遗漏真实库存；
运行前必须与原始范围核对。

参考 [自身命名清单](../cases/evidence/self-naming-review.json) 和
[历史目录清单](../cases/evidence/catalog-review.json)。它们是真实案例，不是空模板。

运行 `python3 scripts/audit_names.py 输入路径`，stdout 输出 JSON 报告，包含
`ok`、`counts`、`errors`、`warnings`。退出码 0 表示结构通过，1 表示清单未通过，
2 表示输入或读取失败。警告需人工判断；优雅程度、近义冲突、真实性与线上状态
仍由工作流验收。

重名检测忽略 Unicode 兼容变体、大小写和空白，不改输出原字。作者前缀由
`author_prefixes` 明确提供，脚本不猜品牌归属。
