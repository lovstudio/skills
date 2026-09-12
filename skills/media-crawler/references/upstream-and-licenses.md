# Upstream Projects and Licenses

## MediaCrawler

- Repository: `https://github.com/NanmiCoder/MediaCrawler`
- Verified integration commit: `5665a271ef15e0ec82b1f48a951b66760e054db9`
- Role: platform routing, Playwright login-state reuse, signed API access and platform-specific media extraction for Xiaohongshu, Douyin, Kuaishou, Bilibili, Weibo, Tieba and Zhihu.
- License at the verified commit: `NON-COMMERCIAL LEARNING LICENSE 1.1`.

The setup command checks out this commit into the user's cache and leaves the upstream `LICENSE` intact. MediaCrawler is not copied into this Skill, is not a hidden install, and must not be used commercially or for large-scale crawling without separate permission.

## WeChat Channels extension

The public MediaCrawler platform enum does not include WeChat Channels. The dedicated adapter follows the same local-session principle but uses a different two-step contract:

1. Tencent Yuanbao `get_parse_result` resolves a `weixin.qq.com/sph/...` share URL into an export ID and playable page token.
2. WeChat Channels `get_feed_info` returns the authorized media URL and metadata.

The API flow was cross-checked against `ltaoo/wx_channels_download` and its public Cloudflare Worker source. That project carries an MIT license with Commons Clause restriction. This Skill does not bundle or sell that project. A third-party Worker is never used without explicit opt-in.

## WeChat client capture (`wx_channels_download` binary)

- Repository: `https://github.com/ltaoo/wx_channels_download`
- Pinned release: `v260907`, macOS `darwin_arm64` / `darwin_x86_64` zip, verified against the release `checksums.txt` before unpacking.
- Install location: `~/.cache/lov-media-crawler/wx_channels_download/<version>/`, with a Skill-owned `workdir/config.yaml` that only changes the download directory and database path.
- Role: a local MITM proxy that injects into the WeChat desktop Channels page, exposing `/api/channels/feed/profile` and `/api/v1/download_task/*` on `127.0.0.1:2022`. It reaches content the Yuanbao path cannot (publisher blocks out-of-WeChat parsing) because the request is made by the logged-in WeChat client itself.
- Boundary: starting it installs a root certificate and sets the system proxy. That is a system security change and is always executed by the user (`scripts/wxclient.sh start`), never by the Agent. The binary is not bundled in this Skill; `setup-wxclient` downloads it only when invoked.

The local Python implementation is original glue around the documented HTTP contracts and standard download tools. Service behavior can change; treat authentication failures as a prompt to reauthorize, not as permission to bypass platform controls.

## Responsibility boundary

- Users must have permission to access and save the content.
- Do not remove DRM, decrypt protected streams, evade paywalls or perform account-scale collection.
- Platform terms and copyright continue to apply to downloaded media.
