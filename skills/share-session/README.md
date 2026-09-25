# 会话分享 · Session Sharing

![Version](https://img.shields.io/badge/version-0.5.0-CC785C)

把一个 Agent 会话（Claude Code / Yoda / 任意 JSONL transcript）转成免费公开或
按 Credits 解锁的 LovStudio 在线页 URL。

Codex Desktop 会话可直接通过 `CODEX_SESSION_ID` 自动发现；同一会话因压缩或恢复
产生多个 rollout 文件时会按时间合并。公开正文只保留用户和助手的可见消息，不上传
开发者指令、推理、工具调用、状态事件或自动注入的 AGENTS、环境、Skill、权限与
Plugin 上下文。即使这些内容被 Codex 折叠进 `role=user` 消息，也会按结构剥离；
发现无法完整清理的已知宿主标记时会在上传前失败并阻止公开。

## 本地安装

标准安装：

```bash
npx skills add lov-share-session -g -y
```

## 用户 Profile（跨 session）

每个生成的 Skill 都会在 `skill.yaml` 中声明 `user-profile/v1`，并从共享
Profile 读取用户、品牌、工作区和本 Skill 的长期记录。用户直接说出的持久
偏好或品牌事实由 `scripts/profile_store.py` 写回 Profile；源代码保持可移植。
**access/refresh token 绝不写入 durable records**，只存本机 gitignore 文件。

用户可以明确保存站立授权：主动调用 `lov-share-session` 时，默认同意把当次当前会话或显式指定会话
脱敏后上传到 `https://lovstudio.ai`，无需二次确认。这个默认不允许后台自动公开其他会话，也不覆盖
其他站点、附件或付费 Session，并可随时取消。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

```bash
python3 scripts/share_session.py --detail concise
# 自动探测当前会话 → 归一化 → Lovstudio 授权 → 上传 → 打印分享 URL

python3 scripts/share_session.py --file /path/to/session.jsonl --detail detailed
# 显式给定 transcript 文件，display-level 烘焙成 ?detail=detailed

python3 scripts/share_session.py \
  --paid-skill lov-target-skill --case-id accepted-case --json
# 价格由服务端按目标 Skill 当前售价的 1/10 向上取整，客户端不能指定
```

输入是会话来源（自动探测或显式文件），输出是一条可复制的 LovStudio 分享 URL。
首次运行会走 device-flow 打印一个授权链接，用户浏览器同意后拿到并缓存 refresh
token，后续运行自动复用。
缓存 access token 过期并返回 401 时，会先 refresh 再重试一次。token 不写入用户
Profile。

## 原子组合

每个新 Skill 都带有 `references/skill-composition.md`。它记录已检查的相邻
Skills、可选的上游/下游交接、重叠处理，以及为何选择 Single Skill 或自包含
Skill Kit。`lov-skill-add-case` 是已声明的下游调用方。

## 可信度卡与用户案例

每个新 Skill 都必须随源代码提供：

- `skill-card.yaml` / `skill-card.md`：用途、负责人、依赖、风险、输出与维度地图。
- `cases/cases.json`：至少一个真实的 Input → Prompt → Output 案例。
- `pricing-card.yaml`：免费或付费都要写清价值锚点、交付边界和复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.10+（CLI 仅用标准库，无需第三方包）
- PyYAML（仅 `validate_skill.py` 校验源需要）

## License

MIT
