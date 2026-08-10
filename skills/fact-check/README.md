# lov-fact-check

![Version](https://img.shields.io/badge/version-0.1.2-CC785C)

尽调式事实校验 skill：把用户提出的事实命题拆成可验证问题，优先查一手资料，交叉验证证据链，并输出结论、边界和置信度。

Part of [lovstudio skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx lovstudio skills add fact-check -g -y
```

## Dependencies

无本地运行依赖。这是纯指令型 skill。

事实校验通常需要联网检索。涉及当前状态、技术文档、法规、产品能力、人物组织信息或需要精确出处的问题时，应优先使用 web/search 能力并引用来源链接。

## Usage

在 Claude Code 中触发：

```text
/lov-fact-check
```

也可以自然语言触发：

```text
帮我确认一下：Tauri 程序不支持 GitHub webhook handler 吗？
```

```text
Fact check this claim: Vite cannot be used with Tauri v2.
```

```text
这段文章里的核心事实是真的吗？请给我证据链。
```

## Output

默认输出结构：

```markdown
**结论**
成立 / 不成立 / 部分成立 / 目前无法确认。

**更精确的说法**
把原命题改写成更准确的表述。

**证据链**
1. [一手] 来源：证明了什么
2. [二手] 来源：证明了什么

**反例或边界**
版本、平台、定义、workaround、例外情况。

**置信度**
高 / 中 / 低：原因。

**下一步验证**
最小复现实验、要查的 issue、要问维护者的问题。
```

## Evidence Labels

| Label | Meaning |
|---|---|
| `[一手]` | 官方文档、源码、release notes、维护者直接回复、法规原文、论文原文 |
| `[准一手]` | 官方示例、官方博客、官方讨论区中维护者回复 |
| `[二手]` | 媒体、博客、教程、社区问答、百科 |
| `[实测]` | 本地复现、最小 demo、命令输出 |
| `[推断]` | 基于证据链的合理判断，但没有直接出处 |

## License

MIT
