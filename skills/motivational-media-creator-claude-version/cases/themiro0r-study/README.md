# 案例：从 8 条 TheMiro0r 原片建立节奏包络

## 输入

- 8 条原片与原生英文字幕：`mgmVOuLgFB0`、`g-jwWYX7Jlo`、`26U_seo0a1g`、`9z4Kft47kBM`、`ZOy0YgUDwDg`、`V2EfL1j4KYE`、`Se7ulyG5nFA`、`nigWWy-SDhQ`。2026-10-22 在用户授权下取得，存放在手工川内容创作仓库的研究目录 `output/research/themiro0r-2026-10-22/media`，不随 Skill 分发。

## Prompt

`/lov-skill-creator 基于 …/themiro0r-2026-10-22/media 做 lov-motivational-media-creator-claude-version`

## 做了什么

1. 逐片 `study_reference.py --transcript <en.vtt>`（Dream 另加 `--ignore-cue` 去掉致谢条）。
2. 每 4 秒一帧、带时间码的联系表 15 张，实际看了 9 张，覆盖全部 8 条。
3. 按 20 秒分段通读 8 份字幕，标出节拍。
4. `build_envelope.py` 按片型分组（5 条 chorus、3 条 single-arc）→ `assets/reference-envelope.json`。

## 输出

- `assets/reference-envelope.json`
- `references/reference-study.md`（逐片指标、规律、画面手法、三条片子的节拍表、局限）
- `references/archetypes-and-beats.md`、`references/rhythm-and-sound.md`

## 过程中发现并修掉的脚本问题

- 本机 FFmpeg 不再接受 `-vsync`，联系表命令改用 `-fps_mode vfr`。
- `ebur128=framelog=verbose` 在默认日志级别下不输出逐帧数据，第一次跑出的响度弧全为空；改用 `ametadata` 输出短时响度后重跑。
- 字幕末尾的“字幕组署名”条被算作人声，让尾声变成 0 秒；加了默认过滤和 `--ignore-cue`。

## 未做

没有连续完整看片，没有主观听音；切点漏计叠化与甩镜。
