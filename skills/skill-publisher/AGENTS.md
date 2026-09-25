# lov-skill-publisher 跨会话经验

- 官网 `lovstudio.ai` 是 Vercel 项目 `lovstudio/homepage`，源码在 `~/lovstudio/coding/web`（远程 `lovstudio/lovstudio-home`）。skill 数据从 `raw.githubusercontent.com/lovstudio/skills/main/skills.yaml` **运行时**拉取（`next: revalidate 600` + tag `skills-index`），不是构建时打包。
- 官网 revalidate secret 变量名是 `LOVSTUDIO_REVALIDATE_SECRET`（publisher 文档里的 `SKILL_REVALIDATE_SECRET` 过时）；curl 用 `x-revalidate-secret` header 直接读 web `.env.local` 的 `REVALIDATE_SECRET`（2026-08-21, 907a0f3）。
- 免费 skill 的 source repo 必须 **public**：官网 `ghFetchOpts(false)` 不带 token 拉 `raw.githubusercontent.com/{repo}/main/{SKILL.md,README.md,skill-card.yaml}`。skill-card.yaml 对 free skill 是可选（describe-image 的 card 是 404 仍渲染正常）。
- 详情页 404 排查：先确认 `curl raw.githubusercontent.com/lovstudio/skills/main/skills.yaml` 含条目、source repo 的 SKILL.md/README/skill-card 均 200、SKILL.md frontmatter 能被 `yaml.load`。数据层正常却 404 → 是 **CDN 边缘缓存了旧 404**；用 `?v=N` cache-bust 或直接 curl 部署 URL 验证，边缘缓存过期后自动 200（2026-08-21, 907a0f3）。
- 官网代码的 skill 过滤仅 `filter(s => !s.test)`，无白名单；category `Meta/Dev Tools/Developer Tools` 映射为 Dev，其余保留原值。
- catalog `lovstudio/skills` 本地 checkout 是 `~/lovstudio/coding/lovstudio-skills`；`skills.yaml` 是唯一真源，README/marketplace 由 `scripts/render-{marketplace,readme}.py` 渲染，不要手改。本地新增单个 skill 用 `rsync -a --delete --exclude .git <源>/ skills/<name>/`，不必跑全量 `sync-skills.py`（>120s）（2026-08-21, 907a0f3）。
- `skills.yaml` 里 description 含 `: ` 必须加双引号，否则 CI `yaml.safe_load` 直接 ScannerError（2026-08-18, e32d199）。
- catalog 仓库 working tree 常驻 `.github/workflows/build-cdn.yml`、`docs/` 等既有未跟踪 WIP；`git add` 只加本次 skill 相关文件，推送遇非快进先 `git pull --rebase` 再 push（2026-08-21, 907a0f3）。
- 官网发布若数据层正常但列表/详情仍不显示，最可靠是 `vercel --prod --yes` 重新部署（全新 fetch 绕过 ISR 缓存），部署 URL `homepage-<id>-lovstudio.vercel.app` 即可见；生产域 `lovstudio.ai` 受边缘缓存影响（2026-08-21, 907a0f3）。
