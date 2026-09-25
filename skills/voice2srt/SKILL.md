---
name: lov-voice2srt
description: >
  把录音、播客或视频转成可剪辑的 SRT、JSON 与纯文本，复用 OpenLess 或
  lov-personal-vocabulary 词库增强专有名词，并在付费云端 ASR 前显示成本。Use it to transcribe audio or create subtitles with hotwords.
license: MIT
depends_on:
  - lov-branding-consistency
metadata:
  author: skill-publisher
  version: "0.1.1"
  card_standard: lovstudio/skill-card/v1
  tags:
    - asr
    - srt
    - subtitles
    - hotwords
    - openless
  compatibility: "Portable Agent Skills format. Python 3.9+, FFmpeg/FFprobe, and a supported cloud ASR credential."
  dependencies: []
---

# 语音成字幕 · Voice to Subtitles

输入音频或视频，输出 UTF-8 SRT、结构化 cue JSON、纯文本与可审计报告。
默认复用可发现的 OpenLess 词库；也可直接接收 `lov-personal-vocabulary` 的
canonical `vocabulary.json`，但不接管词库的增删、学习与同步。

## Triggers

### Activate when

- “把这段录音转成 SRT，专业词用我的个人词库纠正。”
- “复用 OpenLess 的模型和热词，把这个视频转成带时间戳字幕。”
- “Transcribe this audio and create an SRT using my hotword vocabulary.”

### Do not activate when

- 用户只要维护、合并或同步个人词库；交给 `lov-personal-vocabulary`。
- 用户已经有字幕，只要加学习注释或人物艺术层；交给 `lov-subtitle-freedom-skill`。
- 用户要完成视频剪辑、混音、烧录和成片质检；交给 `lov-media-creator`。

## User Profile (cross-session)

Every generated Skill is connected to the shared `user-profile/v1` contract in
`skill.yaml`. Read the shared user, brand, workspace, preferences, and this
Skill's `skills.<skill_id>` namespace at the start of every run. Keep the source
portable: resolved personal values belong in the shared profile, never here.

When the user directly states a durable preference or brand fact, persist it
through `scripts/profile_store.py` and report the saved profile path. Put
Skill-specific values under `records.<field>`; use `brand.<field>` or
`user.<field>` for shared values. Do not persist inferred secrets or credentials.
See `references/user-profile.md` for the complete contract.

## Skill Group Composition

Read `references/skill-composition.md` before deciding whether to invoke or
extend any adjacent capability. The record distinguishes optional upstream and
downstream handoffs from embedded Kit modules. Do not silently depend on a
sibling Skill that is not shipped with this source.

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve skill root, dependencies, and runtime context

- Use `SKILL_DIR` if the environment provides it.
- Otherwise infer the installed skill directory from the current skill context.
- Verify every required local module, reference, script, and asset before work.
- If a required resource is missing, name its expected relative path and stop
  before producing a partial result.

When running scripts manually:

```bash
export SKILL_DIR="/path/to/lov-voice2srt"
```

Resolve `context.profile` on every invocation. The precedence is current request,
project context, Skill-specific profile records, shared preferences, shared
brand/user profile, then safe defaults. A direct user statement about a durable
preference or brand fact should be saved with `scripts/profile_store.py record`
using `--confirm`, followed by a concise saved-path report.

### Step 1: Understand the requested outcome

- Separate internal context from user-visible output.
- Confirm the input, intended audience, expected deliverable, and evidence gaps.
- Record one real user case before calling the Skill complete. The case must show
  the input, the prompt or minimum brief, and the output; do not invent results.

在调用付费 API 前必须运行 `--dry-run`，向用户显示输入时长、provider、model、
词库条数、分段方案与预计费用。只有用户已明确接受本次 API 费用，才使用
`--confirm-cost`。用户只说“以后可以接受 API 成本”时，仍要给出本次金额摘要。

### Step 1.5: Analyze nearby Skills before implementation

- Inspect related local and installed Skills by routing contract and concrete
  input/output, not by filename alone.
- Record upstream, core, downstream, overlap, and not-composed decisions in
  `references/skill-composition.md`.
- Keep sibling Skills optional and artifact-based. When stages require hard
  coupling for one outcome, create a self-contained Kit instead.

### Step 2: Execute the workflow

1. 读取媒体时长，解析 provider 与 runtime-only credential。优先级为本次参数、
   用户显式启用的 OpenLess Keychain、环境变量；绝不把 key 写入命令日志或报告。
   OpenLess 渠道化后 map key 可能仍是旧 provider 名，必须以 `providerType` 判断真实
   协议，不能把 `activeAsrProvider` 或 map key 当作密钥类型。
2. 解析词库。支持 OpenLess 数组 `{phrase, enabled}`、canonical
   `{entries:[...]}` 与一行一词文本；过滤禁用项、空词和大小写重复项，默认最多
   80 个。只在用户选择 `--no-vocabulary` 时关闭。
3. provider 选择：
   - `dashscope`：`qwen-audio-3.0-asr-flash`，默认按 240 秒转为 16 kHz 单声道
     MP3 分段；即时热词权重为 5，通过 SSE 收集每个 `sentence_end=true` 的句级
     与词级时间戳。兼容 provider 返回单句或分段累计 `sentence` 两种行为；累计
     结果必须按前缀 words/text 做增量差分，再按强标点、最长约 5.2 秒或 24 字的
     软标点切成可读 cue。适合已有 `DASHSCOPE_API_KEY`、不想授权 Keychain 的运行。
   - `volcengine`：大模型录音文件极速接口，把整段音频压成 MP3 后一次提交，
     使用 `show_utterances` 与 OpenLess 同款 `context.hotwords`。支持环境变量凭据；
     `--openless-keychain` 只在用户明确允许一次性读取时使用。
   - `whisper-cpp`：无云端凭据或音频不能离机时的本地回退；读取
     `WHISPER_CPP_MODEL` 或本机缓存的 large-v3-turbo 模型，把个人词库作为
     initial prompt。它不产生 API 费用，但不把 prompt 传入等同于术语必然正确。
4. 合并分段偏移，去除边界重复，校正重叠并输出 `transcript.srt`、
   `transcript.json`、`transcript.txt`、`report.json` 与脱敏 raw responses。

先做成本预检：

```bash
python3 "$SKILL_DIR/scripts/voice2srt.py" INPUT \
  --output-dir OUTPUT_DIR \
  --provider dashscope \
  --vocabulary VOCABULARY_JSON \
  --dry-run
```

用户确认本次费用后执行：

```bash
python3 "$SKILL_DIR/scripts/voice2srt.py" INPUT \
  --output-dir OUTPUT_DIR \
  --provider dashscope \
  --vocabulary VOCABULARY_JSON \
  --openless-keychain \
  --confirm-cost
```

如需复用 OpenLess 当前火山引擎凭据，在 macOS 钥匙串弹窗可见且用户允许时：

```bash
python3 "$SKILL_DIR/scripts/voice2srt.py" INPUT \
  --output-dir OUTPUT_DIR \
  --provider volcengine \
  --openless-keychain \
  --confirm-cost
```

不要通过修改 Keychain ACL、导出明文凭据或把凭据复制到 Profile 来消除授权弹窗。

### Step 3: Validate the deliverable

- 要求至少一个 cue，所有时间戳非负、`end > start`、不重叠，最后时间不超出媒体
  时长 1 秒。用 FFmpeg 把 SRT 转成 WebVTT 做 parser smoke test。
- 抽查词库中的项目名、产品名和英文缩写；报告“出现/未出现”，不要因为热词被
  传给 API 就宣称识别正确。
- 若有本地 Whisper 基线，比较专有词召回、cue 数、覆盖区间、运行耗时与成本；
  不以单一 cue 数量判断模型优劣。
- 报告确切输出路径、provider/model、实际或预计计费秒数、词库条数、耗时、
  validation 与仍未核验的内容。
- 运行 `python3 scripts/validate_skill.py .`、`python3 scripts/test_voice2srt.py`
  和 `python3 scripts/voice2srt.py --help`，并验证 trust bundle。若调用成功但
  parser 规则后来修正，可运行 `rebuild_dashscope.py --output-dir OUTPUT_DIR` 从 raw
  重建，不重复调用 API。

## Dependencies

- Python 3.9+ standard library。
- FFmpeg 与 FFprobe。
- 云端 provider 凭据：`DASHSCOPE_API_KEY`，或 `VOLCENGINE_API_KEY`，或
  `VOLCENGINE_APP_KEY` + `VOLCENGINE_ACCESS_KEY`。
- 本地回退需要 `whisper-cli` 与 ggml 模型，可用 `WHISPER_CPP_MODEL` 指定。
- 可选：macOS `security` 命令，仅在显式 `--openless-keychain` 时读取 OpenLess
  Keychain；`lov-personal-vocabulary` 只通过 JSON 文件交接，不是安装依赖。
