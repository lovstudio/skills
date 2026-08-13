---
name: lov-media-crawler
description: >
  给定视频号、小红书、抖音、快手、B站、微博、贴吧或知乎链接，复用登录态解析并高速下载媒体，返回可验证文件与诊断报告；适用于“下载这个视频链接”、"download this media link"。
license: MIT
metadata:
  author: contributors
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  tags:
    - media-crawler
    - video-download
    - wechat-channels
    - mediacrawler
    - resumable-download
  compatibility: "Portable Agent Skills format; Python 3.9+, curl; optional aria2, uv, Git, Playwright, Chrome, and MediaCrawler."
  dependencies:
    - python
    - curl
---

# lov-media-crawler — 链接到本地媒体文件

用户给一个公开且有权保存的社交媒体链接，本 Skill 负责识别平台、复用已有授权、下载原始媒体，并交付文件与 JSON 验证报告。优先减少等待、重复登录和中间选择。

## Triggers

### Activate when

- 用户说“下载这个视频链接”“把这个视频号保存下来”“抓取这条抖音/小红书/B站内容”。
- 用户直接给出 `weixin.qq.com/sph/...`、抖音、小红书、快手、B站、微博、贴吧或知乎内容链接并要求本地文件。
- User asks “help me download this media link”, “save this WeChat Channels video”, or “fetch this post and its media”.

### Do not activate when

- 用户只给片名并要求搜索电影、比较版本或下载种子；交给 `lov-media-fetch`。
- 用户已有素材并要求剪辑、混音、转码或制作发布成片；交给 `lov-media-creator`。
- 用户要批量抓取账号、评论或用户资料，或无权访问的私密、付费、地域受限内容；本 Skill 只处理单条或明确列出的少量公开链接，不绕过访问控制。

## User Profile (cross-session)

每次运行读取 `skill.yaml` 声明的 `user-profile/v1`：用户语言、工作区输出位置、共享偏好，以及 `skills.lov-media-crawler` 下的 Skill 记录。解析顺序为当前请求、项目上下文、Skill 记录、共享偏好、用户 Profile、安全默认值。

用户明确声明长期输出目录、下载并发数或媒体格式偏好时，使用 `scripts/profile_store.py record --confirm` 写回 Profile，并报告保存路径。Cookie、Token、代理密码和浏览器登录态永不写入 Profile；视频号元宝授权仅进入操作系统凭据存储或当前进程环境。完整契约见 [`references/user-profile.md`](references/user-profile.md)。

## Skill Group Composition

运行前阅读 [`references/skill-composition.md`](references/skill-composition.md)。本 Skill 独立拥有“已知链接 → 已验证本地媒体”的验收；相邻 Skill 只通过链接或本地文件交接，不是隐藏依赖。

## Workflow (MANDATORY)

**必须按以下顺序执行。**

### Step 0: 解析根目录、Profile 与运行时

- 使用 `SKILL_DIR`，否则从当前 Skill 上下文推断安装目录。
- 验证 `scripts/media_crawler.py`、`scripts/authorize_yuanbao.py`、`references/platform-matrix.md`、`references/upstream-and-licenses.md` 存在。
- 运行 `python3 "$SKILL_DIR/scripts/media_crawler.py" doctor --json`，只安装当前链接确实需要的可选依赖。
- 默认输出到用户显式目录、Profile 的 `records.output_dir`、项目输出目录，最后才是当前目录下 `downloads/`。不得覆盖已有成品。

手工运行时：

```bash
export SKILL_DIR="/path/to/lov-media-crawler"
```

### Step 1: 核对链接、权限与目标

1. 从请求中提取唯一链接；多链接时逐个建立独立 job，不混写目录。
2. 只处理用户有权访问与保存的内容。不要绕过登录、付费、私密、地域或 DRM 控制。
3. 用户未指定格式时保留源媒体；不默认转码。用户未指定文件名时使用作者/标题生成安全文件名。
4. 先探测再下载，探测阶段不得创建伪成功文件：

```bash
python3 "$SKILL_DIR/scripts/media_crawler.py" probe URL --json
```

### Step 2: 选择最短可用路径

按 [`references/platform-matrix.md`](references/platform-matrix.md) 路由：

- **微信视频号**：先读系统凭据或 `LOV_MEDIA_CRAWLER_YUANBAO_COOKIE`，通过腾讯元宝解析分享链接，再由微信视频号接口取得 CDN 地址。缺少授权时运行一次可见浏览器授权：

  ```bash
  python3 "$SKILL_DIR/scripts/authorize_yuanbao.py" --test-url URL
  ```

  公共 Worker 默认禁用。只有用户明确接受把公开分享链接发送给该服务时，才使用 `--allow-public-resolver`；优先使用用户自建的 `--worker-url`。

- **MediaCrawler 支持的平台**：使用本机已有 checkout；没有时，先告知上游的非商业学习许可证，再执行：

  ```bash
  python3 "$SKILL_DIR/scripts/media_crawler.py" setup-mediacrawler \
    --accept-noncommercial-license
  ```

  适配器固定已验证 commit、关闭评论抓取、只抓指定内容、启用媒体下载，并从 9333 起选择可用调试端口启动独立 Chrome Profile，不连接 9222 或其他已有调试实例。

- **直接媒体 URL**：跳过浏览器与爬虫，直接进入传输层。

不要把 MediaCrawler 不支持视频号的事实隐藏起来；视频号适配器是本 Skill 的独立扩展路径。

### Step 3: 下载与即时反馈

```bash
python3 "$SKILL_DIR/scripts/media_crawler.py" download URL \
  --output-dir OUTPUT_DIR \
  --connections 8 \
  --json-report OUTPUT_DIR/result.json
```

- 优先使用 aria2 的多连接、断点续传；没有 aria2 时使用 curl 的续传、重试和进度条。
- 首次可见反馈应在链接解析后立即出现；长下载期间至少每分钟报告一次进度、当前速率和 ETA。
- 失败保留可继续的 `.part` 文件；重试同一 URL 与输出路径，不创建第二份完整 payload。
- 文件名冲突时生成稳定后缀，除非用户明确允许覆盖。

### Step 4: 验证成品

完成条件不是 HTTP 200，而是：

1. 文件存在且非零，响应不是 HTML/JSON 错误页。
2. MP4/MOV 检查 `ftyp`，WebM/MKV 检查 EBML，图片检查 PNG/JPEG/GIF/WebP 魔数；视频可用时再用 `ffprobe` 验证流、时长、编码与分辨率。
3. 实际字节数与 `Content-Length` 一致（服务器提供时）。
4. JSON 报告包含 `status`、`platform`、`source_url`、`output_path`、`bytes`、`elapsed_seconds`、`average_mbps`、`verification` 和 `context_id`。

视频号只能取得标题/封面但没有视频流时，状态必须是 `authorization_required` 或 `resolver_failed`，不得写成 downloaded。

### Step 5: 报告结果

首句给出成功/失败和本地文件路径。成功时补充大小、耗时、平均速度、平台和验证结果；失败时给出错误码、`context_id`、缺失条件和一条可直接复制的下一步命令。区分：

- `resolved`：已拿到元数据或媒体 URL；
- `downloaded`：payload 已落盘；
- `verified`：容器/流与大小检查通过。

## Dependencies

- 必需：Python 3.9+、curl。
- 推荐：aria2（多连接与稳定续传）、ffprobe（媒体验证）。
- 视频号一次性授权：Playwright Python 包与 Chrome；凭据默认存 macOS Keychain。
- MediaCrawler 路径：Git、uv、Node.js、Chrome，以及上游自身依赖；其代码与使用受上游非商业学习许可证约束。

完整平台边界见 [`references/platform-matrix.md`](references/platform-matrix.md)，上游与许可证见 [`references/upstream-and-licenses.md`](references/upstream-and-licenses.md)，故障码见 [`references/troubleshooting.md`](references/troubleshooting.md)。
