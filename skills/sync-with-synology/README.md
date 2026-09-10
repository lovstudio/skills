# sync-with-synology

![Version](https://img.shields.io/badge/version-1.0.0-CC785C)

A local Codex skill and CLI for verified Synology File Station transfers.

## Install

Install from the LovStudio catalog:

```bash
npx lovstudio skills add sync-with-synology
```

For a local source checkout:

```bash
~/.agents/skills/sync-with-synology/scripts/install.sh
~/.agents/skills/sync-with-synology/scripts/install-cli.sh
```

## Use

```bash
synology-cli config
synology-cli doctor
synology-cli run --source ~/Music/MP3 --remote-dir /home/Music/MP3 --dry-run
synology-cli run --source ~/Music/MP3 --remote-dir /home/Music/MP3 --delete-mode trash
# Irreversible local deletion, only after explicit confirmation:
synology-cli run --source ~/Music/MP3 --remote-dir /home/Music/MP3 --delete-mode unlink
```

## Test

```bash
~/.agents/skills/sync-with-synology/scripts/test_e2e.sh
```

The test uses a local fake HTTPS DSM and does not upload anything to a real NAS.
