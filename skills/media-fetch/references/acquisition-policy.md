# Acquisition, Monitoring, and Recovery Policy

## Capacity calculation

Before transfer, require:

```text
selected payload
+ incomplete-file overhead (10%)
+ parallel probe count × probe budget
+ fallback continuation metadata and temporary control files
+ configured free-space reserve
```

Use the filesystem containing the closest existing parent of the destination. Report
bytes in both GiB and human-readable form. If the destination does not exist, capacity
belongs to its nearest existing parent.

## Probe policy

- Default concurrency: 3.
- Default duration: 180 seconds after a 60-second warm-up.
- Default temporary budget: 512 MiB per candidate.
- Default slow threshold: sustained speed below 1 MiB/s.
- Deduplicate by info hash before adding.
- Use a unique tag `media-fetch-<job-id>` and exact per-candidate directories.
- Existing hashes are read-only observations; never alter or clean them.
- Prefer aria2 for direct URLs, Metalinks, Magnets, and Torrent inputs. Its `.aria2`
  control file is evidence of continuation state, not a completed payload.
- Treat qBittorrent as optional. Enable it for reviewed search plugins, queue UI,
  deeper swarm inspection, or long-term seeding; do not make WebUI login a prerequisite
  for an aria2-capable run.
- Allocate distinct listen and RPC ports for concurrent aria2 probes.
- Configure DHT, PeX, LSD, and a bounded tracker set. Direct connections are preferred
  when proxy environment variables produce a slow or incomplete swarm. Record the
  selected backend and connection mode in the report.

A probe winner should combine sustained speed, availability, peers, progress, and ETA.
Prefer stability over a single peak sample.

## Active monitoring

- Poll the client every 5–15 seconds inside the worker.
- Surface a user update at least every 60 seconds while the agent is running tools.
- Track progress delta and received bytes, not only reported state.
- Treat metadata retrieval separately from payload speed.
- A candidate is stalled when both progress delta and download traffic remain below
  thresholds for the configured `stall_seconds` after metadata is available.

## Switching

1. Pause the stalled winner.
2. Resume the next candidate with a successful probe.
3. Recalculate storage if the next candidate is larger than the planned payload.
4. When the ranked list is exhausted, keep the best partial task paused, return to
   discovery, add a new wave, and probe again.
5. Record every switch and reason in the acquisition report.
6. When switching transports for the same input, preserve the isolated job directory,
   reuse partial data only when the backend can validate it, and never report two
   parallel full copies as one completed artifact.

## Cleanup

Cleanup starts only after the winner reports complete and the final file path exists.

- Resolve exact task hashes created in this job.
- Delete losing qBittorrent tasks using exact hashes only when that backend was used.
- Delete files only inside the resolved job probe directory.
- Preserve the winner, final destination, report JSON, and every pre-existing task.
- If path resolution falls outside the job directory, skip file cleanup and report it.

## Terminal states

- `complete`: client complete and local files present; ready for media verification.
- `needs_more_sources`: all tested candidates are below thresholds or unavailable.
- `capacity_shortfall`: no payload transfer started.
- `client_error`: connection or task API failure with copyable diagnostic details.
- `cancelled`: user-requested stop; created tasks are paused and exact state is reported.

## Backend routing

Run `scripts/aria2_acquire.py` first for supported inputs. Use a stable `job_id`,
`--watch` for bounded restarts, `--output-name` for opaque direct URLs, and a report
containing `backend_started`, `backend_restarted`, `last_snapshot`, and
`final_snapshot` events. Switch to qBittorrent only after an enabled probe supplies
measured evidence or the requested queue/seeding behavior requires it. The final report
must separate `download_status` from the later media and subtitle verdicts.
