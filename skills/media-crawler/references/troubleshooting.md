# Troubleshooting

Every CLI failure includes a stable `code` and `context_id`.

| Code | Meaning | Recovery |
| --- | --- | --- |
| `authorization_required` | Video号 public preview returned metadata but no media URL. | Run `authorize_yuanbao.py --test-url URL`, then retry. The script waits 600 seconds for the QR login by default; pass `--timeout SECONDS` when the user needs longer. |
| `authorization_failed` | The Yuanbao or Channels API returned HTTP 401/403: the stored Cookie is stale. If `--worker-url` or `--allow-public-resolver` was passed, that resolver service was tried as well and also failed; the message names its error code. | Re-run `authorize_yuanbao.py`; do not expose the Cookie in chat or logs. The Keychain entry is overwritten only by a successful authorization. |
| `resolver_unauthorized` | The resolver service itself (`--worker-url` or `--allow-public-resolver`) returned HTTP 401/403. This is its own access control, not the Yuanbao session. The public instance answered `401 {"error":"unauthorized"}` when measured on 2026-11-19; see `platform-matrix.md`. | For a self-hosted Worker, set `LOV_MEDIA_CRAWLER_WORKER_CREDENTIAL` to its access credential and retry with `--worker-url`; if the message says the supplied credential was rejected, the value does not match the Worker's. Otherwise drop the resolver flag and retry so the local Yuanbao authorization or WeChat client capture is used. Re-authorizing Yuanbao does not change a resolver's answer. |
| `invalid_url` | No HTTP(S) link was found in the input, or `LOV_MEDIA_CRAWLER_WORKER_CREDENTIAL` is set while `--worker-url` is plain HTTP on a non-loopback host. | Pass a full link; use an `https://` Worker URL, or unset the credential. |
| `resolver_failed` | The Cookie authenticated but Yuanbao returned no export id (publisher restricts out-of-WeChat parsing or the link is limited), or a resolver/platform API failed for a reason other than 401/403. | Probe another public `sph` link to confirm the channel works; re-authorizing does not help. Otherwise check URL expiry or use WeChat client capture. |
| `wxclient_unavailable` | The local `wx_channels_download` API on `127.0.0.1:2022` is not reachable. | Run `setup-wxclient` once, then have the user start it with `scripts/wxclient.sh start` (admin rights). |
| `wxclient_not_connected` | The downloader runs but no WeChat Channels page is connected to it. | Open any Channels video in the WeChat desktop client and keep it open, then retry. |
| `wxclient_failed` | The client could not return the feed, the task could not be created, or it failed/cancelled. | Check `scripts/wxclient.sh status`, confirm the video plays inside WeChat, and inspect the task with the `next_action` curl. |
| `unsupported_url` | The host is outside the supported matrix and is not a direct media URL. | Use the platform-specific downloader or add a reviewed adapter. |
| `mediacrawler_missing` | No verified upstream checkout exists. | Run `setup-mediacrawler --accept-noncommercial-license`. |
| `mediacrawler_failed` | Upstream process exited unsuccessfully or produced no media. | Copy the diagnostic command/output, verify login, and inspect the upstream data directory. |
| `download_failed` | aria2/curl could not complete the transfer. | Retry the same URL and output path to reuse `.part` state. |
| `verification_failed` | Downloaded response is empty, truncated or not a media container. | Keep the report, remove only the exact invalid payload after review, and re-resolve an unexpired URL. |

The JSON report never includes cookies, tokens or the full signed CDN query string. Diagnostic URLs are reduced to scheme, host and path.
