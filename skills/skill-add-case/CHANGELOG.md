# Changelog

## [0.4.1] - 2026-09-07

### Fixed

- 将兼容的 LovStudio 登录模块随包分发，修复全新安装缺少共享依赖的问题
- 无需单独安装 lov-share-session 即可登录和投稿；旧付费上传仍显式依赖它

## [0.4.0] - 2026-09-07

### Added

- 对齐官网账号投稿，支持 JSON 导入与 Agent 直接提交
- 复用 LovStudio 登录，加入服务端预检、内容指纹确认与幂等重试
- 公开 Session 改为可选；旧付费 Session 命令保留为显式维护者路径
- 修正公开案例验收的实际 DOM、图片路径和 Session 检查

## 0.3.0 - 2026-08-29

- Give every case a stable public detail route owned by its case ID.
- Keep parent Skill pages concise and move full public Input → Prompt → Output
  plus paid-session access to the independent case page.
- Extend live verification to the case page without exposing transcript content.

## 0.2.2 - 2026-08-29

- Verify every public `cover` and `gallery` asset returns non-empty image content.
- Require the rendered LovStudio detail page to reference each published case
  image before reporting `live-verified`.

## 0.2.1 - 2026-08-29

- Require every primarily visual accepted case to include its final artifact as
  `cover`, with additional accepted variants in `gallery`.
- Add `evidence.artifact_type` validation so image-producing case workflows fail
  before publication when visual evidence is missing.
- Document public asset hosting for paid or private target repositories.

## 0.2.0 - 2026-08-27

- Add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill.
- Compose `lov-share-session` as a declared dependency for every new case.
- Upload the redacted full conversation as a paid Session priced by the server at
  `ceil(target Skill Credits price / 10)` before mutating the case registry.
- Require structured Session metadata in new cases and verify the unauthenticated
  paywall, title, and Credits price during public readback.
- Keep the case file unchanged when the target Skill is free, unlisted, unpriced,
  or the paid Session upload fails.

## 0.1.0 - 2026-08-23

- Add an explicit user-acceptance gate for case collection.
- Add privacy-safe, duplicate-aware, atomic `cases/cases.json` mutation.
- Add canonical SHA-256 and public raw JSON plus LovStudio page verification.
- Document the optional `lov-skill-publisher` case-only synchronization handoff.
