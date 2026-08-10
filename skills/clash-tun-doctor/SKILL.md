---
name: sgc-clash-tun-doctor
description: >
  Diagnose and repair application connectivity failures caused by Clash Verge
  Rev TUN routing, rule precedence, stale runtime state, proxy timeouts, or
  unusable IPv6 paths. Trigger for symptoms such as WeChat images failing to
  send, Moments images loading slowly, an app hanging after TUN is enabled, or
  requests unexpectedly matching DIRECT/proxy rules. Also trigger when the user
  mentions "Clash TUN 排障", "微信图片发不出去", "朋友圈图片加载慢",
  "修复微信 TUN 网络", or "diagnose Clash TUN app connectivity".
license: MIT
metadata:
  author: lovstudio
  version: "0.2.0"
  tags: clash mihomo tun network diagnostics wechat macos
---

# Clash TUN Doctor

Evidence-first diagnosis and reversible repair for application networking
failures behind Clash Verge Rev TUN mode.

## When to Use

- An application works without TUN but fails, stalls, or loses media with TUN.
- WeChat text works while image uploads or Moments images fail.
- A rule change makes the symptom worse or the app remains stuck on Loading.
- The subscription says `ipv6: false`, but runtime traffic still uses IPv6.
- Clash logs contain `no route to host`, `context deadline exceeded`, or an
  unexpected rule/strategy for the affected process.

Do not use this skill for generic subscription acquisition, node purchasing,
or bypassing organizational network policy.

## Workflow (MANDATORY)

### Step 0: Resolve the skill and Clash data directories

Resolve `SKILL_DIR` from the installed skill context. For manual execution:

```bash
export SKILL_DIR="/path/to/sgc-clash-tun-doctor"
```

The CLI resolves the Clash Verge Rev data directory in this order:

1. `--data-dir`
2. `LOVSTUDIO_CLASH_TUN_DOCTOR_DATA_DIR`
3. macOS Clash Verge Rev default under `~/Library/Application Support/`

Never hard-code a user's home directory.

### Step 1: Diagnose before proposing a rule

Run the read-only command first:

```bash
python3 "$SKILL_DIR/scripts/clash_tun_doctor.py" diagnose --app wechat
```

Report concrete evidence from all available layers:

- App-level `config.yaml` overrides.
- Generated `clash-verge.yaml` top-level and DNS IPv6 values.
- Runtime `/configs`, `/rules`, and `/connections` through Mihomo's Unix socket.
- Recent service-log failures for the target application.

Treat screenshots and runtime state as truth. A rule saying `DIRECT` does not
prove the connection succeeded.

### Step 2: Choose the narrowest repair

Use `references/troubleshooting.md` to map evidence to a repair. For the proven
WeChat pattern, use the built-in repair:

```bash
python3 "$SKILL_DIR/scripts/clash_tun_doctor.py" fix-wechat
```

This is a dry run. It previews:

- Direct rules for the WeChat processes and media domains.
- Disabling the app-level IPv6 override that can supersede subscription and
  extension settings.
- The exact files that would be backed up and changed.

Do not route the whole application through a proxy merely because direct media
failed. First check proxy health and IPv6 errors; a proxy timeout can turn one
failed image into a fully stuck application.

For a browser site or application with multiple dependency hosts, generate one
evidence-backed DIRECT list instead of adding domains one by one:

```bash
python3 "$SKILL_DIR/scripts/clash_tun_doctor.py" direct-list \
  --app miracleplus \
  --host apply.miracleplus.com \
  --output ./miracleplus-direct.yaml
```

The command reads active connections and recent rotated service logs, deduplicates
hostnames, and includes only:

- Hosts explicitly supplied with `--host`.
- Hosts previously observed through a non-DIRECT route.
- Hosts already maintained as explicit DIRECT rules.

Hosts observed only through a healthy DIRECT route are reported as ignored
instead of bloating the explicit list.

### Step 3: Apply only with user authorization

For a DIRECT list, preview first, then persist and hot-load it:

```bash
python3 "$SKILL_DIR/scripts/clash_tun_doctor.py" direct-list \
  --app miracleplus \
  --host apply.miracleplus.com \
  --apply
```

This path must merge with existing `prepend` rules, create a timestamped backup,
update the generated config, hot-load Mihomo through its Unix socket, and verify
every listed host as an exact `DOMAIN -> DIRECT` runtime rule. Keep Clash Verge
running throughout this rule-only flow.

For the specialized WeChat IPv6 repair, run:

```bash
python3 "$SKILL_DIR/scripts/clash_tun_doctor.py" fix-wechat --apply
```

The command must:

1. Stop Clash Verge before editing its generated global settings.
2. Create a timestamped backup and manifest.
3. Set the global IPv6 override to `false`.
4. Prepend persistent WeChat `DIRECT` rules in the current profile's rule file.
5. Restart Clash Verge and verify final/runtime state.

If verification fails, report the backup path and do not claim success.

### Step 4: Restart the affected application and verify the user path

Close stale connections or restart the affected application. Re-run diagnosis:

```bash
python3 "$SKILL_DIR/scripts/clash_tun_doctor.py" diagnose --app wechat --json
```

For the WeChat IPv6 failure, success requires all of the following:

- Runtime `ipv6` is `false`.
- WeChat rules resolve to `DIRECT`.
- New WeChat destinations are IPv4.
- New logs no longer show WeChat `no route to host` errors.
- The user can send an image and load Moments images.

### Step 5: Roll back when needed

```bash
python3 "$SKILL_DIR/scripts/clash_tun_doctor.py" rollback --apply
```

Rollback restores the newest backup by default. Never delete backups
automatically.

## CLI Reference

| Command / option | Default | Description |
|---|---|---|
| `diagnose` | — | Read configuration, runtime state, connections, and logs. |
| `direct-list` | — | Discover, export, or apply an evidence-backed DIRECT host list. |
| `fix-wechat` | dry run | Preview or apply the proven WeChat repair. |
| `rollback` | dry run | Preview or restore the latest repair backup. |
| `--data-dir PATH` | auto | Clash Verge Rev application data directory. |
| `--socket PATH` | `<data-dir>/mihomo.sock` fallback | Mihomo controller Unix socket; standard `/tmp/verge/verge-mihomo.sock` is auto-detected. |
| `--app NAME` | `wechat` | Application filter used by diagnosis. |
| `--host HOST` | — | Seed an exact host in a DIRECT list; repeatable. |
| `--output PATH` | — | Save a Mihomo classical rule-provider YAML list. |
| `--log-limit N` | `4000` | Recent lines inspected in each rotated service log. |
| `--apply` | false | Authorize filesystem changes and restart/restore actions. |
| `--no-reload` | false | Persist a DIRECT list without runtime hot-load. |
| `--no-restart` | false | Apply changes without restarting Clash Verge. |
| `--json` | false | Emit machine-readable diagnosis output. |

## Dependencies

Python 3.8+ standard library only.
