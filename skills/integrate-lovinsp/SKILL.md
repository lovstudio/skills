---
name: lov-integrate-lovinsp
description: >
  幂等集成 lovinsp (click-to-code) 到当前前端项目，并支持从 code-inspector 自动迁移。
  Use when the user asks to "装 lovinsp"、"集成 lovinsp"、"接入点击跳转源码"、"click to code"、
  "从 code-inspector 迁移"，or when scaffolding/upgrading a browser-rendered app that needs
  click-to-source support. Also trigger when another skill (例如 lov-app-generator) requires
  the Lovinsp integration invariant to be satisfied. 重复执行安全：已集成则只做版本检查。
license: MIT
compatibility: "Portable Agent Skills format. Requires a Node frontend project with pnpm or npm and a supported bundler config (Vite / Webpack / Next.js / Nuxt / Rspack / Farm / Mako)."
metadata:
  author: contributors
  version: "1.5.0"
  tags:
    - lovinsp
    - click-to-code
    - devtools
    - frontend-integration
  dependencies: []
---

# Integrate Lovinsp

幂等地将 lovinsp（点击 DOM 跳转源码）集成到当前前端项目。支持从 code-inspector 自动迁移。

## Triggers

### Activate when

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

ARGUMENTS: $ARGUMENTS

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
