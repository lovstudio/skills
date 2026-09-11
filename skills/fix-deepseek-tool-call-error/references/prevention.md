# 预防规则

## 硬约束

1. **`view_image` 独占一条消息**：不与任何其它工具调用同批，包括 `sips`、`rg`、`ls`
   这类瞬间返回的命令。批次里只要存在被缩放的图片，竞态就会出现。
2. **看图前先缩图**：`sips -Z 2048 <图> --out <副本>`，长边不超过 2048 时 Codex 不再缩放，
   也就不会插入 `<image_resize_notice>`。
3. **需要高保真复核时外包看图**：用 `lov-describe-image`（GLM-4V）或更强的外部视觉模型，
   会话内不调用 `view_image`。注意外部小模型会漏字，交付级逐字核对仍要人工或更强模型。

## 落地位置

- 常驻 Prompt：`~/.agents/AGENTS.md` 的规则 `51`（DeepSeek 看图独占回合）。
- 领域 reference：`~/.agents/references/misc-operations.md` 的 `MISC-29`，
  记录判据、命令与事故数量。
- 宿主软链：`~/.codex/AGENTS.md` 指向同一份 `AGENTS.md`，改动后回读确认仍可解析。

## 可选：关掉缩放提示（需用户同意，尚未在 app 侧验证）

- 目标：保留拍照与看图能力，只去掉那条 developer 消息。
- 方式：在 `~/.codex/config.toml` 的 `[features]` 表里加一行 `image_resize_notice = false`，
  改动前备份文件。
- 代价：模型不再被告知图片被缩放，做像素级测量时会失去口径提示。
- 验证：改完后在一个一次性 thread 里让 agent 同批看两张超长图；不报错才算成立。
- 未验证前不要写入，也不要在用户没同意时改动全局配置。

## 反模式

- **不要把 `view_image` 关闭**：`[features] view_image = false` 会在同一台机器上砍掉所有会话
  的看图能力，代价远超收益；用户明确拒绝过这种一刀切。
- **不要靠重试**：同一 thread 重试只会重复同一秒的失败，并消耗额度。
- **不要 fork 中毒 thread**：fork 继承坏历史，同样 400。

## 适用边界

- 仅适用于 `provider=yoda` 且 `wire_api = "responses"` 的 DeepSeek 直连配置。
- 换成容忍该顺序的 provider 时，这些约束可以放宽；重新出现同类 400 时再启用。
