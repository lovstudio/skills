# media-crawler · WorkBuddy + Kimi K2.7

- 结果：部分通过
- 日期：2026-11-06
- 环境：macOS 26.6 arm64 · WorkBuddy 内置 CodeBuddy CLI 2.115.0 · kimi-k2.7
- Skill 版本：0.3.1（567aa3f）
- 入口：WorkBuddy 自带的命令行，不是图形界面；图形界面没有单独测
- 隔离：清空环境变量后运行，用 macOS 沙箱禁止读取密钥和个人目录，只给合成素材，配置目录为空，模拟一个新用户
- 运行：47 轮，1.4 分钟，输入 370309 tokens（缓存命中 347392），输出 2215 tokens

## 范围

点名 Skill 后走完直链路线：10 MB 文件下载、校验并写出 JSON 报告，状态 verified，完整解码。

## 差距与没覆盖的部分

只测了直链下载。第一次没有点名时，它直接用 curl 下载，没走 Skill，所以没有校验报告。视频号和其他平台没测。

## 给 Agent 的原话

```text
$lov-media-crawler 下载这个视频链接到当前目录的 downloads/：https://raw.githubusercontent.com/lovstudio/skills/main/cases/assets/koubo-short-topic-to-short-2026-10/sample.mp4
必须按这个 Skill 的流程走，并写 JSON 报告。这是一次无人值守运行：不要向我提问。完成后告诉我文件路径、大小、耗时和校验结果。
```

## 独立验收

下面的检查不看模型自述，由验收脚本直接读产物。

- 通过：Skill 确实被调用（工具调用或读取 SKILL.md）
- 通过：Agent 正常结束
- 通过：有下载文件
- 通过：完整解码，有视频轨和音轨
- 通过：写出了 Skill 的 JSON 报告
- 通过：报告状态正常（verified）
- 通过：用了 Skill 自带的脚本

## 其他观察

同样的请求不点名 Skill 时，模型只用一条 curl 就下完了，没有走 Skill，也没有校验报告。那次不算证据。
