---
name: sgc-media-acquisition
description: >
  在下载前检查磁盘空间，通过 qBittorrent 并行测试多个候选、选择持续速度更好的来源、观测进度并在停滞时切换；适用于“开始下载，太慢就换源”、"race sources and finish the download"。
license: MIT
metadata:
  author: contributors
  version: "0.2.0"
  tags:
    - storage-preflight
    - qbittorrent
    - aria2
    - download-monitoring
    - failover
  compatibility: "Python 3.9+; qBittorrent 5.x Web API with aria2 1.36+ as resumable fallback."
  dependencies:
    - python
    - qbittorrent
---

# Media Acquisition

Treat download as an observed job with recovery, not a fire-and-forget client action.
Use qBittorrent for integrated discovery and initial probes, with aria2 available as a
same-input resumable transport when a swarm behaves better outside qBittorrent.

## Triggers

### Activate when

- 用户说“开始下载，太慢就自动换源”“同时测试几个，选最快的”。
- 用户给出一个或多个 Magnet，希望下载完成并保留最优任务。
- The user asks to race sources, monitor a download, or recover a stalled transfer.

### Do not activate when

- 用户还在比较内容不同的剪辑版本，尚未作出用户偏好决定。
- 目的磁盘的容量预检没有通过。
- The user asks only to search or rank releases without downloading.

## Workflow (MANDATORY)

### Step 0: Load safeguards and connection

Read `$KIT_DIR/references/acquisition-policy.md` and resolved configuration. Verify
qBittorrent login before adding tasks. If first-run initialization is needed, keep the
WebUI on loopback and credentials in the operating system credential store. Query
existing hashes and mark them as
pre-existing; never delete, relocate, or retag those tasks.

### Step 1: Capacity preflight

Run `scripts/storage_preflight.py` with the decision file, destination, probe count,
temporary probe allowance, and free-space reserve. Stop before transfer when the JSON
result says `ok=false`; surface required, available, and shortfall.

### Step 2: Create an isolated probe job

Use a unique tag and `$OUTPUT/.media-fetch-probes/$JOB_ID`. Probe no more than the
configured concurrency. Keep each candidate in its own child directory so exact losing
payloads can be cleaned without broad path deletion.

### Step 3: Measure sustained usefulness

Run `scripts/qbittorrent_acquire.py`. Ignore the warm-up window when comparing. Score
sustained speed, availability, peers, progress, and ETA. A candidate with a brief burst
followed by zero is weaker than a stable source. Keep advertised seeders and observed
health in separate fields.

### Step 4: Continue and recover

- Move the winner to the final destination and keep polling until completion.
- Provide a user progress update at least once per minute while tools are active.
- If progress and traffic remain below thresholds for `stall_seconds`, pause the
  current task and resume the next proven candidate.
- If the same Magnet or Torrent input is better served by aria2, run:

  ```bash
  python3 "$KIT_DIR/scripts/aria2_acquire.py" \
    --input INPUT --job-id JOB_ID --output-dir OUTPUT_DIR \
    --result ACQUISITION_JSON --watch --no-proxy
  ```

  Keep the `.aria2` state in the isolated job directory, record the backend switch,
  and verify the final payload before relocation.
- If the complete candidate list is exhausted, preserve the best paused job, return to
  discovery for the next wave, preflight the incremental probe budget, and continue.
- Use a finite configured search wave per process; the agent owns the outer retry loop
  and remains in conversation with the user.

### Step 5: Finish exact cleanup

After one task reports complete and its files exist, remove only tasks created by this
job and exact isolated losing directories. Keep logs and the JSON acquisition report.
Never delete by wildcard, parent directory, candidate name alone, or unresolved path.

## Dependencies

qBittorrent 5.x with WebUI enabled. Connection values come from
`QBITTORRENT_URL`, `QBITTORRENT_USERNAME`, `QBITTORRENT_PASSWORD`, or the shared
profile; secrets stay outside committed source.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
