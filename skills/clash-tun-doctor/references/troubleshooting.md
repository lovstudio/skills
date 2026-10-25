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
| `diagnose` exits with `Cannot reach the Mihomo controller Unix socket` | Core not running, or its controller socket is somewhere unexpected | Read only the socket path from the running core (`pgrep -lf mihomo \| grep -o -- '-ext-ctl-unix [^ ]*'`; the full command line may carry `-secret`) and pass it with `--socket`; never report runtime state as healthy without it |

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
verify the rules without quitting Clash Verge.

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
