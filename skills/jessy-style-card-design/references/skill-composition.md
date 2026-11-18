# Skill Group Composition

## Nearby Skills Inspected

| Skill | 路由合同 | 关系 |
| --- | --- | --- |
| `lov-iris-style-card-design` | 克隆 Iris 名片的内容架构与设计方法，双面电子稿 | sibling：同族的另一套版式，命名与分工照它；参考是 Iris 名片时用它 |
| `lov-business-card` | 收集身份信息，填固定的编辑式 2:1 模板（三套主题） | overlap（同为名片成品）：不指定参考时用它 |
| `lov-visual-clone` | 从参考图提取视觉 DNA，输出复刻 prompt | not composed：参考别的名片、只要视觉分析时用它 |
| `lov-wdb-cowork` | 读本地微信会话、起草回复、把对方要的活做出来 | upstream：从聊天里取出主体资料；downstream：起草随名片发出的消息 |
| `lov-wdb-cli` | 本地微信只读数据通道 | upstream（经 `lov-wdb-cowork`） |
| `baoyu-image-gen` | 多家图像 API 生成图片 | optional upstream：替代内置脚本生成地标线稿 |
| `lov-gen-card` | 知识卡片排版 | not composed：内容卡片，不是名片 |
| `lov-branding-consistency` | 读者可见文字的品牌与语境门禁 | declared dependency：审校职务译文、口号等新写文字 |

## Atomic Handoffs

| 交接 | 输入 | 负责方 | 输出 | 验收边界 |
| --- | --- | --- | --- | --- |
| 主体资料 | 微信联系人或群名 | `lov-wdb-cowork` | 对方在会话里确认过的姓名、职务、联系方式 | 每条资料能对应到会话原话 |
| 地标线稿 | 场景 prompt | `baoyu-image-gen` 或内置 `gen_illustration.py` | 白底线稿 PNG | 无字、无 Logo、无人像；`lineart.py` 转墨线 |
| 名片成品 | Profile、官方资产、Jessy 版式模板 | 本 Skill | PNG ×3 与自包含 HTML | 版式检查无问题、二维码 1/3 尺度可解、文字均有来源 |
| 随附消息 | 成品与会话语气样本 | `lov-wdb-cowork` | 未发送的消息草稿 | 不替用户发送 |

## Overlap Decisions

- 与 `lov-iris-style-card-design` 同族分开：两者都是“克隆某个人名片的设计，换成当前主体的资料”，
  各自锁定一张参考。Iris 那套偏内容架构（简介、关系段、案例证据），Jessy 这套是机构式横版信息卡。
- 与 `lov-business-card` 分开：它的版式是自有的编辑式模板，不对应任何参考名片。
- 参考别的名片时不扩展本 Skill：照本 Skill 的结构另建 `lov-<名字>-style-card-design`，
  `render_card.py`、`verify_qr.py`、`lineart.py` 可以原样复用。

## Composition Decision

Single Skill。映射、线稿、渲染、验收是同一个结果的连续步骤，单独拆出来都不是独立有用的产物。
外部 Skill 都是可选的文件级交接，不是隐藏依赖；没有它们时，用户直接给资料、内置脚本生成线稿即可完成。
