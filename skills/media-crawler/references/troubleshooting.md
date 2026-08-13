# Troubleshooting

Every CLI failure includes a stable `code` and `context_id`.

| Code | Meaning | Recovery |
| --- | --- | --- |
| `authorization_required` | Video号 public preview returned metadata but no media URL. | Run `authorize_yuanbao.py --test-url URL`, then retry. |
| `authorization_failed` | Yuanbao Cookie is stale or the parse API rejected it. | Clear/re-run authorization; do not expose the Cookie in chat or logs. |
| `resolver_failed` | Custom/public resolver or platform API failed. | Retry direct authorization, check URL expiry, or provide a custom Worker. |
| `unsupported_url` | The host is outside the supported matrix and is not a direct media URL. | Use the platform-specific downloader or add a reviewed adapter. |
| `mediacrawler_missing` | No verified upstream checkout exists. | Run `setup-mediacrawler --accept-noncommercial-license`. |
| `mediacrawler_failed` | Upstream process exited unsuccessfully or produced no media. | Copy the diagnostic command/output, verify login, and inspect the upstream data directory. |
| `download_failed` | aria2/curl could not complete the transfer. | Retry the same URL and output path to reuse `.part` state. |
| `verification_failed` | Downloaded response is empty, truncated or not a media container. | Keep the report, remove only the exact invalid payload after review, and re-resolve an unexpired URL. |

The JSON report never includes cookies, tokens or the full signed CDN query string. Diagnostic URLs are reduced to scheme, host and path.
