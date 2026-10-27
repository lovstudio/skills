# 时间线格式 `motivational-timeline/v1`

`check_timeline.py` 读这个格式。它是交给渲染执行器之前的“剪辑意图”，不是某个剪辑软件的工程文件；执行器按它搭工程。起步可复制 `assets/timeline.template.json`。

时间单位一律是秒（片内时间），从 0 开始。

## 顶层

| 字段 | 必填 | 说明 |
|---|---|---|
| `schema` | 是 | 固定 `motivational-timeline/v1` |
| `title` | 否 | 片名 |
| `archetype` | 是 | `single-arc` 或 `chorus` |
| `status` | 否 | `draft`（默认）、`review`、`publishable` |
| `duration_s` | 是 | 片长 |
| `beats` | 是 | 节拍 |
| `voice` | 否 | 所有人声：旁白、本人原话、解说、对白 |
| `music` | 否 | 音乐段 |
| `shots` | 否 | 镜头 |
| `titles` | 否 | 片名、画面字幕、落款 |
| `sources` | 否 | 素材账本 |
| `claims` | 否 | 事实账本 |
| `sensitive` | 否 | 敏感题材标记 |

## `beats`

```json
{"id": "b1", "role": "hook", "start": 0, "end": 12, "note": "这拍要让观众知道什么", "intensity": 3}
```

`role` 的取值与顺序规则见 [片型与节拍](archetypes-and-beats.md)。节拍之间不能重叠，空隙超过 1 秒会警告。

## `voice`

```json
{"id": "n01", "kind": "narration", "start": 3.4, "end": 7.8, "text": "旁白原文", "claims": ["B01"]}
{"id": "q01", "kind": "own-words", "start": 32.5, "end": 40.7, "source": "S35", "text": "原文", "subtitle": "中文字幕"}
```

- `kind`：`narration`（原创旁白）、`own-words`（主人公本人）、`commentary`（现场解说）、`dialogue`（其他人的原声）。
- 除旁白外都要有 `source`，且出现在 `sources` 里。
- `claims` 引用事实账本；`disputed` 报错，`single-source` 警告。
- 旁白与任何人声重叠超过 0.15 秒报错；两段录音人声重叠超过 0.15 秒警告。

## `music`

```json
{"id": "m1", "source": "M01", "start": 10.0, "end": 200.6, "in_s": 0.35, "note": "整首连续；94–101s 歌内安静段对准 abyss"}
```

同一 `source` 只能出现一次（不重复挂载）；两段音乐重叠超过 4 秒报错；超过两首会警告。

## `shots`

```json
{"id": "c01", "source": "S25", "start": 0.0, "end": 5.1, "in_s": 955.0}
```

只用来算镜头长度与核对素材是否进了账本；画面细节写在执行器工程里。

## `titles`

```json
{"id": "t01", "kind": "caption", "start": 0.3, "end": 4.9, "text": "2026 年 10 月 6 日", "over": "picture"}
```

`kind`：`title`、`caption`、`lower-third`、`end-card`。`over`：`picture` 或 `black`。
开 `--forbid-black-cards` 时，除 `end-card` 外压在黑底上的文字报错；不开时超过 4 秒警告。

## `sources` 与 `claims`

见 [权利、事实与安全](rights-and-safety.md)。

```json
{"id": "S35", "kind": "interview", "rights": "permitted", "origin": "2019 年电视采访", "verified": true}
{"id": "B01", "text": "2016 年宣布退出国家队", "source": "官方声明与当日报道", "status": "verified"}
```

`status: publishable` 时，所有用到的素材都必须是已清权的四种之一。

## `sensitive`

```json
{"suicide_or_self_harm": true, "safe_messaging_reviewed": true, "help_card": "片尾 4 秒：当地心理援助热线（已核实来源与日期）"}
```

## 体检输出

```json
{"valid": true, "status": "review", "archetype": "single-arc",
 "errors": [], "warnings": [{"code": "rhythm", "message": "..."}],
 "metrics": {"speech.coverage": 0.595, "arc.peak_position": 0.793, "...": "..."}}
```

`valid: false` 时退出码为 1。`metrics` 里与包络同名的指标会和 `assets/reference-envelope.json` 的区间比较，偏出只给警告。
