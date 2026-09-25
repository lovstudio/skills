# 一个备份目录，让 slash 列表凭空长出两条命令

打开 Claude Code 敲下斜杠，列表里多了两条我从来没写过的东西：

```text
enhance-claude-md.backup.20260303_013706:enhance-claude-md
enhance-claude-md.backup.20260303_013706:README
```

冒号前面那串带时间戳的名字，已经把答案写在脸上了。

## 加载器只认目录和 .md

`ls ~/.claude/commands` 一眼看到源头：

```text
cc-doctor
code-reviewer.md
enhance-claude-md
enhance-claude-md.backup.20260303_013706
frontend-design.md
lovstudio
Skill Development.md
```

Claude Code 把 `commands/` 下的每个子目录当成一个 slash 命名空间，目录里的每个 `.md` 注册成一条 `命名空间:命令名`。这个备份目录里躺着两个文件：旧版的 `enhance-claude-md.md`，和一份 `README.md`。

加载器不知道 `.backup.20260303_013706` 对我意味着什么。它看见一个目录、两个 `.md`，于是注册了两条。

README 也变成命令这件事最能说明机制：**没有豁免名单，凡是 `.md` 就是入口。**写给人看的说明文档和可执行的命令提示词，在这个目录里没有区别。

diff 完更不想留着它。正式版的 `enhance-claude-md.md` 只有 501 字节，是今年 3 月迁移之后的兼容入口，正文一句话——把本次请求交给 `lov-agent-instructions`；备份是 4089 字节的旧版全文，带着 `permissions`、`hooks` 和一整套 `claude-md-enhancer` 的多阶段工作流。手滑点中带时间戳的那条，跑的是半年前已经废弃的流程。

顺手在 `~/.claude/agents/` 里翻到同一批留下的 `claude-md-guardian.md.backup.20260303_013706`，跟正式文件 diff 完全一致。它的结尾不是 `.md`，大概率没被加载，但留着也没有任何理由。

## 先确认没被追踪，再挪走

`~/.claude` 本身是个 git 仓库，所以动手之前先问一句它管不管这些文件：

```bash
git ls-files commands/enhance-claude-md.backup.20260303_013706 agents/
```

没有输出。这些备份从来没进过版本控制，删掉就是真没了。

所以不用 `rm`，用 `mv`：

```bash
mkdir -p ~/.claude/backups/removed-from-scan-20260909
mv ~/.claude/commands/enhance-claude-md.backup.20260303_013706 \
   ~/.claude/agents/claude-md-guardian.md.backup.20260303_013706 \
   ~/.claude/backups/removed-from-scan-20260909/
```

`~/.claude/backups/` 不在任何扫描路径上。文件还在原地能取回，slash 列表干净了。

再把 `commands/` 和 `skills/` 下的 `README.md` 全扫一遍，只剩 `skills/media-use/luts/README.md`——它在某个 skill 内部的资源子目录里，不构成命令命名空间，不受影响。

## 沉淀规则时翻的两个车

这类结论值得进长期规则，我把它加进 `/Users/mark/.agents/references/misc-operations.md`：

> `MISC-25` **备份不留在扫描目录**：`~/.claude/commands|skills|agents` 下的备份目录会被当成命名空间加载，目录内每个 `.md`（含 README）都会变成多余的 slash 条目；备份一律移到 `~/.claude/backups/`。

写完回读编号，撞了。文件里已经有一条 `MISC-14` 在讲生图模型下线，我顺手接的编号正好压在它上面。grep 一遍现有编号，最大是 24，改成 `MISC-25`。

然后想给规则变更做个 commit 方便日后溯源，`cd /Users/mark/.agents && git add -A` 直接报 `fatal: not a git repository`。是 `~/.claude` 是仓库，`.agents` 不是。而我已经按习惯在条目末尾标了 `3474d0f`——那是 `~/.claude` 的 HEAD，跟这条规则所在的文件毫无关系。删掉，只留日期。

一条指向错误仓库的溯源信息，比没有溯源信息更糟。

## 约定式加载的代价

不需要注册表，把 `.md` 丢进 `commands/` 就能用，这是 Claude Code 这类工具顺手的原因。代价是目录结构本身成了配置：任何“人类看得懂”的命名——`backup`、`old`、`_deprecated`、`副本 2`——对加载器都不构成信号。

备份要么改掉扩展名，要么挪出扫描路径。我选第二种，因为不知道下个版本的加载器会不会开始认别的后缀。
