# 人像大片 · Spectacular Portraits

![version](https://img.shields.io/badge/version-0.1.0-blue)

`lov-spectacular-ps` 把旅行与户外照片修成有环境气势、仍能认出本人的人像。
支持微信头像、风格参考、真实对比图与可复刻 Prompt。无需 Photoshop。

## 用法

上传原图后调用：

```text
$lov-spectacular-ps 修成有气势的微信头像，保留本人和姿态，附对比图与可复刻 Prompt。
```

```text
$lov-spectacular-ps 参考第二张的构图和光影，保留第一张的天气、灯塔和红色外套。
```

```text
Make a cinematic environmental portrait. Keep my identity, clothing and pose.
```

默认保持真实场景；增加云雾、改变地形或替换背景需属于用户明确要求的范围。
申请文书 PS、职业证件照、Riso 插画和仅加图注不属于此 Skill。

## 本地安装

将源码保存在自己的 Skill 源目录，在共享安装位建立 symlink，再让宿主链接共享入口。
以下在源码根目录执行，目标已存在时 `ln` 会拒绝覆盖：

```bash
mkdir -p "$HOME/.agents/skills" "$HOME/.codex/skills"
ln -s "$PWD" "$HOME/.agents/skills/lov-spectacular-ps"
ln -s ../../.agents/skills/lov-spectacular-ps "$HOME/.codex/skills/lov-spectacular-ps"
python3 scripts/validate_skill.py .
```

目录发布后的统一安装命令为 `npx skills add lov-spectacular-ps -g -y`；本版本仅完成本地
创建与安装，尚未验证该远程命令可用，不能将它当成本次安装证据。

## 运行环境与 Profile

需要支持原图查看、原生生成式图像编辑的 Agent。主流程由指令驱动，不绑定固定模型。
Python 3.9+ 和 PyYAML 用于校验；可选对比工具还需 Pillow。不会自动安装全局依赖。
`lov-branding-consistency` 负责创作型说明与标签审校。

每次读取 [skill.yaml](skill.yaml) 的 `user-profile/v1`。可通过 `SKILL_PROFILE_PATH`
指定共享 Profile；见 [Profile 合同](references/user-profile.md)。只保存用户明确声明
的长期偏好，不保存肖像、位置或从单次反馈推断的偏好。

```bash
python3 scripts/profile_store.py read --skill-id lov-spectacular-ps
```

## 对比图

用户要求精确对比且两个真实文件可用时：

```bash
python3 scripts/compare_images.py --before original.jpg --after selected.png \
  --output comparison.png --height 1000
```

两图等高、各自保持比例和完整画面；PNG 不覆盖已有文件。默认不烧录文字，左原图、右成片。
JSON 输出含输入/输出 SHA-256、原始尺寸与面板位置。等高排版会确定性缩放，不声称
与原图逐像素相同。详见 [对比规范](references/comparison.md)。

## 验收与来源

回读全图、脸部、缩略图与圆形裁切，检查身份、服装、姿态、手部、场景与光向。
原图保持不变，重构环境须披露。不要把 Prompt 当成已生成照片。

工作流来自用户提供的[微信头像对话](https://chatgpt.com/share/6ab38700-6d34-83ec-90c9-989ecd2d7f5a)。
真实案例保留输入、执行 Prompt、结果引用与用户确认；本次只核验分享页文字与引用，
未下载或重新验收其中的人像文件，也未重跑图像生成。见 [案例](cases/cases.json)、
[来源边界](references/source-notes.md) 和 [Skill Card](skill-card.md)。

Skill 免费，图像服务费用由宿主或服务商另计；免费和付费渠道均未发布。
