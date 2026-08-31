---
name: lov-create-qrcode
description: >
  将网址、文本或任意 UTF-8 内容生成可扫码验证的二维码 PNG，默认只输出码本体，并复用个人配色、圆角、纠错与海报偏好；适用于“生成二维码”“按我的偏好做 QR code”和 “create a QR code”。
license: MIT
compatibility: "Portable Agent Skills format. Python 3.10+, qrcode 7.4+ and Pillow 9+; OpenCV is optional for scan verification."
allowed-tools:
  - Bash
  - Read
depends_on:
  - lov-branding-consistency
metadata:
  author: LovStudio
  version: "0.1.1"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  tags:
    - qrcode
    - image
    - branding
    - profile
    - local-first
---

# lov-create-qrcode

把一段内容确定性地生成二维码或按需生成 Warm Academic 海报 PNG。默认只输出二维码
本体，不加 header、footer、标题或明文；配色、码点、尺寸、纠错和海报选项可由当前
请求或共享 Profile 覆盖。

## Triggers

### Activate when

- 用户说“把这个链接生成二维码”“按我的偏好做一个 QR code”“生成可扫码的二维码海报”。
- 用户要把文本、网址、Wi-Fi 配置或其他 UTF-8 内容编码成 PNG 二维码。
- The user asks to “create a QR code”, “make a branded QR poster”, or “use my saved QR preferences”.

### Do not activate when

- 用户要识别、反解或批量提取现有二维码内容；使用二维码识别能力。
- 用户要装饰一张已有图片，但不需要生成二维码；交给 `lov-image-decorator`。
- 用户要生成插画、Logo 或改动二维码所指向的网页；交给对应图像或工程能力。

## User Profile (cross-session)

每次运行先读取 `skill.yaml` 和共享 `user-profile/v1`。按当前请求、项目上下文、
`skills.lov-create-qrcode.records`、共享 Preferences、品牌 Profile、安全默认值的顺序
解析配置。具体字段与允许值见 `references/style-contract.md`。

只有用户直接声明的长期偏好才通过 `scripts/profile_store.py record --confirm` 保存；
推断自品牌资产、历史产物或当前项目的值只用于本次任务。不得保存二维码载荷、Wi-Fi
密码、token 或其他秘密。

## Skill Group Composition

运行前读取 `references/skill-composition.md`。相邻 Skills 只通过图片、Logo 或已校验的
本地文件交接，不构成隐藏运行依赖。

## Workflow (MANDATORY)

### Step 0: Resolve root, dependencies, and preferences

1. 从当前 Skill 上下文解析 `SKILL_DIR`，确认下列资源存在：
   - `$SKILL_DIR/scripts/create_qrcode.py`
   - `$SKILL_DIR/scripts/profile_store.py`
   - `$SKILL_DIR/references/style-contract.md`
   - `$SKILL_DIR/references/skill-composition.md`
2. 读取 `skill.yaml` 与 Profile；不得把 Profile 中的私有路径或载荷写进 Skill 真源。
3. 检查 Python、`qrcode` 与 Pillow。用户要求扫码回读时还要检查 OpenCV。

### Step 1: Resolve the payload and visible output

- 保留用户提供内容的 UTF-8 字节，不擅自补协议、改大小写、去查询参数或缩短网址。
- 私密载荷优先通过 stdin 或输入文件传入，避免写进 shell history。
- 未指定样式时使用安全默认：`rounded`、`classic`、M 级纠错、4 modules quiet zone。
- 默认只生成二维码方图，不添加 header、footer、标题、说明、边框海报或载荷明文。
- 只有用户明确需要海报、标题或说明时启用 `--poster`；只有用户明确允许显示原始内容
  时启用 `--show-data`。不能因为品牌 Profile 存在名称就自行切换成海报。
- 使用 Logo 时要求 H 级纠错，且 Logo 必须是用户有权使用的本地图片。

### Step 2: Generate through the deterministic CLI

普通二维码：

```bash
printf '%s' 'https://example.com' | python3 "$SKILL_DIR/scripts/create_qrcode.py" \
  --stdin --output ./qrcode.png --json
```

按 Profile 生成 Warm Academic 海报：

```bash
printf '%s' 'https://example.com' | python3 "$SKILL_DIR/scripts/create_qrcode.py" \
  --stdin --poster --title '扫码访问' --show-data \
  --output ./qrcode-poster.png --verify scan --json
```

当前请求中的 flag 始终覆盖 Profile。需要完全忽略 Profile 时使用 `--no-profile`。

### Step 3: Verify the actual artifact

1. 回读 JSON，确认绝对输出路径、PNG 尺寸、字节数、SHA-256、载荷字节数和载荷摘要。
2. 至少完成结构校验；对公开交付、打印、Logo 或自定义低对比度样式使用
   `--verify scan`，确认解码内容与输入逐字节一致。
3. 检查 quiet zone 至少 4 modules、前景比背景更暗、图像没有被拉伸或覆盖。
4. 海报需视觉检查标题、正文披露、留白与移动端可读性；不得把
   `verification=structural` 写成已扫码验证。

## Output contract

- 默认输出一个宽高等于 `size` 的纯二维码 PNG；不包含 header、footer 或海报包装。
- 只有显式 `--poster` 才输出海报版；只有显式 `--force` 才允许覆盖精确目标。
- `--json` 返回输出路径、尺寸、样式、纠错级别、验证模式、载荷长度与摘要，不回显载荷。
- 失败时不留下部分文件，并返回可诊断错误；扫码失败不能降级为成功。

## Dependencies

- Python 3.10+
- `qrcode` 7.4+ 与 Pillow 9+
- OpenCV Python 可选，仅用于真实扫码回读
- 不需要网络、浏览器、凭据或外部 sibling Skill

## Runtime context (shared)

字段解析顺序为当前请求、项目上下文、Skill 记录、共享 Preferences、品牌 Profile、
安全默认值。直接声明的长期偏好才写入 Profile，并在结果中报告保存路径。
