# 视频转 PPT · Video2PPT

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

把会议演讲、网课或录屏视频还原成去重后的幻灯片：一份 PPTX、一份 PDF、一个 PNG 帧目录，
每页备注写着它在视频里的时间点。算法移植自
[video2ppt 桌面应用](https://github.com/MarkShawn2020/video2ppt)，并针对“幻灯片嵌在讲者画面里、
底部有字幕、换页带叠化”的演讲视频补了裁剪、稳定帧选择和复核增删。

## 本地安装

```bash
npx lovstudio skills add video2ppt -g -y
```

或在本仓库根目录手动链接：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${LOVSTUDIO_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" "$LOVSTUDIO_SKILLS_INSTALL_DIR/lov-video2ppt"
```

运行依赖：

```bash
brew install ffmpeg            # 或 apt install ffmpeg
python3 -m pip install pillow python-pptx
```

## 使用

对 Agent 说：

- “把这个演讲视频转成 PPT：~/Downloads/talk.mp4”
- “https://weixin.qq.com/sph/... 这个视频号，把里面的幻灯片扒下来”
- “Extract the slides from this lecture as a PDF”

直接调用脚本：

```bash
# 演讲视频：裁出幻灯片区域，用像素比较
python3 scripts/video2ppt.py extract talk.mp4 out/ \
  --method pixel --similarity 0.985 --settle 3 --min-duration 2 \
  --crop 981:551:288:11 --name talk-slides

# 看完 out/contact-sheet.jpg 后删页、补页并重建
python3 scripts/video2ppt.py pack out/ --drop 6,16 --add 00:08:50

# 与桌面版完全一致的默认行为
python3 scripts/video2ppt.py extract screen.mp4 out2/
```

输出目录：`frames/`、`<name>.pptx`、`<name>.pdf`、`contact-sheet.jpg`、`manifest.json`；
复核后删掉的帧在 `dropped/`。参数与实测对比见 [references/tuning.md](references/tuning.md)。

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`，读取用户语言、工作区，以及
`skills.lov-video2ppt.records` 下的 `output_dir`、`method`、`similarity`、`fps`。
用户直接说出的长期偏好由 `scripts/profile_store.py` 写回 Profile。详见
[references/user-profile.md](references/user-profile.md)。

## 原子组合

链接下载交给 `lov-media-crawler`（可选上游），本 Skill 只负责“本地视频 → 已复核的幻灯片包”。
详见 [references/skill-composition.md](references/skill-composition.md)。

## 可信度卡与用户案例

- [`skill-card.yaml`](skill-card.yaml) / [`skill-card.md`](skill-card.md)
- [`cases/cases.json`](cases/cases.json)：13 分钟视频号演讲 → 39 页 PPTX
- [`pricing-card.yaml`](pricing-card.yaml)：免费

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 tests/test_video2ppt.py
```

## 依赖

- Python 3.9+、Pillow、ffmpeg/ffprobe
- python-pptx（PPTX 输出）
- PyYAML（仅校验脚本）

## License

MIT
