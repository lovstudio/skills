# Operations Reference

## What the CLI Does Per File

1. Computes the local MD5.
2. Looks up the remote path through `SYNO.FileStation.List.getinfo`.
3. If an equal remote file already exists, treats the local file as safe to prune.
4. Otherwise uploads via `SYNO.FileStation.Upload` with `create_parents=true`.
5. Verifies the remote size.
6. Verifies the remote MD5 through `SYNO.FileStation.MD5`.
7. Recomputes the local MD5 to detect a file that changed during transfer.
8. Moves the local file into the trash directory, unlinks it only when explicitly requested, or leaves it in place with `--delete-mode none`.

## Exit Behavior

- `0`: every file was uploaded/verified/pruned, or a dry-run completed.
- `1`: at least one file failed, or connectivity/config validation failed.
- `2`: runtime dependency import failed; run `scripts/install.sh`.

## Recovery

If a run fails after a partial upload:

- The local source remains in place unless the failure happened after all verification checks.
- Re-run the command. The next run detects an already-present remote file and prunes the local copy without uploading it again.
- For reversible runs, restore files from the configured `trash_dir`.
- Inspect `audit_log` for the exact remote path, size, MD5, action, and error detail.

## QuickConnect Notes

QuickConnect relay resolution is implemented against the public portal protocol:

1. `POST https://global.quickconnect.<cn|to>/Serv.php` with `get_server_info`.
2. If needed, `request_tunnel` against `env.control_host`.
3. Build `https://<serverID>.<relay_region>.quickconnect.<cn|to>`.
4. Ping `server.pingpong_path`.
5. Use the relay origin for DSM File Station Web API calls.

If the portal returns `Alias not found`, the NAS is offline, QuickConnect is disabled, or the alias changed. Configure a reachable `base_url` as a fallback and verify it with `doctor`.
