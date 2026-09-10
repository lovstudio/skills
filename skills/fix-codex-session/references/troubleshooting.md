# Codex 会话失效 · 排查与恢复手册

## 症状

一条 Codex 线程在 UI 里显示 `systemError`，尝试继续时会复现：

```text
No tool output found for tool call call_<....>.
```

底层错误码为 `invalid_request_error`。线程标题、之前的对话记录、项目文件和
已生成的交付物都还在，但**无法再向这条线程发送新的任务**。

## 根因

Codex 把每条线程的完整对话持久化到 JSONL rollout 文件里（默认
`~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`）。每次继续线程时，宿主会根据
该 rollout 重建发给模型的请求。请求里每出现一个 `function_call`（工具调用）项，
就必须在同一请求中带上对应的 `function_call_output`（工具结果）项；两者通过
`call_id` 配对。

当 rollout 尾部出现一个**有调用、无输出**（或输出被丢在非工具消息之后）的
悬挂工具项时，重建出的请求就带了一个没有配对的工具调用，服务端因此拒绝：

```text
No tool output found for tool call call_<....>.
```

触发这个状态的常见条件：

1. 同一轮里并行发出多个 `view_image`（或别的图片/大结果工具）调用，而宿主在
   各工具结果之间插入了非工具消息（例如喂养给模型的 `developer` 图片消息），
   导致后面的工具输出没有连续跟在各自的调用后面。
2. 工具结果体量很大（例如 base64 图片，几十到几百 KB）。走自定义模型提供商
   或代理（如 `deepseek` via ccswitch/custom base URL）时，大结果更可能被
   截断、去重或乱序。
3. 线程的 `model_provider` 为 `custom`/`vscode`/代理时，服务端重建规则更严格，
   更容易命中这一校验。

因为错误发生在“重建历史”阶段，而不是“执行工具”阶段，所以**每次**尝试继续
都会重新命中同一句报错，重试无用。

## 诊断

在事件边界内逐项核对 `call_id`，找出“有调用无输出”的项即可确认：

1. 定位此线程的 rollout 文件（`state_5.sqlite` 的 `threads.rollout_path`，或
   在 `~/.codex/sessions` 下按线程 id 搜索）。
2. 解析 JSONL，抽取所有 `response_item` 中 `function_call` / `function_call_output`
   的 `call_id`。
3. 若无输出的 `function_call` 出现在最后一次 `task_complete` 附近，即为毒点。

用随包脚本做只读诊断：

```bash
python3 "$SKILL_DIR/scripts/fix_codex_session.py" "<thread_id>" --codex-home "$HOME/.codex" --json
```

报告会给出每个 rollout 的 `calls` / `outputs` / `dangling_calls` 与
`last_turn_error`；`poisoned=true` 说明该文件的尾部会导致“无工具输出”。

## 修复

**首选：从磁盘交付物继续，不复活旧历史。** 出错线程的真实产出（Markdown、PDF、
图片、代码）都已保存在项目目录里，内容没有丢。在项目已产出内容的基础上新开一条
干净线程，把收尾工作做完，是最稳的路径；不要再向旧线程发消息。

**次选：截断 rollout 到最后一个健康里程碑。** 若必须保留同一线程，可用脚本写出
一个修复后的 rollout，把毒点之后的内容裁掉：

```bash
python3 "$SKILL_DIR/scripts/fix_codex_session.py" "<thread_id>" --fix --codex-home "$HOME/.codex"
```

默认写 `<rollout>.repaired.jsonl`，不覆盖原文件。仅当你确认原文件已备份且宿主
未在运行该线程时，才用 `--write` 原地替换并自动留存 `.bak` 备份。无论是否修复，
脚本都不会改动项目目录里的任何交付物。

> 注意：如果宿主把线程状态缓存在内存里，修改 rollout 文件后通常需要重启宿主，
> 或让线程重新从磁盘加载，修复才生效。因此多数场景下“新开线程 + 从交付物接手”
> 比“修复旧 rollout”更可靠。

## Provider 切换 · Model provider not found

### 症状

在 OpenAI Official、原生 API 或不同中转站之间切换后，打开旧 thread 时出现：

```text
ChatGPT can't load config.toml, so this thread can't resume.
Fix config.toml: Model provider `custom` not found.
After saving the file, reopen the thread.
```

### 根因

Codex 在 `state_*.sqlite` 的 `threads.model_provider` 中记住每条 thread 创建时
使用的 provider 名。CC Switch 等工具切换 provider 时只会重写 `config.toml`；
如果新的配置删掉了旧的 `[model_providers.<name>]`，旧 thread 引用的名字就
无法解析。这里的 `custom` 一般不是配置损坏，而是 thread 元数据还没有跟上
当前 provider；`threads.model_provider` 为空字符串时也会触发同类报错。

### 修复边界

**只同步 SQLite 索引，不改 rollout JSONL。** paginated 会话依赖
`end_byte_offset` / `end_ordinal`，任何插入、删除或重排都会改变字节位置，
可能把原本可恢复的历史变成 `invalid paginated history lineage`。跨 provider
正文本身不兼容时，新建线程接手比改坏 rollout 更安全。
Codex 恢复线程时以 `threads` 行的 provider 为准；rollout 首行的
`session_meta` 可以保留原始 provider 作为历史记录，不需要为了让索引可用而重写。

先做只读预演：

```bash
python3 "$SKILL_DIR/scripts/sync_thread_provider.py" --codex-home "$HOME/.codex" --json
```

默认只迁移“当前配置里已不存在的 provider”，不会把 built-in `openai` 旧
thread 一起改成当前中转站；需要显式全局迁移时再加 `--all-threads`。确认
`candidate_count` 后，退出 Codex Desktop 再应用：

```bash
python3 "$SKILL_DIR/scripts/sync_thread_provider.py" --codex-home "$HOME/.codex" --apply
```

脚本会先用 SQLite `backup()` 写一份一致备份，再更新
`threads.model_provider`；遇到 `-wal` / `-shm` sidecar 会警告并拒绝应用，
除非显式传 `--force`。应用后重启 Codex Desktop，让 UI 重新读取索引。

如果只想恢复某一条 thread，也可以先让 provider 名称重新可解析：临时把旧的
`[model_providers.<name>]` 补回 `config.toml`，或使用
`--source-provider custom` 只迁移来自该 provider 的 thread。

## 避免

- 需要看图时**一次只看一张**，不要在同一轮并行 `view_image` 多个大图。
- 工具结果之间若有喂给模型的消息，尽量让同一批工具输出连续排列，避免被非工具
  消息切断配对。
- 走自定义模型提供商 / 代理时，更保守地使用图片类工具；这类工具结果往往是
  base64 大块，容易被截断或乱序。
- 一个任务完成到干净的节点（出现一次正常的 assistant 回复）后再收尾，不要停在
  “工具刚要返回、下一步还没生成”的中间态。
- 一旦出现“No tool output found”，立即改用“从已保存交付物继续”的路径，而不是
  反复重试同一条线程。
