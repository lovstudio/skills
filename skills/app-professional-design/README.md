# 性能架构师 · Performance Architect

![Version](https://img.shields.io/badge/version-0.1.1-CC785C)

把应用的启动、数据加载、前后端 bridge、缓存和并发从“能运行”提升为可测量、可恢复、可持续优化的商业级架构，并推动实现与真实验收。

## 本地安装

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" \
  "$SKILLS_INSTALL_DIR/lov-app-professional-design"
```

## 使用

### 从具体卡顿修到完整数据链路

输入：

> 联系人页面每次切回来都会重新加载，而且加载期间整个界面卡住。请按商业级产品的方式修复。

输出：实际运行路径证据、生命周期所有权矩阵、全局后台任务、增量 bridge、快照与失效协议、代码修改、回归测试和运行时验证。

### 系统审查现有应用

输入：

> Review this desktop app and implement a production-grade startup, streaming data, caching, and concurrency architecture.

输出：基于真实热点的分层诊断、优先级明确的架构修复、关键垂直切片实现、性能基线和剩余风险，而不是泛化的重写建议。

## 适用范围

- Tauri、Electron、原生桌面、Web、移动端和混合应用。
- 冷/热启动、索引初始化、大列表、搜索、文件监听、实时数据、IPC/bridge、后台任务、线程池和多进程隔离。
- 既支持一个明确性能缺陷，也支持对现有应用做系统性性能架构审查。

纯视觉设计、纯技术选型或单独的 Tauri 命令面治理由相邻能力处理。

## 质量门

```bash
python3 scripts/validate_skill.py .
```

同时检查：

- 一个文档化触发语能稳定路由到本 Skill；
- “只调整按钮颜色和字号”保持在视觉设计能力范围；
- 所有 references 均能解析且没有私有绝对路径；
- Skill 要求同数据、同环境的前后对照，不允许以编译通过替代用户交互验收。

## 依赖

- Skill 运行时：无额外依赖。
- 本地质量校验：Python 3.8+、PyYAML。

## License

MIT
