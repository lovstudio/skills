# lov-project-port

![Version](https://img.shields.io/badge/version-0.1.1-CC785C)

Generate a stable project-specific development port in the 3000-8999 range, then help wire it into `.env`, package scripts, Vite, or other dev-server config.

Part of [skill-publisher dev skills](https://example.com/skills/dev-skills) — by [example.com](https://example.com)

## Install

```bash
npx skills add project-port -g -y
```

## Usage

```bash
./scripts/hashport.sh
./scripts/hashport.sh my-project
```

The script prints the port to stdout and reports occupancy to stderr when `lsof` is available.

## Algorithm

```python
port = 3000 + (sum(ord(c) * (i + 1) for i, c in enumerate(project_name)) % 6000)
```

The same project name always maps to the same port.

## Common Targets

| File | Update |
|---|---|
| `.env` / `.env.local` | `PORT=<port>` |
| `package.json` | add or update `--port <port>` in dev scripts |
| `vite.config.ts` | set `server.port` |

## License

MIT
