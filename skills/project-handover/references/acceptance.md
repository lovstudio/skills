# 全新目录验收

目的：证明接手方拿到 zip、照着交接文档做，就能得到和交出方一样的结果。验收在交出方机器的临时目录里做，模拟一台没有任何缓存的新机器；做不到的部分（网络下载）要说明是环境问题还是包的问题。

## 步骤

```bash
mkdir -p "$TMP/accept" && cd "$TMP/accept"
python3 -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall('.')" <交接包>.zip
cd <交接包文件夹>
python3 "$SKILL_DIR/scripts/handover_manifest.py" verify .
python3 "$SKILL_DIR/scripts/handover_scan.py" . --top 5
```

然后按交接文档第 7 节逐条执行：安装依赖、类型检查或构建、关键工具的干跑、费用账本汇总、完整重建主要产物。最后比对：

```bash
python3 "$SKILL_DIR/scripts/media_compare.py" <原成品> <重建成品>
```

非媒体项目用项目自己的测试、构建产物的校验和或导出文件对比。

## 记录模板

```markdown
## 11. 交接验收记录（YYYY-MM-DD）

在一个全新目录里解开 zip，按本文第 7 节从零操作：

| 项目 | 结果 |
| --- | --- |
| 文件清单 | N 个文件，SHA-256 全部一致，无缺失、无多余 |
| 敏感信息扫描 | 无本机路径、邮箱、密钥 |
| 安装依赖与类型检查 | …（验收中修正的命令写在这里）|
| 关键工具 | … |
| 完整重建 | 成功；与原成品比对：声音…，画面…帧，最低 PSNR … dB |
| 环境问题 | …（及处理办法在第几节）|
```

## 常见坑（症状 → 原因 → 处理）

| 症状 | 原因 | 处理 |
| --- | --- | --- |
| pnpm 报 “packages field missing or empty” | `pnpm-workspace.yaml` 只有 `allowBuilds`、`onlyBuiltDependencies` 这类设置，属于 pnpm 10 写法 | 文档写 `npx --yes pnpm@10 install --frozen-lockfile` |
| `npx tsc` 提示 “This is not the tsc command you are looking for” | npx 去装了同名的无关包 | 用工程里的 `./node_modules/.bin/tsc` |
| 安装时 `ECONNRESET` | 官方源经代理偶发断线 | 文档给出镜像源写法，例如 `export npm_config_registry=https://registry.npmmirror.com` |
| 第一次渲染报 `ECONNRESET`，`node_modules/.remotion` 里只有半个 zip | Remotion 首次渲染要下载约 100 MB 的无头浏览器 | 先单独 `npx remotion browser ensure`；断了删目录重下。验收时可以用交出方已下载的同版本浏览器继续验证包本身，并在文档说明 |
| 脚本失败但显示退出码 0 | 管道 `cmd | tail` 返回的是 `tail` 的退出码 | 输出写日志文件，单独打印 `$?` |
| 生成工具干跑只显示 `cached`，不报价 | 已有足够的生成结果，工具跳过 | 文档写明要重跑先增加重跑次数字段 |
| 第三方生成服务报余额不足，实际余额够 | 服务按单个任务的最高可能费用预扣，并发任务一起占用额度 | 文档写明余额要留足、任务串行提交 |
| 生成任务提交后网络断开，本地报错 | 远端任务仍在运行并计费 | 用任务编号取回，避免重复提交付费 |
| 解包后出现 `__MACOSX`、`._*` | 用 Finder 压缩或 `ditto --sequesterRsrc` 打的包 | 用 `handover_pack.py` 重打 |
| Windows 上 `CLAUDE.md` 打不开 | 用了符号链接 | 改成一行文字的普通文件 |
| 重建成品的校验和和原成品不同 | 多线程编码、GPU 或 WebGL 渲染的细微随机性 | 用 `media_compare.py`：声音逐位相同、画面每帧 PSNR ≥ 40 dB 即视为一致；低于阈值时看最差的那几帧 |

## 验收后

- 修正文档里错误的命令和遗漏的步骤，把新发现的坑写进对应章节；
- 写验收记录，重新出清单和 zip，记下最终 SHA-256；
- 删除临时目录（含依赖和重建产物，常有数 GB）。
