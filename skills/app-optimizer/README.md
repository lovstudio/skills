# 应用性能医生 · App Performance Doctor

![Version](https://img.shields.io/badge/version-0.2.1-CC785C)

面向交互式应用的证据驱动运行时优化 Kit。它把“越用越卡、掉帧、耗电、内存增长、后台资源不释放”拆成真实运行时审计、工作量削减、生命周期治理和同负载验收，覆盖 Electron、Tauri、原生桌面、iOS、Android、React Native、Flutter 与 Web/PWA。

Electron/Yoda 是首个完整案例；平台无关核心不要求 tmux、worktree 或 Node。

## 本地安装

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" \
  "$SKILL_SKILLS_INSTALL_DIR/lov-app-optimizer"
```

仓库初始化时也可让 Skill Creator 建立同名符号链接。安装目录只保存链接，源代码仍位于可维护的 Skills 仓库。

## 使用示例

- `这个 Electron 应用越用越卡，按真实进程和数据规模定位后台风暴并优化。`
- `iPhone 真机滚动掉帧、切后台后耗电，请固定 release build 和操作脚本做 Instruments 前后对照。`
- `这个 PWA 长时间打开后内存上涨，检查 worker、BFCache、轮询和不可见页面生命周期。`
- `Review this session/cache reclamation design for ownership gaps, ABA races, and fail-open behavior.`

完整流程使用 `optimize-runtime`；也可选择 `audit-only`、`review-reclamation` 或 `verify-change`。

## 输出

- `app-runtime-evidence/v1` 证据账本、运行边界和规模放大公式；
- 可证伪的根因排序与最小完整优化 seam；
- 所有权/lease/activity/fingerprint 驱动的安全生命周期方案；
- 冻结比较合同下的 before/after 报告与 evidence gaps；
- 正确性门、残余热点和下一次判别性测量。

Yoda 案例见 [`cases/cases.json`](cases/cases.json)。它保留 Electron、PTY/tmux、Agent session、Git worktree 与 SQLite 的具体证据，但不会把单产品数据写成跨平台结论。

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 -m unittest discover -s tests -p 'test_*.py'
```

## 用户 Profile

`skill.yaml` 声明 `user-profile/v1`。只有用户明确要求长期沿用的性能预算或输出偏好才写入共享 Profile；现场路径、设备标识、进程信息、凭据和推断不会持久化。v0.2 可读取旧 `lov-electron-runtime-optimizer` Profile 上下文，但只写新 namespace。

## 依赖

- Python 3.9+
- PyYAML（仅用于源代码 validator）
- 目标平台的 profiler、真机/浏览器、Git、tmux、SSH、SQLite 均为可选 adapter

## License

MIT
