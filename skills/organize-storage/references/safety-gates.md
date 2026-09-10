# Safety Gates

Run these gates before asking for confirmation and again before each apply.
Every gate is read-only unless the final step is explicitly confirmed.

## Gate 0: target and scope

- Confirm the exact volume root or archive root.
- Record filesystem type, total space, free space, and whether the volume is
  writable.
- Confirm the user wants a structural move, not a duplicate deletion or a local
  Mac cleanup.
- If the user only asked for analysis, stop after the plan.

## Gate 1: system and trash denylist

Never move or rename:

- `.Trashes`
- `.Spotlight-V100`
- `.fseventsd`
- `.DocumentRevisions-V100`
- `.TemporaryItems`
- `$RECYCLE.BIN`
- `System Volume Information`

The planner hard-blocks these paths even when they appear inside a proposed
source. Record their size and contents count only.

## Gate 2: sole-copy and trash seal

If a trash directory contains media or documents that do not exist elsewhere on
the volume, treat it as a sealed evidence area:

1. inventory filenames and sizes without opening or moving them;
2. compare against source cards, archives, and independent backups;
3. if no second copy is confirmed, leave the trash untouched;
4. only after an independent copy is verified may the user authorize cleanup.

Never empty a trash directory as part of a structural reorganization.

## Gate 3: active work and app libraries

- Detect files modified within the last 48 hours under a source.
- Check for open writers with `lsof | grep -F "$ROOT"` when available.
- Leave files modified recently in place unless the user explicitly confirms the
  job is finished.
- App libraries such as `.tvlibrary`, `.fcpbundle`, `JianyingPro`, and editor
  project databases stay at their expected path unless the consuming app has
  been repointed or the library is confirmed cold.
- Historical JSON and logs may contain absolute paths. Do not rewrite them; map
  old paths to new paths in `mapping.json`.

## Gate 4: same-volume and destination

- A rename must stay on the same device. Compare the source and destination
  parent device IDs.
- The destination must not exist. There is no overwrite path.
- The destination parent is created only when it is inside the target root.
- No source may be an ancestor or descendant of another source in the same plan.
- Cross-volume moves are copies; they require a separate migration plan, free
  space, and a checksum verification loop.

## Gate 5: sidecars and metadata

- ExFAT and similar filesystems use AppleDouble files named `._<name>`.
- When a file or directory is renamed, carry or verify its sidecar.
- If the operating system moves the sidecar automatically, verify that the
  destination sidecar exists and record the automatic move.
- Never delete a sidecar independently of its target.
- Do not bulk-delete `._*` metadata just because Finder hides it.

## Gate 6: rollback and evidence

Before apply, write:

- `mapping.json`: every old path, new path, type, pre/post inode, size, and
  timestamp evidence;
- `rollback.sh`: reverse-order best-effort restore commands;
- a dry-run summary with move count, total logical size, hard blocks, warnings,
  and untouched system paths.

After apply, verify every source is gone, every destination exists, and sidecars
are paired. Report any move that was skipped or deferred.

## Gate 7: no-deletion invariant

This Skill does not delete. Quarantine means rename into a visible holding
directory. Deletion belongs to a separate capability and a separate user
confirmation. A plan that cannot be completed without deletion is a blocked
plan.
