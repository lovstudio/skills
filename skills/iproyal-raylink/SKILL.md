---
name: lov-iproyal-raylink
description: >
  把 IPRoyal 静态住宅 IP 经 RayLink 加密节点链式接入 Clash Verge，让 AI 网站走固定出口，可验证、可回滚。
  Use for "把 IPRoyal 加入 RayLink", "IPRoyal 直连连不上", "chain IPRoyal behind RayLink".
license: MIT
compatibility: "Clash Verge Rev 2.0+ (mihomo) with a RayLink subscription and an IPRoyal ISP proxy. Python 3.8+ standard library; node optional for a syntax check. Automatic restart on macOS; manual restart on Windows/Linux."
metadata:
  author: lovstudio
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  display_name:
    zh: IPRoyal 链式出口
    en: IPRoyal Chain Exit
  tags:
    - clash-verge
    - mihomo
    - raylink
    - iproyal
    - proxy-chain
---

# IPRoyal 链式出口 · IPRoyal Chain Exit

Attach an IPRoyal ISP (static residential) proxy to a RayLink subscription in
Clash Verge Rev so AI sites leave through the fixed IPRoyal IP, carried by an
encrypted RayLink group. The result is verified on the running core and can be
removed or rolled back.

## Why a chain is required

IPRoyal ISP endpoints only accept plaintext HTTP or SOCKS5 (IPRoyal documents
TLS-to-proxy for Residential products only). Dialed directly from mainland
China, the target host is visible: blocked sites are reset, the proxy port is
then blackholed for about 90 seconds, and IPRoyal itself randomly refuses part
of the connections from a mainland source. Chained through RayLink, the same
endpoint is stable. Details and the original evidence: `references/why-chain.md`.

## Triggers

### Activate when

- “把 IPRoyal 加入 RayLink”“给 RayLink 配上 IPRoyal 出口”“AI 网站走 IPRoyal 固定 IP”
- “IPRoyal 单独做配置连不上 / 间歇性失败，但在 RayLink 里能用”
- "Chain my IPRoyal ISP proxy behind RayLink in Clash Verge."
- "Use IPRoyal as the exit for ChatGPT/Claude on my RayLink profile."

### Do not activate when

- A Clash TUN application failure unrelated to IPRoyal (WeChat images, IPv6,
  DIRECT lists) — use `lov-clash-tun-doctor`.
- Buying proxies, choosing an airport, or bypassing an organization's network
  policy.
- Deploying or operating a RayLink server (adding inbounds, ports, certificates).
- Chaining IPRoyal behind a non-RayLink airport: the CLI supports any carrier
  group via `--carrier`, but most airports refuse to relay to IPRoyal's 1232x
  ports; explain that limit instead of promising it works.

## User Profile (cross-session)

Read the shared `user-profile/v1` scopes declared in `skill.yaml` on every run.
Only non-secret preferences may persist, for example a preferred carrier group or
which groups should lead with the exit, under `skills.lov-iproyal-raylink.records`
via `scripts/profile_store.py record ... --confirm`. **Never persist IPRoyal
credentials** in the Profile; they stay in the user's environment and in the
Clash Verge script file (mode 600). See `references/user-profile.md`.

## Skill Group Composition

Read `references/skill-composition.md`. `lov-clash-tun-doctor` is an optional
downstream diagnostic; no sibling Skill is required.

## Workflow (MANDATORY)

Resolve `SKILL_DIR` from the installed Skill context. All commands are
`python3 "$SKILL_DIR/scripts/iproyal_raylink.py" <command>`.

### Step 1: Detect (read-only)

```bash
python3 "$SKILL_DIR/scripts/iproyal_raylink.py" detect
```

Report from the JSON: the RayLink profile found (`target.uid`, whether it is
`current`), `script_state` (`stock` / `custom` / `managed`), whether the carrier
group (`TCP 稳定`) and exposed groups (`RayLink 代理`, `AI 网站代理`) exist,
`superseded_seq_definitions`, and the controller. If no RayLink profile is
found or several are, ask the user which `--profile` to use.

### Step 2: Collect the IPRoyal proxy without exposing it

Ask the user to put the IPRoyal dashboard string `host:port:username:password`
into an environment variable themselves (or a file), for example
`export IPROYAL_PROXY='...'` in their own terminal, or `--proxy-file`. Default
protocol is HTTP (port 12323); pass `--type socks5` for 12324. Never echo,
log, or repeat the credentials; the CLI prints only `http://***:***@host:port`.

### Step 3: Preview, then apply

```bash
python3 "$SKILL_DIR/scripts/iproyal_raylink.py" apply            # dry run
python3 "$SKILL_DIR/scripts/iproyal_raylink.py" apply --apply --restart
```

- `stock` script: replaced by the managed block.
- `custom` script: the CLI refuses unless `--wrap-existing` (renames the user's
  `main` to `lovUserMain` and runs it first). Tell the user before using it.
- `managed`: the block is updated in place; re-running is idempotent.
- `--select` (default `AI 网站代理`) chooses which groups lead with and are set
  to `IPRoyal 出口`; other `--expose` groups only list it as an option. Use
  `--select "RayLink 代理,AI 网站代理"` only when the user wants all proxied
  traffic on IPRoyal.
- `--restart` (macOS) quits Clash Verge, persists the selection in
  `profiles.yaml`, relaunches, and sets the selection through the controller.
  Without it, or on Windows/Linux, tell the user to restart Clash Verge and
  select `IPRoyal 出口` in `AI 网站代理`.
- If the target profile is not active, nothing reloads; tell the user to
  switch to it first.

Every write creates `backups/lov-iproyal-raylink-<timestamp>/` with a manifest.

### Step 4: Verify on the running core

```bash
python3 "$SKILL_DIR/scripts/iproyal_raylink.py" verify
```

Success requires `pass: true`: the exit group is loaded, the chained delay test
of `IPRoyal ISP` succeeds, and `https://chatgpt.com/cdn-cgi/trace` through the
mixed port returns the IPRoyal IP (`expected_ip`, default the proxy server
address; override with `--expect-ip`). Report the delay, selections, and trace
IP. A `hint` means the chain works but the AI group is not selected.

### Step 5: Remove or roll back when asked

```bash
python3 "$SKILL_DIR/scripts/iproyal_raylink.py" remove --apply
python3 "$SKILL_DIR/scripts/iproyal_raylink.py" rollback --apply --restart
```

`remove` strips the managed block and restores a wrapped `main` byte-for-byte;
`rollback` restores the newest backup. Both default to dry run. Never delete
backups.

## Failure handling

Read `references/why-chain.md` § Troubleshooting for: chain delay fails
(RayLink carrier down or blocked on the current network), trace IP is an
airport IP (AI group not selected), Clash Verge reports a script error, and
merchant Wi-Fi that blocks RayLink's non-standard ports.

## Dependencies

None beyond Python 3.8+. Optional: PyYAML (more tolerant `profiles.yaml`
parsing), node (syntax check before writing).
