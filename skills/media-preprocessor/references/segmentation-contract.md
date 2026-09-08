# 内容取舍与源时间线

先判断价值，再判断质量与可修复性。静态课件上的有效讲述、安静但有意义的操作、必要思考停顿和关键失败过程都可能应保留。明亮清楚的空场不优先于欠曝但有独特信息的解释。

Agent 必须阅读完整转录并查看画面。ASR 会漏字、幻觉和跨块重复，特别是音乐、远处谈话与长静音；查不清时 review 保留。技术信号只提供线索，不能用几个摘要代替全片审阅。

按问题、方法、演示、结果或独立答疑分段，自然时长服从内容。保留必要桥接，不为固定时长切碎句子。

## 数据格式

计划 schema 为 media-preprocess-plan/v1：

- source 来自 probe，含大小、时长和两端指纹；两端指纹不是全文件哈希。
- basis 为 technical-proposal-only（只可预览）、enhancement-only（完整增强、无内容取舍）或 semantic-reviewed（已审阅内容）。前两者只能使用 review，不能删除或声称完成内容判断。
- grade 为整组增强数值配置，段级可覆盖。
- segments 按源顺序连续覆盖 0 到源片结束，不能有空缺、重叠或隐性丢时长。
- 每段包含唯一安全 id、start/end 秒、title、decision、reason、evidence。
- drop 另需 contains_unique_content=false，实际完成 review.content_checked、visual_checked、boundary_checked。

evidence 写可回看的转录时间范围、源帧/声音窗口和观察。删除理由要具体，不能只写“质量差”。review 是事实，不是占位符。

## 剪口与交付

保留完整词头、词尾、否定词和结论。时间戳定位上下文，有听审能力时回听原声后落刀；高风险剪口补逐字对齐和拼接重转写。宿主没有听审能力时，完整转录、词级时间估计、原声波形和剪口画面共同核验，明确标注未听审，不把 ASR 回读说成人工听审。无法确认时扩大保留区间或设为 review，不用淡化掩盖断句。

keep 与 review 均导出，review 显示在清单和审阅页。drop 从派生素材库排除，源片和理由保留。段文件时间归零，manifest 保留源起止与新时间线位置。

完整语义单元可连续切成独立文件，不强求每个边界都删时长。粗预处理不等于逐个口水词精剪，报告实际粒度。实现 CLI、写 JSON 或发起渲染都不是全片完成。

本地 ASR 使用 [whisper.cpp](https://github.com/ggml-org/whisper.cpp) 或 [MLX Whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper)；模型显式传入，原始输出保留。大模型执行变慢不等于应该静默降级模型。
