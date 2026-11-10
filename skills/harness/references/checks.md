# 检查项与整理动作

`scripts/harness.py` 的每个问题都有稳定的代码和 ID。ID 由代码、路径与对象算出，同一个问题在
两次扫描之间不变，可以直接传给 `tidy --fix <ID>`。

级别的含义：**错误**表示现在就不工作；**警告**表示违反约定或迟早出事；**提示**是可选的清理。

## System Prompt

| 代码 | 级别 | 含义 | 自动整理 |
| --- | --- | --- | --- |
| `PRM-ROOT-MISSING` | 提示 | 共享配置目录里没有 `AGENTS.md`，各宿主各自维护 | 无 |
| `PRM-RULE-DUP` | 错误 | 根 Prompt 或某个 reference 里规则编号重复 | 无 |
| `PRM-RULE-GAP` | 警告 | 根 Prompt 的数字编号不连续 | 无 |
| `PRM-PATH-MISSING` | 错误 / 警告 | 规则引用的本机路径不存在；根 Prompt 里是错误，reference 里是警告 | 无 |
| `PRM-REF-BROKEN` | 错误 | reference 是断开的链接 | 无 |
| `PRM-REF-UNROUTED` | 提示 | 根 Prompt 没有提到这个 reference 的文件名 | 无 |
| `PRM-NS-COLLISION` | 警告 | 两个 reference 使用同一个编号前缀 | 无 |
| `PRM-VERSION-DRIFT` | 警告 | 根 Prompt 的 `version` 与变更记录最新条目不同 | 无 |
| `PRM-HOST-BROKEN` | 错误 | 宿主指令文件是断开的链接 | 移除断链 |
| `PRM-HOST-STALE` | 警告 | 宿主文件里嵌入的规则副本记录的 sha256 与当前根 Prompt 不同 | 无，需重新生成 |
| `PRM-HOST-COPY` | 提示 | 宿主用的是内容相同的实体副本，不会随根 Prompt 更新 | 无 |
| `PRM-HOST-UNBOUND` | 提示 | 已知宿主的目录存在，但没有指令文件 | 链接到根 Prompt |
| `PRM-HOST-INDEPENDENT` | 提示 | 已知宿主的指令文件独立维护 | 无 |

规则按 ``- `ID` **标题**：正文`` 的写法识别；没有这种写法的文件只显示大小和行数。
路径引用只检查反引号里、位于家目录下的路径；带占位符或通配符的写法会跳过，命令行只看第一个词。

宿主指令文件的识别范围：Claude Code、Codex、Gemini CLI、Qwen Code、OpenCode、GitHub Copilot、
Qoder、CodeBuddy 的固定位置；宿主目录下直接放置的同名指令文件；以及家目录点目录两层以内任何
链接到根 Prompt 或嵌入其副本的文件。更深处的项目级指令文件不算宿主入口。

## Skills

| 代码 | 级别 | 含义 | 自动整理 |
| --- | --- | --- | --- |
| `SKL-BROKEN-LINK` | 错误 | Skill 入口是断开的链接 | 移除断链 |
| `SKL-FRONTMATTER` | 错误 | `SKILL.md` 没有可用的 frontmatter | 无 |
| `SKL-NO-NAME` / `SKL-NO-DESC` | 错误 | frontmatter 缺少 `name` 或 `description` | 无 |
| `SKL-FRONTMATTER-YAML` | 警告 | frontmatter 不是合法 YAML（需要 PyYAML 才能判断） | 无 |
| `SKL-NAME-INVALID` | 警告 | `name` 不是 64 字符以内的 kebab-case | 无 |
| `SKL-DESC-OVER-SPEC` | 警告 | `description` 超过 1024 字符 | 无 |
| `SKL-DUP-NAME` | 警告 | 同一宿主里多个目录声明了同一个 `name` | 无，建议停用其一 |
| `SKL-LINK-CHAIN` | 警告 | 宿主链接绕经另一个宿主的目录，按 Skill 汇总 | 共享目录里有它时改为相对链接 |
| `SKL-NO-SKILL-MD` | 警告 / 提示 | 目录里没有 `SKILL.md`；共享目录里是警告 | 共享目录里的移入整理备份 |
| `SKL-LINK-ABS` | 提示 | 宿主用绝对路径直连，而共享目录里已有同一个 Skill | 改为经共享目录的相对链接 |
| `SKL-NOT-SHARED` | 提示 | 宿主直接链接到源码，共享目录里没有它 | 登记到共享目录并改为相对链接 |
| `SKL-ALIAS` | 提示 | 同一个 Skill 在一个宿主里有多个入口 | 宿主里能确定主入口时移除别名链接 |
| `SKL-HOST-COPY` | 提示 | 宿主目录里的实体副本 | 无 |
| `SKL-HUB-UNLINKED` | 提示 | 共享目录里的 Skill 没有任何宿主链接到它 | 无，用 `tidy --link` 安装 |
| `SKL-STRAY` | 提示 | 共享目录里的非 Skill 文件 | 移入整理备份 |

宿主目录是共享目录 `<共享配置目录>/skills` 加上每个含有文件夹或链接的 `~/.<宿主>/skills` 与
`~/.config/<宿主>/skills`。内容类检查按真实目录去重，每个 Skill 只报一次。

## 工作室源码

| 代码 | 级别 | 含义 |
| --- | --- | --- |
| `STU-NOT-REPO` | 警告 | 源码目录不是独立的 Git 仓库 |
| `STU-DIRTY` | 警告 | 有未提交的改动 |
| `STU-UNPUSHED` | 警告 | 有未推送的提交 |
| `STU-VERSION-DRIFT` | 警告 | `SKILL.md`、`skill.yaml`、两张卡片与 README 徽章的版本号不一致 |
| `STU-NO-README` | 警告 | 缺少 `README.md` |
| `STU-CATALOG-AHEAD` | 警告 | 目录版本高于本地源码 |
| `STU-RUNTIME-NAME` | 警告 | 目录的 `runtime_name` 与 `SKILL.md` 的 `name` 不同 |
| `STU-MIRROR-MISSING` | 警告 | 免费条目在目录仓库的 `skills/` 下没有镜像 |
| `STU-BEHIND` | 提示 | 落后上游（以上次 fetch 为准） |
| `STU-NO-REMOTE` | 提示 | 还没有远端仓库 |
| `STU-CHANGELOG-STALE` | 提示 | 变更记录的最新条目不是当前版本 |
| `STU-CATALOG-BEHIND` | 提示 | 源码版本高于目录，等待发布或同步 |
| `STU-MIRROR-STALE` | 提示 | 目录镜像与源码版本不同（以本地目录仓库为准） |
| `STU-UNLISTED` | 提示 | 还没有登记到目录 |
| `STU-NOT-INSTALLED` | 提示 | 没有安装到本机任何宿主 |
| `STU-NO-SKILL-MD` | 提示 | 源码目录里找不到 `SKILL.md` |
| `STU-CATALOG-NO-SOURCE` | 提示 | 目录里有条目在本机找不到源码 |

工作室区域只报告，不提供自动整理：提交、推送、发版和改写内容都属于别的流程。
Git 状态只用只读命令读取，并关闭可选锁，不会干扰正在进行的 Git 操作。

## 整理动作

| 动作 | 触发 | 步骤 |
| --- | --- | --- |
| 移除断链 | `SKL-BROKEN-LINK`、`PRM-HOST-BROKEN` | 删除这一个符号链接 |
| 改为相对链接 | `SKL-LINK-ABS`、`SKL-LINK-CHAIN` | 删除旧链接，建立指向共享目录条目的相对链接 |
| 登记到共享目录 | `SKL-NOT-SHARED` | 在共享目录建立指向源码的链接，再把宿主链接改为相对链接 |
| 移入整理备份 | `SKL-STRAY`、`SKL-NO-SKILL-MD` | 先移除指向它的宿主链接，再把条目移到本批次的 `quarantine/` |
| 链接到根 Prompt | `PRM-HOST-UNBOUND` | 在宿主目录建立指向根 Prompt 的相对链接 |
| 移除别名链接 | `SKL-ALIAS` | 删除名字与 `name` 不同的那些链接 |
| 停用 | `tidy --disable <入口>` | 移除各宿主指向它的链接，把共享目录条目移到 `skills-disabled/` |
| 启用 | `tidy --enable <入口>` | 把条目移回共享目录，并恢复上次停用时移除的宿主链接 |
| 安装到宿主 | `tidy --link <入口> --host <宿主>` | 在宿主目录建立指向共享目录条目的相对链接，名字取 `name` |
| 从宿主移除 | `tidy --unlink <入口> --host <宿主>` | 删除宿主里的这一个符号链接 |

引擎的硬性边界，计划阶段和执行阶段各核对一次：

- 只删除符号链接，目标必须和计划时看到的一致；实体文件和目录永远不删。
- 移动只发生在共享目录、停用目录和整理备份之间。
- 新建链接的位置必须为空，目标必须存在。
- 所有路径必须位于共享配置目录或家目录的点目录内。
- 同一批次里两个整理项改动同一路径时拒绝规划。
- 任何一步失败就停下，其后的步骤标记为跳过。

## 整理记录

每个批次写在 `<整理记录目录>/<批次号>/journal.json`，批次号形如 `20261110-143000-ab12`。
记录包含请求的整理项、每一步的动作与结果，以及撤销时间。`undo` 按相反顺序执行逆操作，
逆操作同样先核对前提；全部成功后批次标记为已撤销，不能撤销第二次。
被移入整理备份的文件保存在同一批次目录的 `quarantine/` 下，撤销时移回原处。
