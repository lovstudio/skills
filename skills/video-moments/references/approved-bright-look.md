# bright-documentary：明亮自然基准

## 已验证的方向

真实课程案例先交原帧后，用户指出“要美化，而且感觉太暗了”；六张明亮美化图交付后，用户明确反馈“这个明亮美化不错”，并要求固化到本 Skill。证据见 `cases/course-evidence.json`。认可对象是这组六张图的亮度、肤色与整体观感，不能扩展为任意人脸重绘或课件改字授权。

把 `bright-documentary` 作为课程现场的默认目标：

- 先看主体面部是否清楚、自然，不能被大面积明亮投影掩盖人物欠曝。
- 明显提亮皮肤、衣服、桌面与木墙暗部，同时压住投影亮部。
- 减轻偏蓝，采用中性、健康的肤色；保留真实皮肤纹理，不磨皮换脸。
- 全组方向统一，以不同场景的实际光线校准，不把每张图调成同一个全图均值。
- 保留现场构图、人物关系和环境，无额外海报框、文字、Logo 或景深特效。

## 可复用编辑 brief

> Edit the supplied photograph itself into a bright, clean, naturally flattering event photograph. Make a noticeable local brightness improvement to underexposed faces, skin, clothing, tabletop and room shadows. Faces must be clearly illuminated on a small phone screen. Use neutral fill-light correction, healthy natural skin and gentle contrast. Keep skin texture, facial shape, age, expression and identity; preserve exact pose, glasses, headset, clothing, hands and position. Preserve all people and objects, framing and aspect ratio. Keep projected screen words, Chinese characters, drawings, layout and colors faithful to the source. Do not reconstruct unreadable text. Protect already bright projection highlights. No new captions, logo, borders or watermark. No de-aging, fake bokeh, cinematic darkness or orange cast. Match the set's approved dimensions and brightness direction.

先完成一张代表图的实际回读，再用于同组。不要把生成工具承诺写成实际验收结果。

## 批准基准与修改边界

记录 `style_approved`、批准来源、成图哈希与本地路径。之后只修用户指出的局部问题，保留已经认可的亮度、构图、人物关系和整体风格。不可因局部小字问题退回偏暗原帧并称任务完成；也不可隐去小字重绘并冒充严格纪实成品。

分别记录风格认可、人物保真、课件保真。原帧长期保留在本地运行目录，私有人物图不随 Skill 源分发。`package` 的严格保真门禁保持独立；未通过的候选可交独立对比页，如实说明缺陷。

## 视频交接

全片亮度修复属于 `lov-media-preprocessor` 的可选上游结果。交接源片、已认可的参考图、时间码和视觉目标；视频必须额外验收帧间稳定性、音画同步与文字保真，不能把逐帧生图拼接当作同等处理。
