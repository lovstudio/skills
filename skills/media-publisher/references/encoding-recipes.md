# 平台拒绝转码后的重压方案

## 适用场景

上传进度到 100%、平台在服务端转码阶段返回失败文案（例如「视频转码失败，调整视频导出参数后重试」）时使用。这类失败不发生在上传期，只有整包传完、服务端尝试转码后才暴露，所以长视频的代价是数小时。

先确认这是服务端转码拒绝，而不是硬限制拦截：文件大小与时长都在当前页面显示的限制内，预检也没有 `errors`。若预检有 `errors`，按 [平台约束](wechat-channels/platform-constraints.md) 处理，不要走本文流程。

## 观测到的一次拒绝与修复

2026-08-15 记录，样本量为 1，作为经验线索而非已证明的因果律：

| 项目 | 被拒版本 | 重压后 |
| --- | --- | --- |
| 文件大小 | 10.02 GB | 1.838 GB |
| 视频码率 | 11.16 Mbps | 1.88 Mbps |
| 时长 | 7054.80 s（1:57:34.80） | 同源，未变 |
| 音频 | AAC 196 kbps | 原轨直通，未重编码 |
| 预检结果 | 仅一条 `video_bitrate_high` | `status=pass`，`warnings` 为空 |
| 平台结果 | 转码失败 | 通过并发布 |

两版之间同时变化了码率、文件体积和封装，无法单独归因到码率。可确定的是：预检唯一标记的偏离项就是 `video_bitrate_high`，把它消除后同一素材通过。因此把「建议项」当作长视频的实际门槛处理，比事后重传划算。

## 先测码率，再定预算

不要凭猜测选码率。用 CRF 抽样，让素材自己给出在目标画质下的真实码率，再据此定 ABR 预算：

```bash
# 在片中三处各取一段，读 CRF 23 preset slow 的实际码率
for t in 600 3000 5400; do
  ffmpeg -hide_banner -nostdin -ss "$t" -i <输入视频> -t 30 \
    -c:v libx264 -preset slow -crf 23 -an -f mp4 -y /tmp/probe-$t.mp4 2>/dev/null
  ffprobe -v error -select_streams v:0 \
    -show_entries stream=bit_rate -of csv=p=0 /tmp/probe-$t.mp4
done
```

上面那次抽样得到 1.71 / 1.79 / 1.81 Mbps，故取 1880k 做 2-pass，略高于抽样上界以留出复杂段余量。

有目标体积上限时，反推视频码率预算：

```
视频码率 ≈ (目标字节 × 8 − 音频码率 × 时长) / 时长 − 容器开销
```

容器开销按 1% 留余量即可。两个约束取更小值：抽样码率满足画质，体积预算满足上限。

## 2-pass 重压

2-pass ABR 比单 pass CRF 更适合这里，因为需要精确命中体积预算：

```bash
COMMON=(
  -c:v libx264 -preset slow -b:v 1880k
  -maxrate 3800k -bufsize 7600k
  -x264-params aq-mode=3
  -profile:v high -level 4.0 -pix_fmt yuv420p
  -g 120 -keyint_min 24
  -color_primaries bt709 -color_trc bt709 -colorspace bt709
)

ffmpeg -hide_banner -y -i <输入视频> -map 0:v:0 "${COMMON[@]}" \
  -pass 1 -passlogfile <日志前缀> -an -f null /dev/null

ffmpeg -hide_banner -y -i <输入视频> -map 0:v:0 -map 0:a:0 "${COMMON[@]}" \
  -pass 2 -passlogfile <日志前缀> \
  -c:a copy -map_metadata 0 -movflags +faststart <输出视频>
```

各参数的理由：

- `-c:a copy`：音频已合规就不要重编码，省一次有损代价，也少一个可能被平台挑剔的变量。
- `-movflags +faststart`：moov 前置，网页端边传边解析更顺。
- `-maxrate` / `-bufsize` 取平均码率的 2 倍 / 4 倍：给复杂段留峰值空间，同时约束 VBV 不失控。
- `aq-mode=3`：对暗部和平坦区域更友好，人脸与字幕边缘更稳。
- `-g 120 -keyint_min 24`：关键帧间隔可预期，便于平台切片。
- 显式写 bt709 三件套：避免色彩元数据缺失导致服务端二次猜测。
- `-preset slow` 而非 `veryslow`：长视频里后者的收益不足以补偿翻倍的耗时。

不要用 VideoToolbox 等硬件编码器换速度。硬编在同码率下画质明显差于 x264，而这里的瓶颈是「一次通过」，不是压制耗时。

## 重压后必须验证

体积正确不等于文件可用。至少做三项：

```bash
# 1. 全解码，任何一帧出错即失败
ffmpeg -v error -xerror -i <输出视频> -f null - && echo "decode ok"

# 2. 回读实际码率、时长、流参数
ffprobe -v error -show_entries \
  format=duration,size,bit_rate:stream=codec_name,width,height,bit_rate,r_frame_rate \
  -of json <输出视频>

# 3. 重跑预检，要求 warnings 为空
python3 <本 Skill 目录>/scripts/check_video.py <输出视频> --json
```

时长要和源片逐秒对齐（容器时基差异带来的毫秒级偏移可接受）。预检还有 `warnings` 就不要上传，本文的全部意义就是不再把警告留到服务端去发现。

担心画质回退时，用可测量的指标而不是主观印象。例如比较源片与重压版在同一时间点的梯度能量，确认导航栏、字幕等细节区没有塌陷：抽同一帧做灰度 Sobel 求和，取比值。上面那次三处采样得到 99.8% / 100.0% / 99.9%，说明 1.88 Mbps 对该素材没有可见损失。

## 不要做的事

- 不要为了绕体积上限而切分成多条发布，除非用户明确要求分集。切分改变了内容形态，是产品决定，不是压制决定。
- 不要在没有实测的情况下下调分辨率或帧率。码率是这次的偏离项，动分辨率会引入新的不可控变量。
- 不要保留被拒版本作为备用上传目标。失败原因未消除前，重传只会再等一遍。
