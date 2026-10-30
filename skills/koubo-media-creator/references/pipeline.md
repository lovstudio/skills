# 流水线：命令、产物与门禁

`S=$SKILL_DIR/scripts`，`EP` = 集目录，`$PY` = 装好 numpy、pillow、mlx-whisper、opencc-python-reimplemented、jieba 的 Python
（或 `uv run -q --python 3.12 --with … python -I`）。所有命令在 `EP` 下运行。

## 目录

```text
EP/
├── brand/          作者头像、形象照、浅色官方 Logo（从品牌资产真源复制）
├── work/           script.json、takes.json、asr/ 缓存、remotion/ 工程
├── broll/          上屏素材（截图、录屏、数据卡 PNG、封面抠图）
├── broll-src/      数据卡、对比卡的 HTML 源
├── recording/      作者原片（只读）；样片的 tts-take.wav
├── music/          配乐候选与元数据
├── deliverables/   teleprompter.html、script.md、shotlist.md；<版本>/ 成片与封面
├── qc/             门禁报告、联系表、缩略图
└── ledger/         costs.jsonl（每次付费调用一行）
```

## 阶段

| # | 阶段 | 命令 | 产物 | 门禁 |
| --- | --- | --- | --- | --- |
| 1 | 脚本 | 写 `work/script.json` → `python3 $S/check_script.py work/script.json --json qc/script-check.json` | 过门禁的脚本 | 0 ERROR |
| 2 | 证据 | `python3 $S/capture.py url URL --out broll/x.png` · `capture.py term out.txt --out broll/y.png` · `capture.py script work/script.json` | `broll/*` | `check_script.py --strict` 0 ERROR |
| 3 | 录制包 | `python3 $S/teleprompter.py work/script.json --out deliverables` | 提词器、脚本稿、素材清单 | 素材清单无「缺」或已安排补拍 |
| 4 | 样片（可选） | `python3 $S/tts.py work/script.json --out recording/tts-take.wav --dry-run`，再去掉 `--dry-run` 加 `--ledger ledger/costs.jsonl` | 占位配音 | 先报字数与单价 |
| 5 | 对齐 | `$PY $S/align.py work/script.json recording/<原片> --out work/takes.json [--words asr.json]` | 每句选中的一遍与切点 | `review` 为空或逐条确认 |
| 6 | 工程 | `python3 $S/setup_project.py EP`（首次；模板更新时 `--force`，不动 `public/data`） | `work/remotion` | `pnpm check` 通过 |
| 7 | 构建 | `$PY $S/build.py work/script.json work/takes.json --recording recording/<原片> --public work/remotion/public --logo brand/logo-white.png [--face-y 0.33]`；样片加 `--still brand/portrait.jpg --placeholder --animatic` | 连续人像/人声中间轨、`timeline.json`、`cover.json` | 中间轨帧数 = 时间线（脚本自检） |
| 8 | 封面人像 | `swiftc -O $SKILL_DIR/assets/tools/cutout.swift -o work/bin/cutout`；`ffmpeg -ss 1.2 -i recording/<原片> -frames:v 1 broll/pose.jpg`；`work/bin/cutout broll/pose.jpg broll/cover-cutout.png` | 透明底人像 | 头发边缘看过；放大不超过 1.1× |
| 9 | 配乐 | `python3 $S/gen_bgm.py --name a --prompt "…" --out music/bed-a --ledger ledger/costs.jsonl` → `python3 $S/mix.py --public work/remotion/public --bgm music/bed-a.mp3` | `public/audio/mix.m4a` | −16 ±1 LUFS-I、≤ −1 dBTP |
| 10 | 成片 | `$PY $S/finish.py EP --name <命名规则> --version v0.x` | 成片、3:4 与 16:9 封面、`qc/report-<版本>.json`、联系表、缩略图 | `ok: true` 且联系表与缩略图看过 |

## 样片与成片的区别

| | 样片（animatic） | 成片 |
| --- | --- | --- |
| 声音 | Seed-TTS 占位配音 | 作者原声 |
| 出镜 | 形象照按原尺寸放在占位框 | 作者竖拍画面 |
| 角标 | 画面底部「样片 · 配音与出镜为占位」 | 无 |
| 用途 | 预审节奏、镜头、包装、封面 | 审片、发布 |

## 改一处要重跑什么

- 改台词 → 1、3；已录过的句子要作者补录这一句，再 5、7、9、10。
- 改镜头、红框、标签、封面字 → 7、10（不必重录、不必重新对齐）。
- 换配乐 → 9、10。
- 改模板（`assets/starter`）→ 6（`--force`）、10。
