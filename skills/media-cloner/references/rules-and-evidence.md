# 规则草稿与证据

## 规则草稿

宿主 AI 把规则写成 `research/rules-draft.json`（`media-cloner-draft/v1`，Schema 见 `assets/schemas/rules-draft.schema.json`），由 `cloner.py build` 解析成风格包。草稿里不写证据编号、支持样本或支持数，它们由脚本根据证据算出。

```json
{
  "schema": "media-cloner-draft/v1",
  "style_id": "lov-SLUG-style-media-creator",
  "display_name": "某某风格短视频",
  "version": "0.1.0",
  "status": "ready_with_limits",
  "transcript_source": "research/transcripts (local only; mlx-whisper large-v3, ASR errors kept verbatim)",
  "dimensions": [{"id": "thinking", "summary": "一句话摘要"}],
  "rules": [{
    "id": "thinking.reframe_problem",
    "dimension": "thinking",
    "observation": "可复查的事实",
    "instruction": "下一个 AI 能执行的动作",
    "strength": "required",
    "eligible_sample_count": 7,
    "confidence": "high",
    "scope": "适用范围",
    "exceptions": ["#46 以流通性分析代替显式改写"],
    "validation": {"method": "semantic review of full transcripts", "criterion": "每条至少一处"},
    "evidence": [
      {"kind": "quote", "sample_id": "ID", "t": 200, "q": "你最大的问题不是遇不到合适的", "key": "reframe-1"},
      {"kind": "measurement", "sample_id": "ID", "file": "measurements/training-metrics.json", "field": "metrics.han_per_min", "note": "中位 380 字/分钟"},
      {"kind": "visual", "sample_id": "ID", "start": 0.5, "end": 0.5, "description": "胸部以上居中", "local_reference": "research/measurements/ID/contact.jpg"},
      {"use": "reframe-1"}
    ]
  }],
  "measurement_files": [{"from": "training-metrics.json", "to": "measurements/training-metrics.json"}],
  "metrics": {}, "narrative_templates": [], "layout_templates": [], "audio_visual_triggers": [],
  "guardrails": ["不冒充作者或使用其名字、头像、品牌字样"], "limits": [], "provenance": {}
}
```

上例的 `dimensions` 只列了一个；实际要写全八个。`measurement_files` 的 `from` 相对草稿文件所在目录。

## 证据

### 原话 `quote`

- **只给定位线索。** 写 `t`（大约的秒数）和 `q`（原话片段，标点与空格可省略）。
- **脚本负责定位。** 脚本在转写里找到原文，写回带原标点的 `quote`、所在分段拼成的 `source_excerpt` 和分段起止时间。
- **原样引用。** ASR 误听也照原样引用，在 `limits` 里说明。
- **找不到时。** 构建报告会给出附近原文，据此调整 `t` 或片段；不要修改转写去迁就引文。

### 测量 `measurement`

- **文件来源。** `file` 必须是风格包内 `measurements/` 下的文件，通过 `measurement_files` 复制进来。复制时会自动剔除以留出样本 ID 为键的条目和 `sample_id` 为留出的记录。
- **字段与说明。** `field` 写字段路径或可读说明，`note` 写取值。

### 画面 `visual`

- **只记位置与描述。** `local_reference` 指向工作区里的抽帧或接触表（可用通配符），只用于本地复查，不进入风格包。
- **描述要可复查。** 写看得见的事实，不写观感评价。

### 复用

同一条证据支撑多条规则时，第一次出现处加 `key`，之后用 `{"use": "key"}` 引用。不要复制同一条证据。

## 支持数、强度与置信

- **支持数。** 等于规则证据覆盖的不同训练样本数；`eligible_sample_count` 是适用的训练样本数，必须不小于支持数、不大于训练样本总数。
- **强度。** 不是投票结果，要结合例外判断：
  - `required`：适用样本中普遍出现，缺了就不像；
  - `preferred`：多数出现；
  - `optional`：子类型变体或少数出现。

  `required` 的支持率低于一半时 `verify` 会提示。
- **置信。**
  - `high`：仪器测量或全量通读后多处原话；
  - `medium`：抽样观察或少量原话；
  - `low`：单例或主观判断。

## 其他字段

- **`metrics`。** 用 `cloner.py metrics` 的训练集分布，保留单位、样本数与方法。
- **`narrative_templates`。** 写阶段角色、建议占比、来源样本与说明，标明“比例是编辑建议”。
- **`layout_templates`。** 坐标为左上角归一化，位置是源片位置，适配平台安全区前的值。颜色用聚类得到的十六进制值；字体写“类型 + 未知的精确字体”。
- **`audio_visual_triggers`。** 每条写触发条件、动作和对应规则 ID。
- **`guardrails`。** 写不可迁移的身份、品牌、素材与观点。
- **`limits`。** 写 ASR 误听、测量局限、样本量、留出污染等。
- **`provenance`。** 写取样日期、下载方式、ASR 提供方、标注方式、测量方法与污染说明。

## 构建、校验、冻结

```bash
$PY "$SKILL_DIR/scripts/cloner.py" build --draft research/rules-draft.json --sources research/sources.json \
  --transcripts research/transcripts/normalized --out style-pack/SLUG-v0.1 --per-video research/per-video-analysis.json --project-root .
$PY "$SKILL_DIR/scripts/cloner.py" verify --pack style-pack/SLUG-v0.1 --sources research/sources.json --transcripts research/transcripts/normalized
$PY "$SKILL_DIR/scripts/cloner.py" freeze --pack style-pack/SLUG-v0.1 --sources research/sources.json --transcripts research/transcripts/normalized
```

`verify` 检查以下内容：

- Schema；
- 训练与留出不重叠；
- 证据时间在片长之内；
- 引文是摘录的子串，摘录能在转写里找到，起点对得上分段；
- 测量文件存在；
- 支持数由证据推出，分母合法；
- 八个维度齐全；
- 冻结后内容未改动。

`freeze` 记录画像、证据与拆分的 SHA-256。冻结包不能原地重建，修订开新版本目录。
