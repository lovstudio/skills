# PicGo Integration

## Backend order

`scripts/upload_image.py` supports three modes:

1. `server` sends JSON to a running PicGo GUI or PicGo-Core Server.
2. `cli` calls an explicitly configured or PATH-discoverable PicGo-Core executable.
3. `auto` tries Server first, then CLI only when the Server transport is unavailable.

Server mode is preferred because it shares the running PicGo GUI's current uploader,
plugins, naming rules, and credentials. CLI mode can use a separate PicGo-Core config;
do not assume the two installations select the same image host.

## Server contract

Default base URL: `http://127.0.0.1:36677`.

- `POST /heartbeat` with an empty JSON object must return a successful `alive` result.
- `POST /upload` receives a JSON object whose `list` value is an ordered array of
  absolute local paths.
- Older PicGo versions return URL strings in `result`; newer versions may also return
  structured objects in `items`. The script accepts both and requires the URL count
  to match the input count.

Official references:

- [PicGo-Core commands and Server API](https://picgo.github.io/PicGo-Core-Doc/guide/commands.html)
- [PicGo-Core repository](https://github.com/PicGo/PicGo-Core)

## Authentication and privacy

If PicGo Server authentication is enabled, set `PICGO_SERVER_SECRET` or pass the name
of another environment variable with `--secret-env`. The value is sent as a Bearer
token. It is never printed or placed in JSON output.

The Skill must not read PicGo's configuration file. PicGo owns image-host keys and
tokens; this wrapper only passes local paths to the already configured process.

## Availability recovery

- `doctor` is read-only and reports Server heartbeat, CLI discovery, installed macOS
  application presence, and whether the secret environment variable is set.
- `--start-app` may open `/Applications/PicGo.app` on macOS and wait briefly for the
  Server. It does not enable Server mode or edit PicGo settings.
- A Server upload failure is not retried through CLI because that could duplicate a
  partially created remote object. `auto` falls back only when the Server transport
  itself is unavailable.

## Result and verification

Every result must be an absolute HTTP or HTTPS URL. `--verify` first uses HEAD, then
falls back to a ranged GET when the origin refuses HEAD. A verification failure occurs
after PicGo may have created the remote object; the script stops before writing
Markdown but cannot roll back the image host.
