# Selection JSON

`video_moments.py package` 消费 UTF-8 JSON，文件路径相对于 selection.json 所在目录解析，也接受本机绝对路径。私有绝对路径只能保存在用户运行目录，不提交 Skill 源。

必须字段：

- `schema`: video-moments-selection/v1。
- `frames_manifest`: extract 生成的 originals/frames.json 相对路径。
- `source`: 原视频的 name 与 duration。
- `selection_basis`: visual 或 audiovisual，依据实际核验能力填写。
- `moments`: 1–9 条记录，顺序为建议发图顺序。

每条 moment 必须包含唯一 id、源 time 秒数、category、reason、可观察 evidence、original 和 final 文件路径、original_sha256、final_sha256、edit_method，以及 review 对象。

`review` 必须包含 source_match、identity、screen_text、composition、privacy，只有实际查看后才能写 true。`privacy=true` 仅表示已检查私人内容，不代表获得公开肖像授权。review_notes 可记录原图已模糊、没有屏幕等具体情况。美化修改任何像素后重新验收、计算哈希。

`edit_method` 为 imagegen、photographic 或 original；未使用 AI 不写 imagegen。可选 quote 非空时必须有 quote_verified=true，并在 evidence 写明音频/转录证据。

`frames_manifest` 把原始帧、时间码和源视频绑定起来；最终文件必须与该源帧逐张比较。源帧已不可读的文字保留模糊，不制造清晰文本。哈希可通过 Python hashlib.sha256 或系统 shasum 计算。

所有最终图片必须实际拥有同样的像素宽高。打包器不会静默裁切或缩放；尺寸不符先返回图像编辑阶段。package 输出新目录，已有目录直接拒绝。

## 多源组图

目录含多个视频时，`package` 仍逐源执行。每个 selection 保留自己的 `frames_manifest`、源身份和相对该视频的 time，先通过原有门禁；不要把多个视频伪装成一段 source 或更换源哈希。

合并层由宿主按已通过的单源包整理：

- 总量 1–9 张，先确定全组顺序；全组 id 唯一，禁止重复的成图哈希及同一源的同一时间。
- 输出 `schema=video-moments-collection/v1`。`images` 每项保留 `order`、`id`、`file`、`size`、`sha256`、`edit_method`、`review`，另附源名称、源 fingerprint、时间码、原帧 SHA-256 和原 selection 路径。
- 确认全组尺寸相同，复制到新目录的 `images/01.jpg` 等；复制前后 SHA-256 必须相同。
- `verify` 可核对 collection 的成图尺寸与哈希，但不代替逐源 selection 门禁。不能把一次 verify 成功描述为已验证合并来源。
- 本地 gallery 提供全尺寸图片与原图对比；总览不裁掉人物。照片 ZIP 只装最终照片并校验 CRC、数量及条目哈希。

`edits.json` 同时记录成图 `sha256`（文件字节）和 `pixel_sha256`（解码 RGB 像素）。ICC 日期等元数据改变会影响文件哈希；必须比较实际解码像素才能确认画面未变，并更新所有最终文件哈希。发生像素变化则重新视觉验收。
