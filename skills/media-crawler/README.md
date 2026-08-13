# lov-media-crawler

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

给一个公开且有权保存的社交媒体链接，得到经过验证的本地媒体文件和 JSON 报告。

## 核心体验

- 视频号：一次授权，后续复用本机元宝登录态，直接解析 CDN 媒体地址。
- MediaCrawler 平台：指定链接、关闭评论、只下载目标媒体，避免无关抓取。
- 下载层：aria2 多连接优先，curl 断点续传兜底。
- 失败可诊断：每次返回稳定错误码、`context_id` 和可复制的下一步命令。

## 本地安装

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" "$SKILL_SKILLS_INSTALL_DIR/lov-media-crawler"
```

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`。长期输出目录、并发数等用户明确偏好可写入 `skills.lov-media-crawler.records`；Cookie、Token 与登录态永不写入 Profile。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

### 视频号链接

首次授权（打开可见 Chrome，登录成功后自动写入系统钥匙串）：

```bash
python3 scripts/authorize_yuanbao.py \
  --test-url 'https://weixin.qq.com/sph/AUlZ10EgtS'
```

下载：

```bash
python3 scripts/media_crawler.py download \
  'https://weixin.qq.com/sph/AUlZ10EgtS' \
  --output-dir ./downloads
```

如果不希望保存授权，也可仅在当前进程设置 `LOV_MEDIA_CRAWLER_YUANBAO_COOKIE`。公共第三方解析默认关闭。

### MediaCrawler 支持的链接

首次准备上游（仅限其许可证允许的非商业学习/研究用途）：

```bash
python3 scripts/media_crawler.py setup-mediacrawler \
  --accept-noncommercial-license
```

随后直接下载目标链接：

```bash
python3 scripts/media_crawler.py download 'https://www.douyin.com/video/…' \
  --output-dir ./downloads
```

### 探测与诊断

```bash
python3 scripts/media_crawler.py probe URL --json
python3 scripts/media_crawler.py doctor --json
```

## 原子组合

[`references/skill-composition.md`](references/skill-composition.md) 记录了与 `lov-media-fetch`、`lov-media-creator`、`lov-publish-wechat-channels` 等能力的交接。外部 Skill 不是运行依赖。

## 安全、权限与许可证

- 只下载用户有权访问和保存的公开内容；不绕过访问控制、DRM、付费或地域限制。
- 视频号登录态只进入环境变量或操作系统凭据存储，不进入 Profile、报告和日志。
- 本 Skill 源码为 MIT；MediaCrawler checkout 保持其独立的 `NON-COMMERCIAL LEARNING LICENSE 1.1`，不得据此用于商业用途或大规模抓取。
- 详细出处与固定版本见 [`references/upstream-and-licenses.md`](references/upstream-and-licenses.md)。

## 质量门

```bash
python3 scripts/media_crawler.py self-test --json
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.9+
- curl
- 可选：aria2、ffprobe、Playwright + Chrome、Git + uv + Node.js

## License

MIT。外部项目和服务遵循各自许可证与条款。
