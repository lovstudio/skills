# Infographic brief

Working title: 移动端跨平台技术选型指南：渠道、体验与团队约束对比
Title mode: topic
Tail recommendation: 先按四类特殊约束分流；均不命中时，React Native + Expo 是均衡默认。
Template: comparison-matrix
Evidence mode: qualitative

## Audience and decision

- Audience: 启动或重构移动产品的产品负责人、技术负责人和开发者。
- Decision or use moment: 在五类跨端路线中确定优先验证对象。
- What should change after reading: 不再问“谁性能最好”，先识别主导约束。

## Governing message

小程序、Web 复用、自绘 UI、重原生四类特殊约束分别触发专用路线；若全部不命中，React Native + Expo 是常规商业 App 的均衡默认。

Presentation rule: 顶部标题说明本图的选型用途与比较维度；具体建议位于矩阵之后、来源之前。

## Argument and evidence map

| ID | Claim or criterion | Exact evidence | Visual encoding | Annotation |
|---|---|---|---|---|
| C1 | RN + Expo 是常规商业 App 默认 | S1 | 唯一橙色行与决策单元 | 无特殊约束 |
| C2 | Flutter 由统一自绘 UI 触发 | S2 | 运行机制微图 | Dart → Impeller |
| C3 | KMP 由原生纵深 / Kotlin 资产触发 | S3 | 运行机制微图 | 共享逻辑 → 原生 UI |
| C4 | uni-app / Taro 由中国小程序渠道触发 | S4 | 约束标签 | 中国多端 |
| C5 | Capacitor 由既有 Web 资产触发 | S5 | 约束标签 | Web 复用 |

## Evidence ledger

- Evidence ID: S1
  - Supports claim: C1
  - Exact source: “Using React Native frameworks, such as Expo, is now the recommended approach to create new apps.”
  - Location: https://reactnative.dev/blog/2024/06/25/use-a-framework-to-build-react-native-apps
  - Type: fact + interpretation
  - Unit / period: 当前官方建议
  - Caveat: 默认推荐仍需检查原生 SDK、最低系统版本和库兼容。
- Evidence ID: S2
  - Supports claim: C2
  - Exact source: Flutter bypasses system UI widget libraries in favor of its own widget set and uses Impeller.
  - Location: https://docs.flutter.dev/resources/architectural-overview
  - Type: fact + interpretation
  - Unit / period: 当前架构
  - Caveat: “适合自绘 UI”是从架构推导的场景判断。
- Evidence ID: S3
  - Supports claim: C3
  - Exact source: “Share a UI with Compose Multiplatform or keep it native.”
  - Location: https://kotlinlang.org/docs/multiplatform.html
  - Type: fact + interpretation
  - Unit / period: 当前能力
  - Caveat: 共享边界依项目架构而定。
- Evidence ID: S4
  - Supports claim: C4
  - Exact source: “开发者编写一套代码，可发布到 iOS、Android、鸿蒙 Next、Web……以及各种小程序。”
  - Location: https://uniapp.dcloud.net.cn/
  - Type: fact + interpretation
  - Unit / period: 当前平台范围
  - Caveat: 多端覆盖不代表无需差异适配。
- Evidence ID: S5
  - Supports claim: C5
  - Exact source: 现有 Web 产品快速封装成 App → Capacitor。
  - Location: preserved source.md
  - Type: interpretation
  - Unit / period: 场景判断
  - Caveat: 需要按项目验证重交互和原生能力边界。

## Assumptions and gaps

- 没有统一测试口径的性能、成本或代码复用率，不做数值排名。
- “默认 / 优先”均是场景适配建议，不是产品级最终定案。

## Exhibit specification

- Primary relationship: compare / decide
- Template: comparison-matrix
- Evidence mode: qualitative
- Required encodings: position, color, connection
- Direct annotations: 运行机制与决策规则
- Decision marker: RN + Expo 默认行
- Source-reference mapping: S1–S5

## Copy map

- Figure label: Exhibit 01 · 跨端选型决策矩阵
- Display title: 移动端跨平台技术选型指南：渠道、体验与团队约束对比
- Tail recommendation: 先按四类特殊约束分流；均不命中时，React Native + Expo 是均衡默认。
- Deck: 定性同维比较说明
- Visual labels: 路线、触发约束、体验机制、可复用资产、主要代价、决策含义
- Source / note: S1–S5，截至 2026-07

## Deliberate omissions

- 性能跑分、代码复用率、价格和二级库。
- Expo Go 的开发预览边界，避免出现第二条故事。

## Human review

- [x] Display title explains the infographic's subject and comparison job.
- [x] Recommendation appears after the matrix and before the source footer.
- [x] Title and recommendation play different roles.
- [x] Matrix encodes aligned differences rather than paragraphs in cards.
- [x] Color has one meaning: default path.
- [x] Every row maps to S1–S5.
- [x] Full-size and thumbnail review completed.
