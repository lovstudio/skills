# 已有公众号草稿操作

本流程用于读取、局部编辑、替换封面、保存或核验已有公众号草稿。它属于 Publisher 的远端持久化职责，不负责重新创作整篇文章。

## Operating contract

- **Read before write.** 写入前取得同一草稿的标题、摘要、正文、封面、区块与保存状态快照。
- **Minimum mutation.** 只修改用户授权的字段或区块，其他可见内容列入保持不变集合。
- **Persisted truth.** DOM 变化、上传成功或接口 `ret=0` 都不是完成；保存并重新加载后的状态才是事实。
- **Single remote owner.** 新草稿、已有草稿、编辑器字段和正式发布共享 Publisher 的授权门、状态和收据，不再调用独立 Operator。

## Workflow

1. 解析精确草稿目标：优先使用 `media_id` / `appmsgid`；只有当前已登录编辑页时，记录页面 URL 与账号侧可见标识。无法唯一定位时不写入。
2. 按 [文章状态契约](article-state-contract.md) 记录 before snapshot；Cookie、token、账号 ID 与未公开 URL 不进入收据。
3. 写 mutation plan：`operation`、目标路径、锚点、`allowed_changes`、保持不变字段和 `required_results`。
4. 使用当前已授权 transport 做最小修改。富文本先用可撤销探针确认落点；大段内容走编辑器真实粘贴或支持的 API，不只改 DOM。
5. 保存后重新加载同一草稿，记录 after snapshot；封面还要核对实际素材 URL 和平台裁切。
6. 运行 `scripts/verify_article_state.py`，验证只有允许路径发生变化，并逐项检查 required results。
7. 只有保存、重载与状态差异全部通过时报告 `draft_saved`；读取任务止于 `draft_read`。失败时保留目标、阶段和 before/after 差异，不扩大修改范围。

## Verification command

```bash
python3 <skill-dir>/scripts/verify_article_state.py BEFORE.json AFTER.json \
  --allow 'body.word_count' \
  --allow 'blocks.prompt*' \
  --expect 'blocks.prompt.count=1' \
  --expect 'observed.saved=true' \
  --expect 'observed.reloaded=true'
```

删除草稿、覆盖整篇正文或改变共享权限属于高影响操作；即使技术上可执行，也必须取得明确授权并再次核对精确目标。
