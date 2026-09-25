# Conservative reclamation policy

Reclamation is an ownership protocol, not a timer plus `kill` or recursive delete.
The safe default is to keep a resource until every required proof agrees.

## Action classes

Choose the least destructive action that meets the runtime budget:

| Action | Meaning | Default authority |
| --- | --- | --- |
| `scope_release` | detach listeners, cancel work and release in-memory scope | normal implementation step |
| `hibernate` | stop an owned runtime while preserving a proven resume path | allowed only after lifecycle proof |
| `cache_evict` | remove reproducible, non-authoritative cached state | bounded by product retention policy |
| `external_reclaim` | terminate an owned external process/session/resource | explicit ownership and final identity check |
| `persistent_delete` | remove durable or user-authored data | explicit target authorization; never automatic optimization |

Mobile suspend/process death and Web Service Worker termination are platform behavior,
not equivalent to desktop process kill. Their adapters must define restoration and data
durability without assuming the app controls the termination moment.

## Resource policies

| Policy | Typical resources | Candidate boundary |
| --- | --- | --- |
| `inventory_only` | unregistered directories, foreign sessions, corrupt rows | never automatically reclaim |
| `orphan_only` | worktrees, workspace terminals, caches with durable owners | owner is missing or explicitly retired, retention is eligible, clean where applicable, unused, stable identity |
| `idle_resumable` | Agent sessions, PTYs, canonical tmux sessions | authoritative idle, no consumer/registration/attachment, stable identity, proven resume path |

An active owner is not the same as active work. `idle_resumable` may reclaim an idle
runtime owned by an active task only when durable state can recreate it without losing
work and the product copy tells users that it will resume on demand. Other policies
keep active owners.

## Universal blockers

Protect the resource when any of these is true:

- activity is `working`, `awaiting_input`, or `unknown`;
- evidence is missing, malformed, oversized, stale, or from the wrong owner;
- an attachment, subscriber, registration, lease, or input/output transition is active;
- a create, restore, archive, move, export, or teardown operation is in flight;
- product retention says retain or has no authoritative verdict;
- identity changed or cannot be proven stable;
- a terminal/process cwd is inside the worktree or directory;
- the worktree is dirty, dirty state is unknown, or the directory is not registered;
- the durable owner relationship is corrupt or crosses a project boundary;
- remote listing, DB lookup, artifact read, or final recheck timed out or failed.

No-server is not the same as a transport failure. A canonical local tmux server that
does not exist may safely yield an empty inventory. SSH failure, timeout, permission
failure, or unparseable output remains unknown and protects resources.

## Lifecycle design

For each resource type, write down:

1. **Durable owner** — the database or project entity that survives application restart.
2. **Runtime lease** — UI consumer, provider registration, attached pane, open file,
   process cwd, or in-flight operation.
3. **Activity truth** — authoritative provider state or complete durable artifact;
   a recent timestamp alone is not proof of idle.
4. **Resume path** — how a protected durable identity recreates runtime state.
5. **Fingerprint** — fields that distinguish one instance from a same-name replacement,
   such as creation time, pane PID, activity stamp and attachment state.
6. **Dependency order** — children terminate before workspaces; workspaces before
   worktrees; identities remain until cleanup is confirmed.

## Two-phase classification

Use two bounded O(N) passes rather than N full inventories:

1. List runtime markers once and batch-load durable owners.
2. Classify possible candidates and read bounded provider artifacts.
3. Yield to the event loop or wait for the policy's grace period.
4. Re-list once, batch-load owners again, and re-run classification.
5. Immediately before the action, query O(1) live registration/consumer state and
   execute an atomic conditional kill/delete against the original fingerprint.

If the resource changed between passes, it is a new instance. Skip it. This blocks
the ABA race where a session is destroyed and recreated under the same name.

## Hydration before sweeping

A sweep cannot fix unconditional rehydration. Startup and task provisioning should:

- start pending initial work;
- reconnect to an already live canonical instance;
- leave completed historical sessions hibernated until explicitly visible or resumed;
- bound concurrent starts and stops;
- share inventory snapshots instead of listing all sessions for every task.

## Worktree and directory ordering

Before a registered worktree is reclaimed, re-read all of the following:

- durable task/project references;
- Git registration and canonical path;
- clean status;
- live process and tmux cwd blockers;
- identity or filesystem signature.

Unknown directories stay in a read-only inventory. Never infer ownership from a name
alone and never recursively remove them as a side effect of future branch reuse.

Archive/delete flows should await runtime teardown. When teardown cannot be confirmed:

- archive may complete its durable state transition but must retain the worktree;
- delete should retain the durable identity so cleanup can be retried;
- project deletion must not cascade away the IDs needed to find detached runtime state.

## Testing matrix

At minimum cover:

- authoritative idle versus working, awaiting input, unknown, empty artifact,
  malformed event and scan-budget exhaustion;
- attached, consumer active, registration in progress and new input after classification;
- no server, SSH error, timeout, kill failure followed by natural exit, and persistent kill failure;
- same name with different creation time or pane PID;
- active resumable owner, archived owner, missing owner, corrupt cross-project owner;
- registered clean worktree, dirty worktree, cwd-in-use worktree and unregistered directory;
- two concurrent cleanup requests collapsing into one single-flight run.
