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
3. Explicit custom `--worker-url`.
4. Public resolver only with `--allow-public-resolver`.
5. Public preview metadata probe and an `authorization_required` result.
6. Local WeChat client capture (`--via auto` fallback or `--via wxclient`) when the Yuanbao path returns `resolver_failed` and `wx_channels_download` is online at `127.0.0.1:2022`.

Never print or persist a Cookie in the Profile or JSON report. A stale credential is a recoverable authorization failure, not a reason to silently send the link to a third party.

## Performance policy

- Resolve once, then download directly from the final CDN.
- Prefer 8 connections; cap user input at 16 to avoid abusive fan-out.
- Reuse `.part` state and the exact output path.
- Disable comments and broad search for a supplied content link.
- Start an isolated Chrome profile on an available port from 9333; never attach to an unrelated existing CDP browser.
- Report resolution time separately from transfer time so login delays are not mislabeled as slow bandwidth.
