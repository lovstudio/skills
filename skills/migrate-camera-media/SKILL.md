---
name: lov-migrate-camera-media
description: 将相机或存储卡素材完整迁移到 SSD，诊断 USB 限速，保留整卡目录，支持断点续传、SHA-256 回读校验、素材抽查和授权清卡。用于相机转存、Sony 备份、换线续传及备份后清卡；目前支持 macOS 挂载卷。
license: MIT
compatibility: "macOS mounted camera cards; Python 3.9+ and xattr. Optional media sampling requires Pillow, ffmpeg and ffprobe."
depends_on:
  - lov-branding-consistency
metadata:
  author: LovStudio
  version: "0.1.0"
  tags:
    - camera-media
    - backup
    - checksum
    - macos
---

# 相机素材迁移

版本：0.1.0。按“查设备 → 查链路 → 整卡复制 → 全量核验 → 素材抽查 → 按授权清卡”执行。使用现有会话中的源路径、目标路径、风险选择和授权；不要反复询问已确认的事项。

## Triggers

### Activate when

- 将相机或存储卡里的素材转存到 SSD，并校验是否完整。
- 排查 Sony 传输过慢、换线后续传或备份完成后的清卡流程。

### Do not activate when

- 只需要视频剪辑、字幕、照片调色或损坏录像恢复；本 Skill 不负责这些结果。
- 设备未挂载为 macOS 文件系统卷时，先解决连接方式，不直接执行迁移脚本。

## 先界定结果与授权

- 回答“怎么做、能不能”时先解释和只读检查。明确的迁移请求执行复制与校验；跨盘移动同样需要复制，不提供速度优势。
- 默认保留源卡。只有上下文已明确授权删除这张卡时，才进入清卡步骤；单独一句技术可行性问句不足以替代删除授权。已有明确授权无需再次确认。
- 把 3-2-1、多份独立备份及未恢复素材作为建议和状态说明。用户已了解并接受当前备份安排后，不反复以同一建议阻止已授权清卡。
- 不继承此 Skill 的真实案例授权。每次确认实际目标；不自动格式化、抹整盘、删除其他卡或清理备份。

## 1. 只读检查与测速

先读取源卷及目标卷身份、格式、可用空间。将每张卡归档到独立目录，将清单与日志放在相邻报告目录，二者均在源卡之外。

```bash
python3 scripts/camera_media.py inspect --source '/Volumes/CAMERA_CARD' --usb
diskutil info -plist '/Volumes/ARCHIVE_SSD'
```

从实际输出取得 Volume UUID，不能把可变的 `disk4` 等设备编号当永久身份。统计所有文件的逻辑字节数，包含隐藏文件、空目录、XML、数据库、代理文件及 RSV；分开统计主照片和视频缩略图。不要读取或归档相机额外挂载的软件安装卷，例如 `PMHOME`。

在大量复制前核对协商速率。若实际读速约 1 MB/s，优先查 `UsbLinkSpeed`；12 Mb/s 的理论上限仅 1.5 MB/s。先排除线、接口和读卡器限制，不能直接用 SSD 宣传速度估算。请求换线前安全停止当前进程并确认退出，保留部分文件；重新连接后复核 UUID 和清单。

Sony FX3A 与 macOS/exFAT 的细节按需读取 [平台与速度](references/platform.md)。其他相机能力须查其官方文档，不从 FX3A 推广。

## 2. 复制并全量校验

使用 Python 3.9+；转存脚本需要 `xattr` 模块。先用 `python3 -c 'import xattr'` 检查可用运行环境，复用已安装环境。缺依赖先解决，不要启动百 GB 复制后才发现接口不可用。

以下路径及 UUID 均为占位示例，替换为刚读取的实际值。目标卡目录和报告目录应尚不存在；断点续传时复用同一组参数。

```bash
caffeinate -i -m python3 scripts/camera_media.py transfer \
  --source '/Volumes/CAMERA_CARD' \
  --destination '/Volumes/ARCHIVE_SSD/活动/原始素材/相机-卡01' \
  --report '/Volumes/ARCHIVE_SSD/活动/转存校验/相机-卡01' \
  --source-uuid 'SOURCE_UUID' --destination-uuid 'DESTINATION_UUID'
```

让脚本顺序读卡，并行写 SSD 和计算 SHA-256，采用有限内存缓冲。它保留 `.partial`，恢复时逐字节比较已复制前缀，并重算源哈希状态；不会盲目追加。保留文件名、目录、时间戳和扩展属性；不把相机的保护标志复制到工作副本。

完成复制后，重新打开目标文件回读计算哈希，验证所有源文件路径、大小、哈希及目录集合。保存 `manifest.json`、`checksums.sha256`、`status.json`。校验成功状态是 `verified`；遇到异常保留错误和中间产物，不显示完成。

`verify` 子命令接受同一组五个路径/身份参数，可在源卡尚存时重新核验。已清卡后不要运行依赖源快照的验证；使用归档清单从目标卡目录执行 `shasum -a 256 -c '/绝对路径/checksums.sha256'` 检查备份本身。

## 3. 处理断连与源清单变化

使用 `inspect --source ... --compare '/报告目录/manifest.json'` 检查新增、缺少和变更文件。失败时不要删锁、关闭校验或直接覆写旧清单。

- 源未变化：使用相同参数续传；已有完整文件先校验，部分文件先核对前缀。
- 源变化：保留旧清单、旧报告和未完成副本，输出差异。只询问影响结果的问题，例如“这些片段是否另行转移”。用新的卡目录和报告目录备份当前内容，不把较小的新快照说成原始整卡已全部备份。
- 用户提供另一目的地：核对具体文件及 XML、原始大小，抽查可播放性。有旧源哈希时比对哈希；没有时只能报告“数量/大小一致、抽查通过”，不能声称逐字节一致。记录已确认的去向和验证范围。

不要因新快照变化推断数据已损坏或被用户删除。不要擅自进行数据恢复。

## 4. 素材抽查与交付

安装环境中存在 Pillow、ffmpeg、ffprobe 时运行：

```bash
python3 scripts/check_media.py --report '/Volumes/ARCHIVE_SSD/活动/转存校验/相机-卡01'
```

只选择清单中的真实文件，避免把 macOS 的 `._*.MP4`、`._*.JPG` 当素材。解码照片全部 MPO 帧；对每个受支持视频检查首、中、尾画面和一段音轨。记录不支持的格式及未尝试恢复的 RSV。抽样解码不是全片逐帧验证，也不是人工视听审查；哈希一致不证明源录像本来可播放。

按宿主机制等待长任务，至少每 60 秒提供有意义的进度。分开报告复制速度、校验速度和完成状态。最终回读清单和结果，简要交付：路径、文件数、字节数、耗时、核验范围、异常去向、RSV 状态、源卡是否保留、第二份备份是否存在。按宿主要求将用户可见报告复制到交付目录。

## 5. 经授权清卡

先读取 [清卡规则](references/cleanup.md)。优先推荐相机内格式化。用户明确选择电脑端清空并已接受备份安排时，可以执行电脑端清理；把厂商建议说明一次，不当作不能执行的权限限制。

使用 `cleanup` 和转存相同的五个参数先生成只读计划；默认不会删除。确认计划中的卡 UUID、源文件、已验证副本、受保护文件及拟释放字节。

授权已明确且计划符合范围后，追加 `--apply --confirm-source-uuid 'SOURCE_UUID'` 执行。此参数只是防误触开关，不提供用户授权。脚本仅删除原清单中仍未变化且备份匹配的文件，跳过受保护文件，不清除 `uchg`，不 `sudo`，不改分区或文件系统。

清理后读取 `cleanup.json`、剩余文件及实际可用空间，更新报告中的源卡状态。`cleared_with_retained_files` 不等于完全空卡；逐项说明保留内容和大小。相机仍可能需要机内格式化来初始化数据库。

## 维护

脚本变更后运行 `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`。测试只使用临时目录和注入的卷身份，禁止用真实卡测试删除逻辑。实战中的发现与证据边界见 [案例](references/case.md)。
