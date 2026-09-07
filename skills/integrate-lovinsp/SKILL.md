---
name: lov-integrate-lovinsp
license: MIT
compatibility: Portable Agent Skills format. Requires a Node frontend project with
  pnpm or npm and a supported bundler config (Vite / Webpack / Next.js / Nuxt / Rspack
  / Farm / Mako).
description: 为现有前端项目幂等接入 Lovinsp 并验证点击定位源码能力。支持明确输入与结果回读。Use to integrate Lovinsp
  in a frontend project.
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 1.6.2
  tags:
  - lovinsp
  - click-to-code
  - devtools
  - frontend-integration
  content_class: deterministic-output
  card_standard: lovstudio/skill-card/v1
---

# Lovinsp 接入 · Lovinsp Setup

幂等地将 lovinsp（点击 DOM 跳转源码）集成到当前前端项目。支持从 code-inspector 自动迁移。

## Triggers

### Activate when

- The user asks to use this Skill for its documented outcome.

- 用户说「装 lovinsp」「集成 lovinsp」「接入点击跳转源码」「click to code」「从 code-inspector 迁移」。
- 用户新建或升级一个浏览器渲染的前端应用，且需要开发期点击定位源码的能力。
- 另一个 Skill（如 `lov-app-generator`）把 Lovinsp 集成列为必须满足的默认不变量。

### Do not activate when

- 目标不是浏览器渲染的前端项目（纯后端服务、CLI、库、无 UI 的 Skill 包）。
- 用户只想了解 lovinsp 是什么、不要求改动当前项目。

本 Skill 是幂等的：已集成时只做版本检查，不会重复写入配置，因此可以被模型自动调用，
不需要人工逐步确认。

## 执行步骤

### 1. 检测项目类型

检测当前项目使用的构建工具：

```
glob: vite.config.{ts,js,mjs}
glob: webpack.config.{ts,js,mjs}
glob: next.config.{ts,js,mjs}
glob: nuxt.config.{ts,js}
glob: package.json
```

根据检测结果确定 bundler 类型：`vite` | `webpack` | `esbuild` | `turbopack` | `mako`

### 2. 检查是否已集成（幂等检查）

在配置文件中搜索：
- `lovinsp` 关键字
- `lovinspPlugin` 关键字
- `@lovinsp/` 前缀

如果已存在：
1. 检查版本更新：`pnpm view lovinsp version` 对比当前版本
2. 若有更新：提示「当前 x.x.x → 最新 y.y.y」并执行 `pnpm update lovinsp`
3. 若已是最新：输出「✓ lovinsp 已集成（v最新版），无需操作」

### 3. 检测并迁移 code-inspector（如存在）

检查 package.json 是否包含 `code-inspector` 相关依赖：
- `code-inspector-plugin`
- `@aspect/code-inspector-plugin`

如果存在，执行迁移：

**3.1 卸载旧依赖：**
```bash
pnpm remove code-inspector-plugin
# 或
npm uninstall code-inspector-plugin
```

**3.2 更新配置文件中的引用：**

替换 import 语句：
```diff
- import { codeInspectorPlugin } from 'code-inspector-plugin';
+ import { lovinspPlugin } from 'lovinsp';
```

替换插件调用：
```diff
- codeInspectorPlugin({ bundler: 'vite' }),
+ lovinspPlugin({ bundler: 'vite' }),
```

**3.3 输出迁移信息：**
```
✓ 已从 code-inspector 迁移到 lovinsp
  - 卸载: code-inspector-plugin
  - 安装: lovinsp
  - 更新: 配置文件
```

### 4. 安装依赖（幂等）

检查 package.json 的 devDependencies 是否已包含 `lovinsp`：
- 已存在：跳过安装
- 不存在：执行 `pnpm add -D lovinsp` 或 `npm install -D lovinsp`

### 5. 修改构建配置

根据 bundler 类型，在配置文件中添加插件：

**Vite (vite.config.ts):**
```typescript
import { lovinspPlugin } from 'lovinsp';

export default defineConfig({
  plugins: [
    // lovinsp 必须放在框架插件之前
    lovinspPlugin({ bundler: 'vite' }),
    // ... 其他插件
  ]
});
```

**Webpack (webpack.config.js):**
```javascript
const { lovinspPlugin } = require('lovinsp');

module.exports = {
  plugins: [
    lovinspPlugin({ bundler: 'webpack' }),
  ]
};
```

**Next.js with Turbopack (next.config.ts):**
```typescript
import { lovinspPlugin } from 'lovinsp';

export default {
  turbopack: {
    rules: lovinspPlugin({ bundler: 'turbopack' }),
  },
};
```

**Next.js with Webpack (next.config.js):**
```javascript
const { lovinspPlugin } = require('lovinsp');

module.exports = {
  webpack: (config) => {
    config.plugins.push(lovinspPlugin({ bundler: 'webpack' }));
    return config;
  }
};
```

### 6. 验证集成生效（无人值守时必须做）

只确认「依赖装上了」不足以说明集成成功——插件顺序错、配置写进了未被读取的文件，
都会静默失效。所以在配置改完后回读一次。

静态检查（任何 bundler 都做）：

- 配置文件里确实 import 了 `lovinsp` 并调用了 `lovinspPlugin`；
- Vite 项目中 `lovinspPlugin({ bundler: 'vite' })` 排在框架插件之前；
- package.json 与配置文件里都不再残留 `code-inspector` 引用。

运行期回读（Vite 项目，dev server 已在跑时做；用户未启动 dev server 就跳过，
不要为了验证而自行拉起或杀掉服务）：

```bash
curl -s http://127.0.0.1:<port>/src/main.tsx | rg "lovinsp-component|lovinsp v"
```

命中即证明 transform 已生效。未命中或未验证时，在结果里如实说明验证到哪一步为止。

**build --watch 架构（非 `vite dev` serve）：**

- lovinsp 的 IDE 桥 HTTP 服务在 build transform 阶段启动、随构建进程存活；项目用 `vite build --watch`（产物被独立 host 静态 serve，而非 `vite dev`）时，必须带 `LOVINSP=1` 常驻 watch 跑，一次性 build 会让桥服务随进程退出而死、点击无跳转（2026-08-20, 12c007237d）
- monorepo 分「shell vite build」与「插件 tsdown watch」两层时，只有含 `vite.config.ts` 的 shell 层触发 lovinsp 注入，别用插件层 watch 替代（2026-08-20, 12c007237d）

### 7. 输出结果

成功集成后输出：
```
✓ lovinsp 集成完成

使用方法：
- Mac: Option + Shift 激活检查器
- Windows: Alt + Shift 激活检查器
- 点击任意 DOM 元素跳转到源码

文档: https://inspector.fe-dev.cn/en
```

## 幂等性保证

- 依赖检查：已安装则跳过
- 配置检查：已配置则跳过
- 重复执行：结果一致，无副作用

## 支持的框架

- Vite: React, Vue2, Vue3, Svelte, Solid, Preact, Qwik, Astro
- Webpack: React, Vue
- Next.js (Turbopack/Webpack)
- Nuxt
- Rspack, Farm, Mako




## Execution boundary

自然语言请求即可触发；无需旧 slash 路径、参数插值或指定助手。明确解析当前请求中的
项目、目标文件、选项与输出位置；用当前宿主实际提供的文件、搜索、CLI 和浏览器能力。
项目依赖版本与外部 API 在执行时核实，不能假设示例是现行配置。随包脚本从 Skill 根解析，
业务文件从目标项目根解析。先读当前状态，保护已有未提交内容与其他任务的暂存区。
分析、预览请求保持只读；修改、提交、推送、部署和发布各依当前请求的明确范围执行。
不绕过保护、自动发送消息、强制结束用户进程或抢前台。失败保留可诊断原始错误。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
