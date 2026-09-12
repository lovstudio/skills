# Troubleshooting

Every CLI failure includes a stable `code` and `context_id`.

| Code | Meaning | Recovery |
| --- | --- | --- |
| `authorization_required` | Video号 public preview returned metadata but no media URL. | Run `authorize_yuanbao.py --test-url URL`, then retry. |
| `authorization_failed` | The Yuanbao parse API returned HTTP 401/403: the Cookie is stale or missing. | Re-run `authorize_yuanbao.py`; do not expose the Cookie in chat or logs. |
| `resolver_failed` | The Cookie authenticated but Yuanbao returned no export id (publisher restricts out-of-WeChat parsing or the link is limited), or a resolver/platform API failed. | Probe another public `sph` link to confirm the channel works; re-authorizing does not help. Otherwise check URL expiry or provide a custom Worker. |
| `wxclient_unavailable` | The local `wx_channels_download` API on `127.0.0.1:2022` is not reachable. | Run `setup-wxclient` once, then have the user start it with `scripts/wxclient.sh start` (admin rights). |
| `wxclient_not_connected` | The downloader runs but no WeChat Channels page is connected to it. | Open any Channels video in the WeChat desktop client and keep it open, then retry. |
| `wxclient_failed` | The client could not return the feed, the task could not be created, or it failed/cancelled. | Check `scripts/wxclient.sh status`, confirm the video plays inside WeChat, and inspect the task with the `next_action` curl. |
| `unsupported_url` | The host is outside the supported matrix and is not a direct media URL. | Use the platform-specific downloader or add a reviewed adapter. |
| `mediacrawler_missing` | No verified upstream checkout exists. | Run `setup-mediacrawler --accept-noncommercial-license`. |
| `mediacrawler_failed` | Upstream process exited unsuccessfully or produced no media. | Copy the diagnostic command/output, verify login, and inspect the upstream data directory. |
| `download_failed` | aria2/curl could not complete the transfer. | Retry the same URL and output path to reuse `.part` state. |
| `verification_failed` | Downloaded response is empty, truncated or not a media container. | Keep the report, remove only the exact invalid payload after review, and re-resolve an unexpired URL. |

The JSON report never includes cookies, tokens or the full signed CDN query string. Diagnostic URLs are reduced to scheme, host and path.
