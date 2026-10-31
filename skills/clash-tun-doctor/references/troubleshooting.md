# Clash TUN Troubleshooting Map

Use evidence from the final generated configuration, runtime API, active
connections, and recent logs. Source subscription settings alone are not proof.

| Evidence | Likely cause | Preferred action |
|---|---|---|
| App works without TUN; media fails; IPv6 destination reports `no route to host` | Clash app-level IPv6 override is enabled without a usable IPv6 route | Disable IPv6 at the highest-precedence app config and verify both top-level and DNS runtime values |
| App becomes fully stuck only after a process-wide proxy rule | Selected node is unavailable or incompatible | Remove the broad proxy rule, restore direct behavior, then inspect node timeout logs |
| `context deadline exceeded` names the proxy server | Proxy transport/node failure | Switch/test the node; do not blame the target application |
| Rule says `DIRECT`, but request still fails | TUN still owns routing and may select an unusable IP family/path | Inspect destination IP, network family, and dial error |
| Subscription says `ipv6: false`, runtime says `true` | Higher-precedence Clash Verge global config overrides the profile | Inspect the application `config.yaml` and generated `clash-verge.yaml` |
| YAML editor reports `did not find expected key` | Invalid list indentation or malformed merge syntax | Restore the last valid file, then use a structured prepend list and parse before reload |
| A GFW-blocked domain (`chatgpt.com`, `openai.com`) fails with `context deadline exceeded` or connection reset through a `type: http` "本机直连" residential node that has no `dialer-proxy`; other domains work through the same node, and the same exit works once chained behind an encrypted `dialer-proxy` relay | The HTTP proxy's `CONNECT host:443` request crosses the border in plaintext, so the GFW injects RST or drops packets by host | Confirm with an unauthenticated CONNECT from the physical interface (see below), then select the node variant with an encrypted `dialer-proxy` relay; do not rotate the exit IP or add DIRECT rules |
| `diagnose` prints `Recent logs: UNAVAILABLE` with `Permission denied` on `clash-verge-service/users/<uid>/logs` | Service-mode core logs are root-only; the counts are unknown, not zero | Rerun with `--live-logs 15` while reproducing the failure, or let the user run the printed `sudo tail` command |
| `diagnose` exits with `Cannot reach the Mihomo controller Unix socket` | Core not running, or its controller socket is somewhere unexpected | Read only the socket path from the running core (`pgrep -lf mihomo \| grep -o -- '-ext-ctl-unix [^ ]*'`; the full command line may carry `-secret`) and pass it with `--socket`; never report runtime state as healthy without it |
| `direct-list --apply` reports `HTTP 400: path is not subpath of home directory or SAFE_PATHS ... allowed paths: [.../clash-verge-service/users/<uid>/runtime]` | The owner-scoped service core reloads config paths only from its root-owned runtime directory or `SAFE_PATHS`; the user-writable data-dir `clash-verge.yaml` is outside both | Since v0.6.0 the skill hot-loads service-mode cores by `payload` with `external-controller-unix` pinned to the live socket, and retries any SAFE_PATHS refusal that way. Older copies saved the rules without loading them: upgrade, then rerun the same `direct-list --apply` (idempotent). Never copy configs into the runtime directory or relaunch the core with a wider `SAFE_PATHS` |
| `direct-list --apply` exits 2 with `Group choices changed` | The forced reload rebuilt the proxy groups; Mihomo restores Selector picks and URLTest/Fallback pins from its cache only when `profile.store-selected` is `true` | The new rules are already active: re-select or re-pin the listed groups in Clash Verge and check `profile.store-selected` in the generated `clash-verge.yaml` before the next hot-load. An unpinned URLTest/Fallback moving to another node is normal and is not reported |
| Right after a hot-load, `/rules` has the new rule but the app's connections still show the old chain | Connections opened before the reload keep the chain they started with until they close | Compare `/connections` ids before and after the reload and judge only the new ones, or restart the app; old connections are not evidence that the rule failed |

## Plaintext HTTP proxy blocked by CONNECT host

An HTTP proxy node without `dialer-proxy` sends `CONNECT chatgpt.com:443` to the
proxy server in cleartext. TLS only starts after the tunnel is established, so
the destination host is visible on the cross-border path even though the
exit IP itself is healthy.

Test from the physical interface so the TUN does not capture the probe, and
deliberately omit credentials: a `407` proves the CONNECT reached the proxy.

```bash
IFACE="$(route -n get default | awk '/interface:/{print $2}')"  # e.g. en0
for host in www.apple.com chatgpt.com; do
  curl --interface "$IFACE" -sS -o /dev/null --max-time 10 \
    -w "$host CONNECT=%{http_connect}\n" \
    -x "http://PROXY_IP:PROXY_PORT" "https://$host/"
done
```

curl exits non-zero in every case (`56` even for `407`), so read the
`CONNECT=` code and the error text instead of the exit status:

- Control host prints `CONNECT tunnel failed, response 407` / `CONNECT=407`;
  blocked host prints `Connection reset by peer` or `timed out` with
  `CONNECT=000`: host-based interference on the plaintext CONNECT. Use the
  chained node with an encrypted `dialer-proxy`.
- Both hosts return `407`: the CONNECT path is clean; look at authentication,
  the proxy's own upstream, or the Clash rule/strategy instead.
- Both hosts fail with `CONNECT=000`: the proxy server or its port is
  unreachable.

`PROXY_IP` must be a literal IP. Under fake-ip, the system resolver returns
`198.18.x.x` for a domain, so resolve a domain `server` outside Clash first.
Never paste the node's username or password into the probe or the report.

## Evidence-backed DIRECT list

For a site whose page, CDN, API, or telemetry hosts split across multiple Clash
rules, collect the list from runtime connections and recent rotated service
logs:

```bash
python3 scripts/clash_tun_doctor.py direct-list \
  --app TARGET_FILTER \
  --host PRIMARY_HOST
```

The generated list keeps explicit hosts and hosts observed through a non-DIRECT
route. Evidence seen only through `DIRECT` stays outside the explicit list.
Review `missing_rules`, then add `--apply` to merge, back up, hot-load, and
verify the rules without quitting Clash Verge. A refused hot-load restores the
files and prints Mihomo's own error; service-mode cores are always hot-loaded
by payload (see the SAFE_PATHS row above).

## Proven WeChat repair

Keep WeChat direct and disable unusable IPv6 resolution/routing:

```yaml
prepend:
  - "PROCESS-NAME,WeChat,DIRECT"
  - "PROCESS-NAME,WeChatAppEx,DIRECT"
  - "PROCESS-NAME,WeChatAppEx Helper,DIRECT"
  - "DOMAIN-SUFFIX,weixin.qq.com,DIRECT"
  - "DOMAIN-SUFFIX,wechat.com,DIRECT"
  - "DOMAIN-SUFFIX,servicewechat.com,DIRECT"
  - "DOMAIN-SUFFIX,qpic.cn,DIRECT"
  - "DOMAIN-SUFFIX,qlogo.cn,DIRECT"
```

The actual rule target is deliberately `DIRECT`. Routing all of WeChat through
a proxy is not a generic fix and can make session/image loading worse.
