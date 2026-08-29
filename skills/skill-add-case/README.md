# lov-skill-add-case

![Version](https://img.shields.io/badge/version-0.2.2-CC785C)

把一次已获用户明确认可的 Skill 结果，整理成公开摘要，并将脱敏后的完整 Session
按目标 Skill 售价的 1/10 上传为付费证据；随后安全写入目标 Skill，并在公开时回读验证。

## 本地安装

标准安装：

```bash
npx skills add lov-skill-add-case -g -y
```

## 使用

在另一个 Skill 产出结果后，用户明确确认满意：

> 这个结果不错，用 skill-add-case 加到 lov-professional-infographic 的案例，并同步官网。

Skill 会收集真实 Input → Prompt → Output、验收与隐私说明，调用
`lov-share-session` 上传付费完整过程，验证服务端权威价格后再原子更新
`cases/cases.json`，最后只对已公开目标执行 case-only 官网同步。

视觉型案例必须把已验收的最终成品放进 `cover`；多张最终成品继续放入
`gallery`。只有文字摘要、没有成品图的视觉案例不会通过新增案例校验。
公开验收还会逐张确认图片已出现在详情页，并返回非空 `image/*` 内容。

英文触发示例：

> Add this accepted result as a skill case and publish the case to the LovStudio page.

如果目标仍是本地 Skill，结果会明确停在 `local`，不会把“已写入本地”说成
“官网已同步”。

### 确定性命令

```bash
python3 scripts/add_case_with_session.py /path/to/target-skill \
  --case /tmp/case.json \
  --share-session-script /path/to/lov-share-session/scripts/share_session.py \
  --dry-run

python3 scripts/add_case_with_session.py /path/to/target-skill \
  --case /tmp/case.json \
  --share-session-script /path/to/lov-share-session/scripts/share_session.py

python3 scripts/verify_public_case.py \
  --cases-url https://raw.githubusercontent.com/org/repo/main/cases/cases.json \
  --page-url https://lovstudio.ai/skills/target-id \
  --case-id accepted-result \
  --fingerprint EXPECTED_SHA256 \
  --marker "Accepted result"
```

案例数据契约见 [`references/case-contract.md`](references/case-contract.md)。

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`。长期工作偏好只在用户直接说明并确认时通过
`scripts/profile_store.py` 写入；案例正文、凭证和私有路径不会进入 Profile。

## 原子组合

- `lov-skill-creator` 是可选上游：它定义标准案例与 Skill Card 契约。
- `lov-share-session` 是必需依赖：它负责会话脱敏、上传和服务端定价。
- `lov-skill-add-case` 拥有案例资格判断、脱敏、去重和本地写入。
- `lov-skill-publisher` 是可选下游：它拥有仓库、目录、缓存与官网 live 状态。

详见 [`references/skill-composition.md`](references/skill-composition.md)。

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.10+
- PyYAML（源 Skill 校验）
- `lov-share-session`
- Git、GitHub 与网络仅用于公开同步

## License

MIT
