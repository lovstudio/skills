# 视频素材精整 · Video Prep

![Version](https://img.shields.io/badge/version-0.2.0-CC785C)

把原始课程或活动实录做成明亮、清楚、按内容组织的可剪辑素材库。保留有价值的讲解和演示，剔除已核验的无效区间；原片只读、待复核默认保留。

## 使用

> 对全片做明亮自然增强，并智能分段：去掉无意义的等待，保留有内容的讲解和演示。

> Preprocess and segment this video into enhanced source clips.

提供本地视频和已有参考。Agent 校准短片、建立全片质量索引、读取完整转录、做语义取舍，再渲染所有保留段。输出 MP4、可搜索及筛选待复核片段的 HTML 素材库、JSON 时间码/源映射与实际校验记录。默认不加 BGM、字幕或出版包装。

## 本地安装

在本目录执行，为共享安装入口建立到当前源码的链接，再从宿主相对链接到共享入口；已有目标先核对，不能覆盖。

```bash
ln -s "$PWD" "$HOME/.agents/skills/lov-media-preprocessor"
ln -s ../../.agents/skills/lov-media-preprocessor "$HOME/.codex/skills/lov-media-preprocessor"
```

当前仅本地安装。统一分发安装命令是 `npx skills add lov-media-preprocessor -g -y`；远程渠道尚未发布，不能把该命令当作已上线验收。

## Profile 与依赖

每次读取 [skill.yaml](skill.yaml) 的 user-profile/v1，直接声明的长期偏好通过 scripts/profile_store.py 原子保存；单次素材不写长期记录。详见 [Profile contract](references/user-profile.md)。

Python 3.9+、NumPy、OpenCV、FFmpeg/FFprobe；PyYAML 用于验证。宿主视觉负责内容判断，时间戳转录由宿主供应或通过 whisper-cli 和显式模型文件在本地生成。无固定私有路径、凭据或远程 API 依赖。

Apple Silicon 可选 `--backend mlx`，需要装有 mlx-whisper 的兼容 Python 环境与本地模型目录。分析音轨单独做响度规范；原片和交付原声保持独立。默认关闭长上下文重复提示以减少静音处循环识别，仍需内容审阅。

转录可选 `--vad`（silero-vad），只跳过分析中未检出人声的窗口，不据此删除视频。渲染可选 `--engine metal --codec h264_videotoolbox`（macOS + Swift 编译工具），使用 Core Image 加速同方向的连续色彩处理；原生后端可用 `check_workflow.py --metal` 验证。完整增强版使用 `plan --enhancement-only`，与语义精简版分开保存。

已经完成的同源增强主片可通过 `--prepared-run` 复用，避免重复调色；分段视频会再次编码，音频从原片读取。转录、视觉和听审分别记录实际完成程度；不能直接听审时采用词级时间、波形和画面核对，不确定区间保留。

要继续剪成视频号独立切片，使用 `scripts/creator_handoff.py --run "$RUN" --output "$OUTPUT/creator-handoff.json" --decode` 导出经过哈希、源映射与实际解码校验的交接，并附可点击 MP4 的 Markdown 列表。`lov-media-creator` 接手精剪、字幕、连续混音和包装；画面复用已增强素材，人声继续按原片时间读取。详见 [成片交接契约](references/creator-handoff.md)。

## 命令与门禁

```bash
python3 scripts/media_preprocessor.py --help
python3 scripts/validate_skill.py .
python3 scripts/check_workflow.py
```

源绑定、全覆盖时间线、删除依据、review 保留、尺寸/音轨/时长、哈希和实际解码均需检查。机器校验不能代替语义与视觉审阅。只完成样片时不得写全片完成。

[增强契约](references/enhancement-contract.md) · [分段契约](references/segmentation-contract.md) · [能力组合](references/skill-composition.md) · [真实案例](cases/cases.json)

## 许可与状态

MIT，本地源码免费。模型推理、存储或转录服务可能另行产生费用；不含发布与素材权利授权。workbuddy、skillpay、github、lovstudio 均未发布。
