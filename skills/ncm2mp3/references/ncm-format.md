# NCM 文件格式与故障对照

本文件在需要解释失败原因、判断新变体或修改解析逻辑时读取。所有多字节整数为
小端序。

## 布局

| 字段 | 大小 | 说明 |
| --- | --- | --- |
| Magic | 8 B | ASCII `CTENFDAM` |
| Gap | 2 B | 跳过 |
| `key_len` | u32 | 后面 RC4 密钥块长度 |
| 密钥块 | `key_len` | 每字节 XOR `0x64` → AES-128-ECB（`hzHRAmso5kInbaxW`）→ 去 PKCS#7 → 去前缀 `neteasecloudmusic` |
| `meta_len` | u32 | 可为 0 |
| 元数据块 | `meta_len` | 每字节 XOR `0x63` → 去前缀 `163 key(Don't modify):` → Base64 → AES-128-ECB（`#14ljk_!\]&0U<'(`）→ 去 PKCS#7 → `music:` 或 `dj:` + JSON |
| CRC32 | 4 B | 不校验 |
| 封面版本 | 1 B | 跳过 |
| `cover_frame_len` | u32 | 整个封面帧占用的字节数 |
| `image_len` | u32 | 帧内实际图片字节数，可为 0 |
| 图片 | `image_len` | 明文 JPEG/PNG |
| 填充 | `cover_frame_len - image_len` | 必须跳过，音频从这里之后开始 |
| 音频 | 到文件尾 | 按偏移寻址的 RC4 变体流密钥 |

`dj:` 元数据的歌曲信息在 `mainMusic` 字段里。

## 为什么其他实现会输出噪声

`ncmdump-py 1.1.6` 与 `Johnserf-Seed/ncm2mp3 0.3.1` 把 CRC 之后的 5 字节当作
无意义间隙，再把 `cover_frame_len` 后面的 4 字节当作图片长度直接读图片，然后
认定音频开始。旧文件的 `cover_frame_len == image_len`，两种读法结果相同；2025
年后下载的文件常见 `image_len = 0` 而帧内预留约 7.4–7.6 KB 填充，这些实现就把
填充当作音频开头。流密钥按音频内偏移取值，错位后每个字节都解错，文件头变成
随机字节，播放器报“Header missing”。

taurusxin/ncmdump（`src/ncmcrypt.cpp`）读取 `cover_frame_len` 并在读完图片后
`seekg(cover_frame_len - n)`，是本 Skill 采用的读法。

## 流密钥

密钥调度与标准 RC4 相同（`S` 置换 256 字节）。生成阶段不同：音频第 `off` 个字节
（从 0 开始）的密钥字节为

```text
j  = (off + 1) & 0xff
ks = S[(S[j] + S[(S[j] + j) & 0xff]) & 0xff]
```

只依赖偏移，所以 256 字节一个周期，可整块生成后与音频做一次异或。

## 格式识别

以解密后的前 16 字节为准，不信任元数据里的 `format`：

| 开头 | 格式 |
| --- | --- |
| `ID3`，或 `0xFF` 且下一字节高 3 位全 1 | MP3 |
| `fLaC` | FLAC |
| 偏移 4 处 `ftyp` | M4A |
| `OggS` | OGG |
| `RIFF....WAVE` | WAV |

MPEG 同步字只有 11 位，错位噪声约 1/2048 的概率会碰巧命中，所以写出后还要比对
时长。

## 故障对照

| stderr 原因 | 含义 | 处理 |
| --- | --- | --- |
| `not an NCM file` | 文件头不是 `CTENFDAM` | 可能本来就是普通音频，或扩展名被改过；用 `file` 查看 |
| `unexpected EOF in ...` | 文件不完整 | 在网易云客户端重新下载 |
| `decrypted audio has unknown header` | 解密后不是已知音频格式 | 文件损坏或出现新加密变体；保留样本，不要重复重试 |
| `cover length ... exceeds frame length` | 封面帧字段自相矛盾 | 文件损坏或新变体，同上 |
| `output lasts ...s, metadata says ...s; the file may be incomplete` | 磁盘上实际可播放的时长与记录不符 | 多为下载中断的 `.ncm`，在网易云重新下载；也可能是试听片段；不要用 `--force` 掩盖 |
| `no such file or folder` | 输入路径不存在 | 核对路径拼写 |
| `cannot read folder: ...` | 目录无读取权限 | 授权或换目录；其他输入照常处理 |
| `output path ... is a folder` | 目标文件名被同名文件夹占用 | 改用 `--output-dir` 或让用户处理 |
| `conflict`：`a different or incomplete audio file ...` | 同名输出能播放但时长不符，可能是用户自己的文件或被截断的旧结果 | 告诉用户两者时长，用户同意后再 `--force` |
| `conflict`：`another input in this run writes the same output` | 同批次两个 `.ncm` 映射到同一输出名 | 去掉重复输入，或分别指定输出目录 |
| 退出码 2：`cannot open log file` | `--log` 路径不可写 | 修正日志路径；此时不会处理任何文件 |
| `... payload needs ffmpeg ...` | 无损内容转 MP3 需要 ffmpeg | 安装 ffmpeg、传 `--ffmpeg`，或用 `--format original` |
| `ffmpeg exited N: ...` | 转码失败，后面是 ffmpeg 原文 | 按 ffmpeg 报错处理；常见是负载损坏 |
| `missing dependency: ...` | 缺 pycryptodome 或 mutagen | 用 `uv run`，或征得同意后 `pip install` |
