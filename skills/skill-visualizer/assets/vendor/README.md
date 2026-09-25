# Vendored Mermaid runtime

- Package: `mermaid`
- Version: `11.12.2`
- Upstream: https://github.com/mermaid-js/mermaid
- Runtime file: `mermaid-11.12.2.min.js`
- SHA-256: `d0830a6c05546e9edb8fe20a8f545f3e0dc7c4c3134d584bad9c13a99d7a71e0`
- License: MIT; see `MERMAID-LICENSE.txt`. The minified bundle also preserves
  its transitive bundled-license notices.

The generator embeds this file directly into each standalone HTML review. It is
vendored so Mermaid SVG rendering works from `file://` without a CDN, package
manager, web server, or network connection.
