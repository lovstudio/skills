# Discourse Audit Workflow

这是 `lov-human-writing` 的内部篇章阶段，不暴露独立 Skill 名称。

## 输入

- 草稿；
- 作者性账本；
- `references/authorship-integrity.md`。

## 步骤

1. 逐项检查命题来源、因果压缩、反例存活、收束压力、读者推理空间、结构非对称
   与作者决定痕迹。
2. 每项发现引用最小充分原文证据，输出 `dimension / evidence / impact / edit`。
3. 区分“材料本来简单”与“无依据地压平材料”。清楚、线性和完整可以是正确选择。
4. 不输出 AI 概率或平台通过结论。
5. 不建议为了像人而增加支线、时间跳跃、模糊、错误或开放式结尾。

## 编辑旁白与讲义腔

逐段追问：本段新增了什么事实、操作、因果、作者判断或必要衔接？检查标题是否指向
实际内容，是否在答案前另加“先厘清”、在风险前另加“不能忽略”、在结尾另加
“解决了具体问题”。检查分类是否由真实决策需要产生，以及“这一段、另一层”等
占位词能否还原为可指认对象。不要仅按词表替换：未命中词表也可能做同一种无效铺垫。

保留必要定义、操作顺序、真实对照、不确定性和引语。每处保留或修改须有原文证据。
`measure.py` 仅提供表层统计；段长、套话频率全部合格不等于文风可交付。

## 可复核的审读记录

1. 运行 `python3 scripts/discourse_gate.py --input draft.md --output scan.json`。
   脚本列出段落、标题及部分可观察句式，退出码 1 和 `needs_review` 是默认状态。
2. 审读全部单元，包括无词面命中的段落。单独写 review.json：
   `schema: lov-human-writing/discourse-review/v1`、`input_sha256`（来自扫描结果）、
   `reviewer`（如 authoring-agent，不能冒称用户或独立评委）、`units` 列表。
   每项记录扫描给出的 `id`、`decision`（accept / revise / protected）、`reason`。
   理由必须说明本段的信息或必要作用；命中而保留时解释上下文，不写“已检查，无问题”。
   引语、转载与固定品牌原文可标 protected，但要指明来源；这不是整篇免审。
3. 运行 `python3 scripts/discourse_gate.py --input draft.md --review review.json
   --output writing-review.json`。遗漏、重复、待返修单元及过期文本散列都阻止通过。
   返修后重新扫描并审读最终稿，不复制旧散列冒充新审读。
4. 交付 `writing-review.json`，保留原始 review.json 供复核。报告的 accepted 仅表示
   审读覆盖及记录校验完成，不是人类作者身份判定，也不保证审读者判断正确。

扫描器无法穷尽同义表达或判断文风。语义审读必须真实执行，禁止循环填充默认好评，
禁止把没有命中自动写成 accepted。用户否定稿件时，以直接反馈重新校准。
