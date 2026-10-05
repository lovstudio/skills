# Why IPRoyal Needs a Carrier, and Troubleshooting

## What IPRoyal ISP is

An IPRoyal ISP order is one static residential IPv4 address exposed as a proxy
endpoint with username/password (or IP whitelist) authentication. Defaults are
`12323` for HTTP and `12324` for SOCKS5; both can be changed in the dashboard
"Port" section. IPRoyal's help center states that only Residential proxies accept
HTTPS/TLS for the client-to-proxy hop; ISP and Datacenter proxies accept HTTP or
SOCKS5 only, and no VPN or WireGuard access is offered.

Sources:
- https://help.iproyal.com/en/articles/7222799-which-internet-protocols-does-iproyal-support
- https://help.iproyal.com/en/articles/7955587-how-to-use-isp-proxies
- https://iproyal.com/acceptable-use-policy/ (no client-country restriction is stated)

## Observed behaviour from mainland China (2026-10-05)

Measured from a mainland network, bypassing Clash TUN, against one IPRoyal ISP
endpoint:

| Path | Result |
| --- | --- |
| HTTP CONNECT to blocked sites (google, chatgpt, youtube) | `Connection reset by peer` — the plaintext CONNECT host is visible to the GFW |
| Any request right after such a reset | TCP connect to the proxy port itself times out for roughly 90 seconds (residual blocking of client IP + proxy IP:port) |
| Unblocked sites (ipify, Cloudflare trace) | 30–50% refused by the proxy: SOCKS5 reply `0x02 not allowed by ruleset` or HTTP `403` |
| TLS handshake to 12323 / 12324 | rejected — the endpoint does not speak TLS |
| Same endpoint chained through RayLink TCP | 12/12 success, exit IP equals the IPRoyal address |

The refusal mechanism is not documented by IPRoyal; treat it as observed
behaviour, not policy. The practical conclusion holds either way: from the
mainland, the endpoint is only stable behind an encrypted carrier.

## Why RayLink and not any airport

`dialer-proxy` only needs a carrier that can open TCP to the IPRoyal port. A
RayLink server is the user's own VPS and relays any port. Many commercial
airports refuse egress to high or proxy-like ports: one tested airport allowed
80/8080/8443/2053/9000 but refused 1080, 3128 and everything from 10000 up,
including 12323/12324, on all 68 nodes. Moving the IPRoyal port to an allowed
value in the dashboard makes such an airport usable as a carrier; this Skill
then works with `--carrier <that airport group>` after the port is updated.

## How the managed block works

Clash Verge Rev (checked v2.0.0, v2.2.3, v2.5.7) builds a profile in this
order: rules/proxies/groups enhancements, then the profile merge, then the
profile script. The managed block runs last, so it:

1. puts one `IPRoyal ISP` proxy first in `proxies`, replacing any same-named
   entry, with `dialer-proxy` set to the carrier group;
2. removes the ISP from every other group (Clash Verge copies entries added via
   the proxies enhancement into the first group);
3. adds `IPRoyal 出口` (select → `IPRoyal ISP`) to the exposed groups — first in
   the `--select` groups, last elsewhere — and never to groups reachable from the
   carrier, which would loop;
4. appends the `IPRoyal 出口` group.

## Troubleshooting

| Symptom | Cause | Action |
| --- | --- | --- |
| `chain_delay_ms` is null | Carrier group is down on this network | Test `TCP 稳定` in Clash Verge; if every RayLink node times out, the network blocks RayLink (next row) |
| All RayLink nodes time out on some merchant Wi-Fi | Every RayLink protocol sits on one IP with default ports 8443–8448/9443 (RayLink `protocol-catalog.js`); venue firewalls often allow only 80/443 | Server side: give RayLink a TCP 443 entry on a separate IP/host. Client side: switch networks or carriers; IPRoyal cannot be reached until a carrier works |
| `trace_ip` is not the IPRoyal IP but the delay works | `AI 网站代理` is not on `IPRoyal 出口`, or the AI domain is routed elsewhere | Select `IPRoyal 出口` in `AI 网站代理`, or re-run apply with `--restart` |
| Clash Verge shows a script error after restart | The custom script was wrapped and the original `main` throws, or a manual edit broke the block | `rollback --apply --restart`, then re-apply |
| Selection reverts after restart | `profiles.yaml` still stores an older choice | Select `IPRoyal 出口` once in the Clash Verge UI; it persists |
| `superseded_seq_definitions` listed in detect | Older hand-made IPRoyal entries in the proxies/groups enhancements | Harmless (the block overrides them); remove them in the Clash Verge editor for clarity |
