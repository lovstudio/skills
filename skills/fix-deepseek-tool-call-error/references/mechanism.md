# 机制与证据

## 因果链

1. Codex 把同一轮里模型发出的多个工具调用当作一个批次执行。
2. 批次里出现 `view_image`，且原图超过图片预算时，Codex 会缩放图片，并在工具输出旁插入
   一条 `<image_resize_notice>` developer 消息，说明原尺寸与缩放后尺寸。
3. DeepSeek 的 `/responses` 要求 `function_call` 与自己的 `function_call_output` 保持相邻；
   这条插入的消息破坏了该约束，同时该消息的落盘成为"批次可以继续"的信号。
4. 下一次请求因此在批次其余调用返回之前发出，body 里出现没有输出的 `function_call`。
5. DeepSeek 拒绝整轮请求：

   ```
   {"error":{"message":"No tool output found for tool call call_01_...","type":"invalid_request_error"}}
   ```

6. 被拒的调用留在 thread 的内存历史里；此后该 thread 的每一轮（以及它的每个 fork）
   都会重发同一条孤儿调用，因此新增轮次在 1 秒级时间内以同样的报错失败。
   磁盘上的 rollout 反而是自洽的——这正是"记录完整、会话已死"的原因。

## 本机证据（2026-09-11）

`scripts/scan_deepseek_sessions.py` 全量扫描得到 8 起事故、6 条会话、1 条确认锁死：

| 时间 (UTC) | session | 被拒调用 | 同批调用 | 变体 | 重复 |
| --- | --- | --- | --- | --- | --- |
| 01:28:37 | 01a08c6b | view_image | exec_command, view_image | 含缩放提示 | 1 |
| 05:40:36 | 01a08ee7 | view_image | exec_command, view_image | 含缩放提示 | 3 |
| 05:41:11 | 01a08ee7 | view_image | view_image | 含缩放提示 | 3 |
| 05:41:25 | 01a08ee7 | view_image | view_image | 含缩放提示 | 3 |
| 05:42:27 | 01a08efc | view_image | view_image | 含缩放提示 | 1 |
| 05:56:45 | 01a08f09 | view_image | exec_command, view_image | 含缩放提示 | 1 |
| 08:26:55 | 01a08f92 | view_image | exec_command, view_image | 含缩放提示 | 1 |
| 08:36:48 | 01a08f9c | exec_command | exec_command, view_image | 含缩放提示 | 1 |

关键读法：

- 八起事故的批次里都有 `view_image`，且都伴随缩放提示；被拒的既可能是第二张图，
  也可能是与图片同批的一条快命令（01a08f9c 的 `sips`），说明风险来自"批次里有被缩放的图"，
  而不是"同批有两张图"。
- 01a08ee7 在同一 call id 上连续失败 3 次，是锁死的判定样本：第 2、3 轮分别在 1.0 秒和
  10.2 秒内失败，说明坏调用已进入内存历史。
- 事故跨越两个完全不同的任务（电影截图排查与信息图复核），不依赖具体项目内容。

## 对照实验

同一 provider、同一模型、临时 `CODEX_HOME`，让模型在同一条消息里并行发两个 `view_image`
（间隔 68 毫秒，与事故现场的 68–112 毫秒同量级）：整轮通过，rollout 中没有出现任何
`<image_resize_notice>`。也就是说，命令行的这条路径没有触发插入，因而没有复现 400。
该实验把嫌疑集中到"缩放提示"这一环，而不是"并行工具调用"本身。

## 上游记录

- `openai/codex#44604`：下一次采样请求先于批次最后一个工具输出落盘发出，并给出两条复现
  （两张 `view_image`；`view_image` 与一条耗时 30 秒的命令同批），thread 之后永久失败。
- `deepseek-ai/DeepSeek-V3#1588`：`function_call` 与其输出之间插入 developer 消息即被拒。
- `farion1231/cc-switch#7190`：标题直接点名 `image_resize_notice` 插队导致 DeepSeek 400。

## 尚未验证的部分

- app 侧 A/B：把图片预先缩到长边 2048 以内、或关掉 `image_resize_notice` 这个 feature
  gate 之后，是否不再复现。命令行侧已通过，应用侧仍待一次受控 thread 验证。
- 其它触发路径（PostToolUse hook 注入上下文、被中断的批次）在本机尚未观察到实例，
  仅见于上游报告。

