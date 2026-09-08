# 已增强素材交接给精剪

本 Skill 负责全片亮度与色彩、低质量诊断、内容分段和源映射；`lov-media-creator` 负责完整观点的独立切片、句子级精剪、字幕、连续混音、包装、成片验收。无需另建同职能 Skill。

```bash
python3 "$SKILL_DIR/scripts/creator_handoff.py" \
  --run "$PREPARED_RUN" --output "$OUTPUT/creator-handoff.json" --decode
```

只有 `rendered` 的实际完成任务才能导出；预览、未完成渲染、变化的计划/源文件、缺段、重排或哈希不符都会失败。`--decode` 会完整解码交接视频，省略时如实记录 `full_decode: false`，不冒充实际解码完成。

输出 `media-preprocess-handoff/v1`，包含原片身份、计划与 manifest 哈希、各段原片 start/end、段文件绝对路径、文件 SHA-256、段内起点 0、增强已应用标记和取舍状态。保留 `review` 素材与已删除区间的原时间；不把剩余片段拼起来重新编号为原片秒数。

例如原片 `[20,30]` 和 `[40,60]` 两段增强后，各自本地播放从 0 秒开始。原片 45 秒对应第二段本地 5 秒；30–40 秒的删除区间仍是缺口，下游不得用拼接后的 35 秒代替原片 35 秒。

完整增强计划即使已成功渲染，也仍标记 `full-recording-content-review-required`，不能声称所有有传播价值的内容已选完。`semantic-reviewed` 仅表示上游确实作出语义分段决策；其中 `review` 仍需下游继续核验。文件完好、画面明亮、内容有价值是三种不同结论。

下游将该 JSON 填入独立切片计划的 `handoff`。画面从已增强段取，不再次提亮；人声按原片秒数从原片 PCM 裁切。缺失范围不能用相邻画面补齐或静默压缩时间轴。

同时交付可直接打开的 MP4 链接与简明列表；HTML 素材库仅作辅助。交接文件旁自动生成 `.md` 列表，带原时间码、取舍与 MP4 入口，方便用户抽看。
