# Atom Workbench

Atom Workbench 是 `lov-atom-feature-dev` 的本地 Companion Dashboard。它采用 ADE 的工作区
思路，但把组织单位从“项目 / 文件 / Agent session”缩小为一个可独立验收的 atom feature。

## 界面

- 左侧：目标工作区与六阶段 Development Flow；
- 中间：Overview、Contract、Run、Compare、Review；
- 右侧：Profile Preset 来源与可直接交给 Agent 的当前 brief；
- 底部：真实 surface command 的 stdout、stderr、退出码和耗时。

## 启动

只看界面 Demo：直接打开 `dashboard/index.html`。此时使用内置只读快照，页面会标记
`File preview · demo data`；不会调用 API、执行 surface 或保存 Profile。

只读模式：

```bash
python3 scripts/atom_feature.py dashboard --root PROJECT
```

允许执行 manifest 中已经声明的 command array：

```bash
python3 scripts/atom_feature.py dashboard --root PROJECT --allow-run
```

允许保存 Profile Preset：

```bash
python3 scripts/atom_feature.py dashboard --root PROJECT --allow-write
```

`--open` 才会主动打开默认浏览器。未传授权参数时，Workbench 只提供只读控制面。默认端口为
`6174`，可用 `--port` 修改。

## Surface command contract

每个可执行 surface 在 `.atom-feature/manifest.json` 中声明 argv 数组：

```json
{
  "status": "implemented",
  "artifact": "tools/export.py",
  "command": ["python3", "tools/export.py"]
}
```

Workbench 将 resolved input 以 UTF-8 JSON 写入 stdin。命令应把规范化业务结果以 JSON 输出到
stdout，把诊断写到 stderr，并使用非零退出码表示失败。Bridge 使用 `shell=False`，不接受
浏览器传入任意命令。

## Local security boundary

- 只允许绑定 `127.0.0.1`、`localhost` 或 `::1`，并拒绝非本地 `Host`；
- 默认不执行命令、不写 Preset；
- 只读取所选项目内由 manifest 引用的 contract 文件；
- 运行输出限制长度并遮蔽常见 token、secret、password 与 API key；
- 运行记录只写入项目内 `.atom-feature/runs/` 和 `status.json`；
- Web 前端使用 restrictive CSP，不加载第三方脚本、字体或遥测。

## 验证

```bash
python3 scripts/atom_dashboard.py selftest
node --check dashboard/app.js
python3 scripts/atom_feature.py validate --root dashboard/demo-project
```

Selftest 在临时目录复制 demo workspace，启动随机 loopback 端口，回读 HTTP health、workspace、
静态入口并真实执行 SDK command。它不会修改 Skill 内置 demo。
