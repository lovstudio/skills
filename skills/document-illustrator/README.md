# lovstudio:document-illustrator

![Version](https://img.shields.io/badge/version-0.2.1-CC785C)

为文档原地插入 AI 配图：先全局规划插入点，再并行生成图片，最后按锚点异步插回原文。

Part of [lovstudio general skills](https://github.com/lovstudio/general-skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx lovstudio skills add document-illustrator -g -y
```

## Workflow

1. 备份原文档为 `{doc_path}.illustrator-backup`
2. 读取完整文档并规划所有插图位置
3. 并行生成所有图片
4. 用锚点文本把图片异步插回原文
5. 验证成功后清理备份

## Options

| Option | Default | Description |
|---|---|---|
| 图片比例 | `16:9` | 可选 `16:9` / `3:4` |
| 封面图 | `否` | 是否在文档开头插入封面 |
| 内容配图数量 | 根据文档长度推荐 | 通常 3-10 张 |
| 风格 | `gradient-glass` | 可选 `gradient-glass` / `ticket` / `vector-illustration` |

## Dependencies

The generation scripts require:

```bash
python3 -m pip install google-genai pillow python-dotenv
```

Set `GEMINI_API_KEY` in the environment or `.env`.

## License

MIT
