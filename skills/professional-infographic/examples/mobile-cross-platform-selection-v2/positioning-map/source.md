# 对话来源：移动端跨端框架的选型最佳实践

## 用户主题

移动端跨端框架的选型最佳实践。

## 对话结论一：总体选型

现在综合最好的选择是：**React Native + Expo**。

如果今天从零做一款面向 iOS、Android 的商业 App，我会默认选它：

- TypeScript / React 生态成熟，开发者与 AI 生成代码的支持最好。
- 使用原生 UI 组件，平台体验比较自然。
- 新架构已经默认启用，原生调用不再依赖旧 Bridge，性能足够覆盖绝大多数产品。[React Native 新架构](https://reactnative.dev/blog/2024/10/23/the-new-architecture-is-here)
- Expo 已是 React Native 官方推荐的生产级框架，原生模块、构建、调试、热更新和应用商店发布链路都比较完整。[官方推荐说明](https://reactnative.dev/blog/2024/06/25/use-a-framework-to-build-react-native-apps)

按场景选择：

| 场景 | 最佳选择 |
|---|---|
| 创业产品、AI App、社交、工具、内容应用 | **React Native + Expo** |
| 高度定制视觉、复杂动画、多平台 UI 完全一致 | **Flutter** |
| 已有 Android/Kotlin 团队，强调原生体验和长期工程质量 | **Kotlin Multiplatform** |
| 微信/支付宝/抖音等小程序是核心渠道 | **uni-app** 或 **Taro** |
| 现有 Web 产品快速封装成 App | **Capacitor** |

Flutter 的优势是自带渲染体系和 Impeller，复杂自绘 UI 很稳，但需要引入 Dart，且原生控件混排成本较高。[Flutter 架构](https://docs.flutter.dev/resources/architectural-overview)

Kotlin Multiplatform 更适合重原生项目：既可以只共享业务逻辑、保留 SwiftUI/Compose，也可以共享整套 UI；目前 Android、iOS 和桌面端 Compose UI 都已进入稳定状态。[KMP 平台稳定性](https://kotlinlang.org/docs/multiplatform/supported-platforms.html)

一句话结论：**没有特殊约束就用 React Native + Expo；中国小程序优先则用 uni-app；极重视自绘 UI 选 Flutter；重原生和长期架构选 KMP。**

## 对话结论二：Expo 的生产交付边界

**Expo Go 57 没上架 iOS App Store**，并不代表基于 Expo SDK 57 开发的 App 不能上架。

Expo Go 只是开发预览器，最终用户完全不需要安装它。正式项目应该使用 Development Build；生产项目通过 EAS Build 或本地 Xcode 生成独立、签名的 `.ipa`，经过 TestFlight 和 App Store 审核后由用户直接安装。

开发阶段：

```bash
npx expo install expo-dev-client
eas build --platform ios --profile development
```

生产阶段：

```bash
eas build --platform ios --profile production
eas submit --platform ios
```

参考：

- [Expo iOS 提交流程](https://docs.expo.dev/submit/ios/)
- [Development Build 说明](https://docs.expo.dev/develop/development-builds/introduction/)
- [SDK 57 过渡说明](https://docs.expo.dev/get-started/create-a-project/)
- [Expo SDK 版本要求](https://docs.expo.dev/versions/latest/)

Expo SDK 57 要求 **iOS 16.4+、Xcode 26.4+**。因此，Expo Go 的上架节奏主要影响快速预览；最低系统版本才是更直接的产品覆盖约束。
