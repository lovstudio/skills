# media-preprocessor · WorkBuddy + DeepSeek V4 Pro

- 结果：通过
- 日期：2026-11-06
- 环境：macOS 26.6 arm64 · WorkBuddy 内置 CodeBuddy CLI 2.115.0 · deepseek-v4-pro
- Skill 版本：0.2.0（c1cde51）
- 入口：WorkBuddy 自带的命令行，不是图形界面；图形界面没有单独测
- 隔离：清空环境变量后运行，用 macOS 沙箱禁止读取密钥和个人目录，只给合成素材，配置目录为空，模拟一个新用户
- 运行：255 轮，20.4 分钟，输入 5598293 tokens（缓存命中 5409984），输出 37735 tokens

## 范围

50 秒合成课程录像全片提亮，本机转写后按内容分段，保留 34 秒、剔除 16 秒静音，每处取舍有依据。Skill 的 verify --decode 通过，读对 3/3 个画面口令。

## 差距与没覆盖的部分

只测了 50 秒合成素材，长片的性能和断点续跑没测。它把 whisper 在静音段幻听出的文字识别了出来，没有写进取舍依据。

## 给 Agent 的原话

```text
当前目录的 course-zh.mp4 是一段线下课程录像，整体偏暗。帮我全片提亮，再按内容智能分段，保留有用内容，输出素材库和源时间码。
本机没有联网转写需求，可以用本机 whisper（Hugging Face 缓存在 <本机路径> mlx-community/whisper-large-v3-turbo）。
这是一次无人值守运行：不要向我提问，按默认决策做完；完成后告诉我输出路径和校验结果。另外，请在最后告诉我录像里每页幻灯片右下角写的口令分别是什么。
```

## 素材

- `course-zh.mp4`（sha256 9c37fb971acf71de）：50 秒偏暗的合成课程录像：幻灯片和人像交替，幻灯片角落有随机口令

## 独立验收

下面的检查不看模型自述，由验收脚本直接读产物。

- 通过：Skill 确实被调用（工具调用或读取 SKILL.md）
- 通过：Agent 正常结束
- 通过：原文件没动：course-zh.mp4
- 通过：有分段视频（7）
- 通过：有取舍计划（['run/enhanced-full/plan.json', 'run/videos/plan.json']）
- 通过：有源时间码清单（['run/enhanced-full/manifest.json', 'run/videos/manifest.json']）
- 通过：有素材库页面（['run/enhanced-full/gallery.html', 'run/videos/gallery.html']）
- 通过：主要产物能完整解码
- 通过：读对了画面里埋的随机口令（说明确实看了画面）（3/3）
- 通过：Skill 自带的 verify --decode 通过
- 通过：Skill 自带的 verify --decode 通过
- 通过：Skill 自带的 verify --decode 通过

实测值：`{"luma_src_person_scene": 36.9, "luma_out_first": 187.7, "canaries_read": "3/3"}`

## 其他观察

它发现了本机 FFmpeg 的 colorbalance 在暗部会出色块，改成了纯曲线提亮，并把 whisper 在静音段幻听出的文字排除在取舍依据之外。
