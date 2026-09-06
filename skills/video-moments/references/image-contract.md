# 纪实美化与标准化

## 默认视觉

真实摄影，自然肤色，轻度去偏色、提亮人物、压制屏幕高光、温和降噪和锐化。整组采用同一白平衡倾向、曝光基准和比例，不做海报滤镜。默认无图上文案、无 Logo、无水印、无圆角套框。只有明确要求才加短 caption，逐字引用必须有音频证据。

投影教室常见“屏幕亮、人物暗”。以人物面部和现场暗部为曝光判断对象，分别检查原尺寸局部与手机缩略图。用户明确反馈太暗时，局部提亮必须肉眼明显，同时保持屏幕标题可读、肤色自然、白衣不过曝；不要仅用全图平均亮度或统一增亮参数验收。

默认保留原始横竖方向：横向现场用 16:9 或 3:2，纵向主体用 4:5；同一组只选一个比例。优先保留人与场景关系，不为方形裁掉主要人物。朋友圈九宫格外观如需预览，另做缩略预览；不能把九张切碎的大图当作九个 moments。

修图方法由当前请求与 Profile 的 `records.edit_method` 决定，并服从宿主约束。已选择摄影调色就直接执行；无需再次生成代表图测试。摄影流程见 [色彩还原](photographic-workflow.md)：颜色证据不明时先查元数据，Log 不能套普通 SDR 增亮滤镜。

建议交付 RGB JPEG，长边 1920（不足时不承诺恢复细节），质量 90–95；也接受宿主图像工具产出的统一尺寸 PNG。像素规格为本 Skill 的编辑约定，不宣称平台官方最佳规格。带 ICC 的图像应转为 sRGB，HDR/Log 明确变换后再交付。导出图片去除定位信息，源帧与源片独立保留。

## 宿主图像工具

遵循宿主图像编辑工具约束；提供本地源帧前先用视觉工具查看。每张使用一份参考源图，保持全组同一编辑目标。禁止凭文字另生一张相似教室代替原帧。

可复用编辑 brief：

> Edit this exact documentary event photograph. Correct only exposure, white balance and mild noise. Preserve every person's identity, facial expression, pose, hands, clothing, position and body shape. Preserve room geometry, people count, screen content, all visible text and logos exactly. Do not add or remove people or objects. Do not invent readable text from blurred pixels. Natural skin tones, restrained photographic contrast, no beauty-filter skin, no cinematic color cast, no synthetic depth of field. Keep the source aspect ratio and documentary composition. No new text, branding, frame or watermark. Match the approved set's output dimensions.

针对偏暗反馈，在 brief 中增加：

> Make a clearly visible brightness improvement to underexposed faces and room shadows, using soft neutral fill-light correction. Keep the already bright projection readable. People should look pleasantly illuminated on a phone screen, without washed-out skin or clipped white clothing. Match the brightness and white-balance direction across the set.

将实际 prompt、宿主工具、输出文件与每次验收结果写入本地数据目录。生成模型可能改变小脸和屏幕文字，不能只验收“好看”。如果身份、动作、屏幕不保真，拒收该图并定向修正；若仍失败，报告问题，保留原图。只有宿主和用户允许确定性摄影处理时，才使用 FFmpeg/ImageMagick/Pillow 做像素级曝光、裁切和重采样；绝不能伪称已完成 AI 美化。

## 回读门禁

逐张比较原图/成图：人物、人数、手势、衣服、投影文字、屏幕窗口、几何与隐私。检查是否过度磨皮、抹掉设备、改字和生成多余手指。关键脸部至少查看原分辨率局部，不能仅以缩略图判身份通过。

确定性摄影处理也必须逐图回读：检查肤色偏黄/偏绿、白衣过曝、投影失色、阴影噪点和局部提亮光晕。保留源片无法恢复的软焦、动作模糊与小字；不因提亮而宣称恢复了不存在的细节。回看手机尺寸整组，亮度与肤色一致不等于各图平均亮度相同。

再看整组缩略图：色调是否一致、是否重复、首张是否成立。最后校验实际像素尺寸、可解码性、文件 SHA-256。机器校验不证明语义正确；`review` 字段必须由实际视觉验收填写。

可把已美化但存在重绘的候选保存在单独的原图对比页，准确标注 AI 美化版本和具体保真缺陷。该对比产物不等于通过纪实门禁；保留失败记录，不改动 `package` 的验收要求，也不把局部看起来相似写成逐字或逐像素保真。

如果使用未经美化的原帧，写 `edit_method=original`，将结果标记为原帧精选；不可把原帧交付说成美化完成。
