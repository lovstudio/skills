# 系统提示词片段

这段托管块保证机制“每次都会触发”：宿主每次加载系统提示词时都会读到它，
所以被动情绪感知与落账不再依赖用户显式调用。

## 片段位置

- 原文：[assets/system-prompt-block.md](../assets/system-prompt-block.md)
- 安装器：`scripts/install_feedback_loop.py` 读取该文件，并把整段托管块
  合并进宿主指令文件。

## 托管块约定

```text
<!-- feedback-loop:begin v1 -->
...片段内容...
<!-- feedback-loop:end -->
```

- 同版本内容一致时跳过，不重复写入。
- 内容变化时整块替换，替换前备份目标文件。
- 宿主已有同名标记时只更新块内内容，块外内容不动。

## 片段全文

```markdown
<!-- feedback-loop:begin v1 -->
## 反馈感知与迭代（反馈飞轮）

- 把用户对上一轮结果的态度当作交付信号来读：明确的赞赏、失望、愤怒、反复纠偏、
  无奈或敷衍都要识别；不把沉默当作满意。
- 检测到强度大于等于 3 的信号时，记录一条反馈事件：宿主与会话、时间、用户原话、
  极性、强度、作用域、处置与最终结果；不记录凭据，也不整段转录私人对话。
- 负信号先做最小修复并在原路径回读；可复用反馈写入最窄的规则层
  （任务 → 项目规则 → 技能 → 全局 Prompt），全局规则变化要升版本、校验引用并分发。
- 主动评价（点赞、点踩、表情、评分、显式指令）与被动情绪走同一条闭环；
  闭环结果回填事件，保持可统计。
- 用户要看统计时生成满意度复盘：趋势、未闭环清单与 signal-to-fix 时长。
<!-- feedback-loop:end -->
```

## 安装

```bash
python3 scripts/install_feedback_loop.py --host codex --dry-run
python3 scripts/install_feedback_loop.py --host codex --prompt-target ~/.codex/AGENTS.md
```

宿主位置见 [host-adapters.md](host-adapters.md)。
