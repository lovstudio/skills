# lov-skill-add-case

![Version](https://img.shields.io/badge/version-0.2.0-CC785C)

把一次已获用户明确认可的 Skill 结果，整理成脱敏、可验证的案例，安全写入
目标 Skill，并在目标已公开时同步到 LovStudio 官网后回读验证。

## 本地安装

推荐使用共享安装层：

```bash
ln -s "/path/to/skill-add-case-skill" "$HOME/.agents/skills/lov-skill-add-case"
ln -s "../../.agents/skills/lov-skill-add-case" "$HOME/.codex/skills/lov-skill-add-case"
```

## 使用

在另一个 Skill 产出结果后，用户明确确认满意：

> 这个结果不错，用 skill-add-case 加到 lov-professional-infographic 的案例，并同步官网。

Skill 会收集真实 Input → Prompt → Output、验收与隐私说明，先 dry-run，再原子
更新 `cases/cases.json`，验证目标源，最后只对已公开目标执行 case-only 官网同步。

英文触发示例：

> Add this accepted result as a skill case and publish the case to the LovStudio page.

如果目标仍是本地 Skill，结果会明确停在 `local`，不会把“已写入本地”说成
“官网已同步”。

### 确定性命令

```bash
python3 scripts/add_case.py /path/to/target-skill --case /tmp/case.json --dry-run
python3 scripts/add_case.py /path/to/target-skill --case /tmp/case.json

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
- Git、GitHub 与网络仅用于公开同步

## License

MIT
