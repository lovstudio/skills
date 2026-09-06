# Skill composition

## Nearby Skills Inspected

2026-09-06 检查本地真源与已安装入口的实际输入输出：

| Skill | 分类 | 实际契约 |
| --- | --- | --- |
| lov-video-chapter | upstream atom，可选 | 字幕和视频生成语义章节及视频章节条；章节时间表可提供候选窗口 |
| lov-image-decorator | not composed | 给现有图增加 caption 底栏和 Logo；默认外框/品牌署名不符合本任务纪实照片 |
| lov-output-wechat-moment | downstream atom，可选 | 从给定事实写朋友圈纯文本；不负责视频选帧与美化 |
| lov-media-selection | not composed | 从媒体发行版本中选编码、字幕和体积；不选一个视频内部的瞬间 |
| imagegen（宿主能力） | optional upstream atom | 仅在选定生成式路径时产出候选；已有摄影调色偏好时不调用 |
| lov-branding-consistency | microcopy 门禁 | 只审校本任务新增标题/短 caption；不改画面中的文字或引文 |

## Atomic Handoffs

章节或带时间戳转录 → 候选窗口：仅用户提供或语义筛选确有需要时使用，新 Skill 最终核对画面。

源视频/源帧 + 色彩证据 + 编辑参数 → 摄影成图，或源帧 PNG + 美化 brief → 宿主生成候选：按当前请求/Profile 和宿主约束选路径。保持原帧、编辑图、时间码、SHA-256 与视觉验收；本 Skill 拥有成图验收。

已验收图片 + 事实清单 → 朋友圈文字 Skill：仅用户要求配文时调用，文字作者不能补造授课内容或效果。

## Overlap Decisions

检查到的现有 Skill 没有拥有“从一个长视频挑选真实照片 moments 并统一美化交付”的完整结果。不扩展 image-decorator：其必要 caption/Logo 会给本工作流引入不相容的默认效果。不重复实现章节视频和媒体下载。

## Composition Decision

采用 Single Skill + standalone Python CLI。索引、筛选、编辑、验收共享源视频与选片清单，服务同一个组图结果，没有必要拆成可独立触发的 Kit。索引、摄影色彩处理与逐源打包在包内；生成式编辑/转录由宿主按需供应；邻近 Skill 只做可选的文件交接，不形成 sibling 运行依赖。
