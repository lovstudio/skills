# lov-skill-add-case

![Version](https://img.shields.io/badge/version-0.4.1-CC785C)

把一次已确认满意的 Skill 结果整理成官网案例。用户可以导入网页后手动发布，
也可以授权 Agent 直接投稿；普通 LovStudio 账号即可使用，无需 GitHub 权限。

## 安装

```bash
npx skills add lov-skill-add-case -g -y
```

## 使用

> 这个结果不错，用 skill-add-case 加到这个 Skill 的案例，并同步官网。

默认整理真实 Input → Prompt → Output、最终成品图、验收和脱敏说明，生成可导入
官网的 JSON。用户登录后预览并确认发布。免费与付费 Skill 均可投稿，目标必须
已经收录且支持官网写入。

案例拥有独立详情页。完整会话不是必填项，可自愿附上本人已有的公开 Session；
当前投稿接口不接受付费 Session。

## 命令

`CATALOG_ID` 使用官网 `/skills/<id>` 中的精确 ID，不要求本地 Skill 源码。

```bash
# 只读确认目标和投稿条件
python3 scripts/submit_case.py contract CATALOG_ID

# 离线生成导入文件；视觉作品可重复传 --image，第一张作为封面
python3 scripts/submit_case.py prepare CATALOG_ID \
  --case case.json --image final.png --output submission.json

# 仅在要求 Agent 直接提交时：设备登录和预检，不发布
python3 scripts/submit_case.py check CATALOG_ID --submission submission.json

# 展示完整预览，用户同意后，使用预检返回的 payloadFingerprint
python3 scripts/submit_case.py publish CATALOG_ID \
  --submission submission.json --confirm REVIEWED_PAYLOAD_FINGERPRINT
```

文字案例省略 `--image`；已有公开图片可直接填入案例的 `cover` / `gallery`。
最多 4 张 PNG、JPEG 或 WebP，每张 1 MiB，总计 2 MiB，请求最多 3 MiB。
更大的图片可交给网页编辑器优化。

直接提交自带 LovStudio 登录模块，与 `lov-share-session` 共用登录缓存和授权契约，
不读取或上传转录。全新安装无需额外安装登录依赖；也可通过 `--share-session-script`
或 `LOV_SHARE_SESSION_SKILL_DIR` 显式指定已有实现。用户无需复制凭据给 Agent。

历史 `consent` 标记不会自动生效。发布必须确认当前内容指纹；修改文字、图片
或 Session 链接后需要重新预览。失败时保留同一个案例 ID 和文件重试。

## 数据与状态

- [案例字段与状态](references/case-contract.md)
- [能力组合](references/skill-composition.md)
- [维护者付费 Session 路径](references/maintainer-paid-cases.md)：保留旧命令，需要
  目标仓库权限和独立授权，不会作为普通投稿的自动回退。

`prepared` 表示已生成文件，`validated` 表示官网预检通过，`published` 表示来源
提交成功。只有回读公开数据、页面、图片及可选 Session 后才报告 `live-verified`。

## Profile

`skill.yaml` 声明 `user-profile/v1`。长期偏好只在用户直接说明并确认后记录；
案例正文、凭据和私有路径不会进入 Profile。

## 验证与依赖

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 scripts/validate_skill.py .
```

Python 3.10+；准备 JSON 和直接投稿均只需标准库，投稿需网络与 LovStudio 登录。
源码校验另需 PyYAML。`lov-share-session`、Git、GitHub 与 `lov-skill-publisher`
仅用于维护者路径。

## License

MIT
