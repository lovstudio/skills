# Platform Matrix

| Input | Resolver | Login/session | Download path | Notes |
| --- | --- | --- | --- | --- |
| `weixin.qq.com/sph/...` | Tencent Yuanbao + WeChat Channels API | one-time Yuanbao web login | aria2/curl from `finder.video.qq.com` | Public preview alone exposes metadata/cover, not the video stream. |
| `weixin.qq.com/sph/...` (publisher blocks out-of-WeChat parsing) | Local `wx_channels_download` proxy + logged-in WeChat desktop client | WeChat desktop login; proxy started by the user with admin rights | Upstream task API on `127.0.0.1:2022`, files land in the requested output dir | Used when Yuanbao authenticates but returns an empty export id; `--via wxclient` forces it. macOS only for now. |
| Xiaohongshu | MediaCrawler `xhs` detail | QR, cookie or upstream cache | MediaCrawler media saver | Single specified post; comments disabled. |
| Douyin | MediaCrawler `dy` detail | QR, cookie or upstream cache | MediaCrawler media saver | H.264 URL preferred by upstream. |
| Kuaishou | MediaCrawler `ks` detail | QR, cookie or upstream cache | MediaCrawler media saver | Single specified work. |
| Bilibili | MediaCrawler `bili` detail | QR, cookie or upstream cache | MediaCrawler media saver | Upstream behavior and platform restrictions apply. |
| Weibo | MediaCrawler `wb` detail | QR, cookie or upstream cache | MediaCrawler media saver | Posts without media may legitimately produce metadata only. |
| Tieba | MediaCrawler `tieba` detail | QR, cookie or upstream cache | MediaCrawler media saver | A thread may contain several media assets. |
| Zhihu | MediaCrawler `zhihu` detail | QR, cookie or upstream cache | MediaCrawler media saver | Article/question content is not guaranteed to contain video. |
| Direct `.mp4`, `.mov`, `.webm`, `.mkv`, `.m4v` URL | none | URL-contained authorization only | aria2/curl | Fastest path; no browser or crawler. |

## Video号 resolver order

1. `LOV_MEDIA_CRAWLER_YUANBAO_COOKIE` for the current process.
2. macOS Keychain service `lov-media-crawler-yuanbao`.
3. Explicit custom `--worker-url`: used when no credential exists, or when the credential from 1–2 is rejected with HTTP 401/403.
4. `--allow-public-resolver`: same conditions as 3. The public instance currently refuses requests; see "Resolver service status".
5. Public preview metadata probe and an `authorization_required` result.
6. Local WeChat client capture (`--via auto` fallback or `--via wxclient`) when the paths above fail and `wx_channels_download` is online at `127.0.0.1:2022`.

Never print or persist a Cookie in the Profile or JSON report. A stale credential is a recoverable authorization failure, not a reason to silently send the link to a third party: without `--worker-url` or `--allow-public-resolver` the run stops with `authorization_failed`. With one of them, the link goes to that resolver service and a successful report carries `fallback_from: authorization_failed`. The Cookie is never forwarded to a resolver service and the Keychain entry is left untouched. Only HTTP 401/403 triggers this fallback; an authenticated-but-unparseable link (`resolver_failed`) does not.

## Resolver service status

Measured on 2026-11-19: `POST https://sph.litao.workers.dev/api/fetch_video_profile` with `{"url": "..."}` returns `401 {"error":"unauthorized"}`. The upstream Worker source (`internal/workers/sph/worker.js` in `ltaoo/wx_channels_download`) requires an `ACCESS_CREDENTIAL` chosen by the deployer, supplied as `Authorization: Bearer <credential>` or HTTP Basic, and its deploy guide tells deployers to keep the Worker for their own use. The public instance is therefore not an open path, and a self-hosted Worker deployed from current upstream needs that credential too.

This Skill sends no credential to a resolver service. A 401/403 from one is reported as `resolver_unauthorized`, which is unrelated to the local Yuanbao session; the working routes remain the local Yuanbao authorization and local WeChat client capture.

## Performance policy

- Resolve once, then download directly from the final CDN.
- Prefer 8 connections; cap user input at 16 to avoid abusive fan-out.
- Reuse `.part` state and the exact output path.
- Disable comments and broad search for a supplied content link.
- Start an isolated Chrome profile on an available port from 9333; never attach to an unrelated existing CDP browser.
- Report resolution time separately from transfer time so login delays are not mislabeled as slow bandwidth.
