# 规则草稿与证据

## 草稿结构

宿主 AI 写 `research/rules-draft.json`（`blogger-cloner-draft/v1`），`cloner.py build` 解析成风格包。草稿里不写证据编号与支持数，它们由脚本根据证据算出。

```json
{
  "schema": "blogger-cloner-draft/v1",
  "style_id": "lov-SLUG-style-writer",
  "display_name": "某某风格写作",
  "version": "0.1.0",
  "essence": "一句话本质",
  "dimensions": [{"id": "voice", "summary": "一句话摘要"}],
  "rules": [{
    "id": "rhythm.setup_reveal",
    "dimension": "rhythm",
    "observation": "可复查的事实",
    "instruction": "下一个 AI 能执行的写法",
    "strength": "preferred",
    "eligible_sample_count": 15,
    "confidence": "high",
    "scope": "适用范围",
    "exceptions": ["某篇的例外"],
    "check": "验收方式",
    "evidence": [
      {"kind": "quote", "sample_id": "ID", "q": "原话片段", "block": 52, "key": "k1"},
      {"kind": "title", "sample_id": "ID"},
      {"kind": "observation", "sample_id": "ID", "blocks": [52, 54], "description": "看得见的结构事实"},
      {"kind": "measurement", "field": "distributions.short_para_ratio", "note": "中位 0.39"},
      {"use": "k1"}
    ]
  }],
  "templates": [{"id": "news-take", "name": "发布解读", "source_samples": ["ID"], "notes": "", "stages": [{"role": "", "share": "", "notes": ""}]}],
  "brand": {"positioning": "", "audience": "", "topics": [], "brand_slots": [{"position": "", "function": "", "pattern": ""}], "identity_tokens": []},
  "guardrails": [], "limits": [], "unknowns": [], "provenance": {}
}
```

上例的 `dimensions` 只列了一个，实际要写全八个，且每个维度至少一条规则。

## 证据

### 原话 `quote`

- 写 `sample_id`、`q`（原话片段）和 `block`（`show` 给出的段号提示）。
- 匹配时忽略空格、标点和大小写；脚本在原文中定位后写回带原标点的 `quote` 和前后约 30 字的 `excerpt`。
- 片段长度 4–60 个字（去掉标点后）。超过 60 字的长句只引关键部分，避免把原文成段搬进风格包。
- 找不到时，构建报告给出最接近的三段原文。调整片段或段号，不改原文。
- 只能引用训练样本；引用留出样本会被拒绝。

### 标题 `title`

只写 `sample_id`，脚本复制登记的标题。用于标题规则。

### 观察 `observation`

`blocks: [起, 止]` 指向原文段号区间，`description` 写看得见的结构事实（“三段同构排比”），不写观感评价。

### 度量 `measurement`

`field` 是 `research/metrics/train.json` 里的点路径，如 `distributions.one_sentence_para_ratio`、`signature_ngrams.distinctive.0`、`boilerplate.0.df`。脚本写回实际值。`note` 要在最后一次运行 `metrics` 之后再写，数字以实际值为准。

### 复用

同一条证据支撑多条规则时，第一次出现处加 `key`，之后用 `{"use": "key"}`。

## 支持数、强度与置信

- **支持数** = 证据覆盖的不同训练样本数；`eligible_sample_count` 是规则适用的训练样本数，不小于支持数、不大于训练总数。
- **强度**：`required` 缺了就不像，适用样本中普遍出现；`preferred` 多数出现；`optional` 子类型变体或少数出现。`required` 的引用覆盖不到适用样本的一半、又没有度量证据时，`verify` 会提示。
- **置信**：`high` 全量通读后多处原话或仪器度量；`medium` 少量原话或抽样观察；`low` 单例或主观判断。
- 不为凑支持数补引文；证据少就降强度或缩范围。

## 构建、校验、冻结

`build` 写出风格包：`style-profile.json`、`evidence.jsonl`、`metrics.train.json`、`brand.json`、`corpus-shingles.json`（训练与留出全文的哈希片段指纹，只用于重合检测）、`build-report.json`。

`verify` 检查：拆分摘要一致、训练与留出不重叠、每条引文是原文段落的精确子串、标题与登记一致、支持数由证据推出、八个维度齐全、冻结后文件未改。

`freeze` 记录各文件 SHA-256。冻结包不能原地重建，修订开新版本目录（`SLUG-v0.2`）。在留出解封之后构建的新版本会被标记为受污染，留出结果不能算独立命中。
