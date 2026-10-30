# 踩过的坑

每条：现象 → 根因 → 做法。首轮来自 2026-10-28 样片（`2026-10-28-topic-to-short`）。

## 对齐与转写

| 现象 | 根因 | 做法 |
| --- | --- | --- |
| 重读的那一句起点早了 0.45 秒，带进了念错那遍的尾巴；首句前多 0.3 秒静音 | Whisper 逐字时间（DTW）在句首句尾漂移几百毫秒 | `align.py` 在「前一段语音的末字」到「本句首字 + 0.5 s」之间找**最长静音缝**落刀，句尾同理；样片 12 句全部落在真值前 60–70 ms / 后 80–90 ms |
| 重转写 CER 0.122，其实成片一字未吃 | Whisper 把 `initial_prompt` 原样吐进转写（「简体中文」盖住了「提词器、封面」）；7/七、他/它算错字 | 质检转写不带提示词；先统一数字与代词；门禁用「吃字率 ≤ 3%」，CER 只作参考 |
| `uv run --with mlx-whisper` 报 `Using SOCKS proxy, but the 'socksio' package is not installed` | 环境里有 `all_proxy=socks5://…`，huggingface_hub 的 httpx 要 socksio | 加 `--with socksio`；模型已缓存时同时设 `HF_HUB_OFFLINE=1` |
| Profile 规定的云端 ASR（听悟）脚本与配置不在了 | 外部脚本路径会搬家 | `align.py --words` 接任何 ASR 的 `[{w, s, e}]`；通道实际不可用才回退本机 Whisper，并告知专名需人工核对 |

## 画面

| 现象 | 根因 | 做法 |
| --- | --- | --- |
| 分屏上半屏的标题在手机上被状态栏盖住 | 素材面板从 y=0 开始 | `layout.ts SPLIT.brollTop = 100` |
| 全脸镜头的大标注压到字幕 | 两者纵向间距不足 | 标注放胸口（y≈1050），字幕下移到 y≈1330 |
| 横向终端截图在分屏里两侧被裁 | 一律 `cover` | `build.py` 缺省 `fit`：裁切 ≤ 25% 才铺满，否则完整显示；长截图用 `focus` 推近 |
| 终端截图英文长行从单词中间断开 | `word-break: break-all` | `overflow-wrap: break-word` |
| 提词器截图字太小、看不出「正在念的那句」 | 1080 宽视口里字号按 vw 算 | 720 宽 × 3 倍截图，并用 `--press Space` 开播后再截 |
| 封面人像发虚 | 391 px 的形象照被放大约 2.5× | 抠图记录像素尺寸，封面最多放大 1.1×；正式封面用录像里 3 秒封面表情的帧 |

## 工程

| 现象 | 根因 | 做法 |
| --- | --- | --- |
| `pnpm install` 报 `ERR_PNPM_IGNORED_BUILDS`（esbuild） | pnpm 10+ 默认不跑依赖的构建脚本 | 起步工程自带 `pnpm-workspace.yaml` 放行 esbuild |
| `setup_project.py --force` 把本集时间线重置成占位 | 整个 starter 目录覆盖 | 已存在的 `public/data/{timeline,cover}.json` 不覆盖 |
| L01 要用封面图当素材，封面又要先建工程才能渲染 | 先有鸡还是先有蛋 | `build.py --allow-missing` 先出时间线与封面规格 → `remotion still Cover34` → 正式 build |
