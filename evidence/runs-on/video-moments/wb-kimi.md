# video-moments · WorkBuddy + Kimi K2.7

- 结果：通过
- 日期：2026-11-06
- 环境：macOS 26.6 arm64 · WorkBuddy 内置 CodeBuddy CLI 2.115.0 · kimi-k2.7
- Skill 版本：0.3.1（977e06e）
- 入口：WorkBuddy 自带的命令行，不是图形界面；图形界面没有单独测
- 隔离：清空环境变量后运行，用 macOS 沙箱禁止读取密钥和个人目录，只给合成素材，配置目录为空，模拟一个新用户
- 运行：169 轮，12.4 分钟，输入 2499436 tokens（缓存命中 2410029），输出 13275 tokens

## 范围

50 秒合成课程录像挑出 3 张图，摄影调色后打包。Skill 的 verify 通过，读对 3/3 个画面口令。

## 差距与没覆盖的部分

合成素材只能验证流程，修图审美没有和 Claude 对比。

## 给 Agent 的原话

```text
从当前目录的 course-zh.mp4 里挑 3 张适合发朋友圈的照片，明亮自然地美化，统一组图。用摄影调色，不要 AI 重绘。
这是一次无人值守运行：不要向我提问，按默认决策做完；完成后告诉我输出路径、每张的时间码和你做过的校验。另外，请告诉我你在录像幻灯片右下角看到的口令有哪些。
```

## 素材

- `course-zh.mp4`（sha256 9c37fb971acf71de）：50 秒偏暗的合成课程录像：幻灯片和人像交替，幻灯片角落有随机口令

## 独立验收

下面的检查不看模型自述，由验收脚本直接读产物。

- 通过：Skill 确实被调用（工具调用或读取 SKILL.md）
- 通过：Agent 正常结束
- 通过：原文件没动：course-zh.mp4
- 通过：有打包好的图片（['video-moments-run/photos-v0.1/images/01.jpg', 'video-moments-run/photos-v0.1/images/03.jpg', 'video-moments-run/photos）
- 通过：图片数量符合要求（3 张）（3）
- 通过：有总览图、审阅页和清单
- 通过：读对了画面里埋的随机口令（3/3）
- 通过：Skill 自带的 verify 通过

实测值：`{"canaries_read": "3/3"}`
