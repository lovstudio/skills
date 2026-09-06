# lov-video-moments

![Version](https://img.shields.io/badge/version-0.3.0-CC785C)

给定视频，挑出适合发朋友圈的真实现场瞬间，提取最佳帧，统一美化并交付成组照片。适合线下课程、沙龙、工作坊与活动记录。

默认交付约六张照片、整组总览、本地审阅页和可回溯时间码。不会把图片套成海报，不会给没听过的对白编金句，也不会自动发布。

默认使用 `bright-documentary` 明亮自然方向：主体面部清楚、暗部舒展、肤色中性、投影亮部可读。用户认可的美化版锁定为视觉基准；风格认可与文字/人物保真分别记录，详见 [明亮效果基准](references/approved-bright-look.md)。

支持摄影调色：按原片元数据还原 S-Log3 / S-Gamut3.Cine 与 Rec.709，再校准曝光和白平衡，输出 sRGB 照片。用户选择“默认摄影调色”后保存在 Profile，后续在宿主允许范围内直接沿用。多种录制模式分别校准，保留真实人物与屏幕内容。

## 安装

```bash
npx lovstudio skills add video-moments
```

在无交互环境中加 `-y`；全局安装再加 `-g`。

### 本地源码安装

将本目录保存在任意本地源码位置，在共享技能目录中建立 `lov-video-moments` 链接，各宿主入口再相对链接到共享目录。目标已存在时先核对真实指向，不能覆盖其他 Skill。

```bash
mkdir -p "$HOME/.agents/skills" "$HOME/.codex/skills"
ln -s "$PWD" "$HOME/.agents/skills/lov-video-moments"
ln -s ../../.agents/skills/lov-video-moments "$HOME/.codex/skills/lov-video-moments"
```

上述链接命令需在本 Skill 源目录执行。

## 使用

> 从这段课程实录里挑六张适合发朋友圈的现场照片，保留真实人物和课件，色调和大小统一。

> Create shareable photo moments from this event video.

视频文件可带中文和空格。先给宿主 Agent 本地路径；Agent 执行全片粗筛、候选细筛、源帧提取、修图和实际回读。纯短视频剪辑、纯朋友圈配文、已有照片加 Logo 不属于本 Skill。

```bash
python3 scripts/video_moments.py probe "$VIDEO"
python3 scripts/video_moments.py index "$VIDEO" --every 60 --output "$RUN/data/coarse"
python3 scripts/video_moments.py extract "$VIDEO" --at 00:01:05 --output "$RUN/data/originals"
python3 scripts/video_moments.py photographic "$RUN/data/originals/frames.json" \
  --color-mode auto --exposure 0.3 --gamma 1.1 --output "$RUN/data/edited"
python3 scripts/video_moments.py package "$RUN/data/selection.json" --output "$RUN/photos-v0.1"
python3 scripts/video_moments.py verify "$RUN/photos-v0.1"
```

`index` 中断后可用相同参数加 `--resume`，只恢复同一源视频。命令中的时间码为示例，实际时间码由 Agent 查看索引后决定。脚本不自动理解视频内容，也不自带生图或语音识别模型。

`photographic` 的数值是校准起点。色彩未知时先查元数据；只有确认已还原的 SDR 原帧才选 `--color-mode srgb`。成图仍需逐张视觉验收并编写 selection。`package` 每次绑定一个源视频，多源交付先分别验收再合并。具体见 [摄影调色流程](references/photographic-workflow.md) 与 [多源组图契约](references/selection-schema.md#多源组图)。

## Profile

每次读取 [skill.yaml](skill.yaml) 声明的 `user-profile/v1`。当前请求优先；品牌、工作目录与长期偏好来自共享 Profile。用户直接声明的长期偏好用 `scripts/profile_store.py` 原子保存，一次性素材不写入长期记录。详见 [Profile contract](references/user-profile.md)。

## 依赖与验收

- Python 3.9+、Pillow 10.1+、FFmpeg、FFprobe；摄影调色需要 NumPy，校验需要 PyYAML。
- 宿主视觉判断；摄影调色本地执行，生成式编辑按宿主规则选择。知识金句需要有时间戳的转录/音频证据。
- `lov-branding-consistency` 只约束新增读者可见文案。
- 真实照片与课件保真、整组差异、尺寸一致、哈希一致均需验收；脚本通过不能代替视觉判断。

```bash
python3 scripts/validate_skill.py .
python3 scripts/check_workflow.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

详见 [筛选规则](references/selection-policy.md)、[美化契约](references/image-contract.md)、[数据格式](references/selection-schema.md)、[能力组合](references/skill-composition.md) 和 [Skill Card](skill-card.md)。

## 许可与状态

MIT。源代码免费，0 Credits；宿主推理、生图或转录服务可能另行计费，当前没有可验证的总成本报价。视频与人物照片不因使用本 Skill 而获得公开传播许可。照片的远程发布、上传与商业渠道不在本地处理流程中。
