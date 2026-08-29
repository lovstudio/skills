# dsh-plugin-publisher

Publish one validated DSH plugin package (`@deepseek-ai/dsh-*` or
`@lovstudio/dsh-*`) to the DeepSeek Harness distribution channels — npm, git,
or tarball — and verify each channel can load it. Publishing updates only the
target plugin's code; when the plugin is developed inside the
`deepseek-harness` monorepo but published from its own repository, only the
plugin's own changes and build artifacts move to the release repo.

![Version](https://img.shields.io/badge/version-0.3.1-CC785C)

## Install

```sh
npx skills add lovstudio/dsh-plugin-publisher-skill --all -g
```

or clone into your skills directory:

```sh
git clone https://github.com/lovstudio/dsh-plugin-publisher-skill \
  "${SKILLS_DIR:-$HOME/.claude/skills}/dsh-plugin-publisher"
```

## Usage

Invoke with “发布这个 DSH 插件” / “publish this DSH plugin”. See `SKILL.md`
for the mandatory workflow and `references/publish-dsh.md` for the grounded
per-channel SOP.

## License

MIT
