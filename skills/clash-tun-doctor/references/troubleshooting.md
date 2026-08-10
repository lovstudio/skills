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
