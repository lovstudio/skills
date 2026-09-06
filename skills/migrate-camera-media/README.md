# 相机素材迁移

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

将相机存储卡完整转存到 SSD，保留目录和关联文件，并通过 SHA-256 回读确认复制结果。

## 安装

```bash
npx lovstudio skills add migrate-camera-media -g -y
```

## 使用

告诉 Agent 源卡和归档路径，例如：

> 将 /Volumes/CAMERA_CARD 的全部内容转存到 /Volumes/ARCHIVE_SSD/活动/相机卡01，尽快完成并校验，保留源卡。

Skill 会检查磁盘身份和 USB 速率、复制整卡内容、核验备份并输出报告。断线后可继续同一任务；源卡发生变化时会先列出差异。清卡需要明确授权，默认保留原始素材。

## 范围

- macOS 挂载卷；Python 3.9+、xattr。
- 照片与视频抽查另需 Pillow、ffmpeg、ffprobe。
- 包含隐藏文件、空目录、XML、数据库、代理文件及 RSV；保留 RSV 不代表已恢复录像。
- 哈希一致证明复制一致；抽样解码不等于全片检查，也不保证源素材本身无损。
- 不包含损坏素材恢复、远程人工支持或其他操作系统适配。

## 验证

14 项临时目录测试覆盖续传、文件变化、校验失败、错误磁盘、路径越界、受保护文件和 USB 信息解析。生成的 JPEG、短视频及音轨抽查通过，真实转存经验记录在 [案例](references/case.md)。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

完整操作流程见 [SKILL.md](SKILL.md)。
