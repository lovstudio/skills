# sgc-media-fetch

![Version](https://img.shields.io/badge/version-0.2.0-CC785C)

一键完成长视频的检索、版本选择、磁盘预检、多源测速下载、可恢复续传、慢源切换和文件验收。

## 本地安装

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" \
  "$SKILL_SKILLS_INSTALL_DIR/sgc-media-fetch"
```

安装链接必须解析到当前源码目录；打包文件不等于本地安装。

## 用户配置

默认下载到 `$HOME/Downloads/Media`。首次运行先查看解析结果：

```bash
python3 scripts/media_config.py show
```

确认后写入共享配置：

```bash
python3 scripts/media_config.py init --write
```

显式请求和环境变量始终覆盖配置。qBittorrent 密码只通过
`QBITTORRENT_PASSWORD` 或系统凭据提供。

## 使用

- “帮我找并下载《影片名》的导演剪辑版，优先中英字幕，体积控制在 20GB 内。”
- “Find and download the best compact 4K release of TITLE, then verify the English and Chinese subtitles.”
- “这个 Magnet 帮我下载；先确认磁盘够用，太慢就自动换另一个版本。”

自然语言调用默认运行 `full` 流水线。已有链接使用 `download-known`；本地文件验收使用 `verify`。
qBittorrent 负责集成搜索与首轮测速，aria2 负责同一 Magnet/Torrent 的续传兜底。
每次切换都写入 transport trace，不把客户端进度当作最终完成证据。

## qBittorrent 连接

首次调用会安装缺失的稳定版依赖，并将 WebUI 限定在本机回环地址。已有兼容
客户端时直接复用。密码保存在系统凭据中，再通过环境变量注入当前任务。

```bash
export QBITTORRENT_URL="http://127.0.0.1:8080"
export QBITTORRENT_USERNAME="admin"
export QBITTORRENT_PASSWORD="从安全凭据读取"
```

依次可运行：

```bash
python3 scripts/qbittorrent_search.py --query "TITLE YEAR" --output candidates.json
python3 scripts/rank_candidates.py --input candidates.json --output decision.json
python3 scripts/storage_preflight.py --decision decision.json
python3 scripts/qbittorrent_acquire.py --decision decision.json --wait-complete --result acquisition.json
python3 scripts/aria2_acquire.py \
  --input INPUT --job-id JOB_ID --output-dir "$HOME/Downloads/Media" \
  --result aria2-acquisition.json --watch --no-proxy
python3 scripts/verify_media.py --path "$HOME/Downloads/Media" --output verification.json
```

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 scripts/media_config.py show --json
python3 scripts/rank_candidates.py \
  --input assets/example-candidates.json \
  --output /tmp/media-fetch-decision.json
python3 scripts/storage_preflight.py \
  --decision /tmp/media-fetch-decision.json \
  --output-dir /tmp
python3 scripts/qbittorrent_acquire.py \
  --decision /tmp/media-fetch-decision.json \
  --dry-run --result /tmp/media-fetch-acquisition.json
```

## 依赖

- Python 3.9+
- PyYAML（Skill 源码校验）
- qBittorrent 5.x WebUI（搜索、测速和下载）
- FFmpeg / `ffprobe`（媒体验收）
- 可选：Rats Search（独立 DHT 检索）
- 可选：aria2 1.36+（qBittorrent 慢源时的续传后端）

## 字幕分支

默认验收 `zh-Hans` 与 `en`。如果成片只有英文字幕，先匹配同一发行版本的外置
SRT，再交给 `sgc-subtitle-freedom-skill` 做时间轴、UTF-8 和 SRT 保真处理。该
Skill 的英文学习提示、人物卡和 ASS 样式均需要明确开启；Media Fetch 不会把它们
作为简中字幕输出。

## 用户案例

《指环王》三部曲的实际任务验证了这条链路：qBittorrent 搜索并测速后，主候选在
首轮实测偏慢，aria2 使用同一信息哈希、DHT/PeX/LSD 与 Tracker 续传，最终得到
3 个可读的 1080p HEVC 文件。下载报告为 `complete`，媒体验收为
`passed_with_warnings`，唯一开放项是原发行文件未嵌入 `zh-Hans`，因此报告继续
保留字幕缺口而不是虚报“双语完成”。完整脱敏证据位于 `cases/evidence/`。

## License

MIT
