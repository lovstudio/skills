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

The local Python implementation is original glue around the documented HTTP contracts and standard download tools. Service behavior can change; treat authentication failures as a prompt to reauthorize, not as permission to bypass platform controls.

## Responsibility boundary

- Users must have permission to access and save the content.
- Do not remove DRM, decrypt protected streams, evade paywalls or perform account-scale collection.
- Platform terms and copyright continue to apply to downloaded media.
