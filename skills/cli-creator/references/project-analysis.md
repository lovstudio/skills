# Project Analysis Rules

The inspector provides a cheap inventory; the agent must confirm architecture by
reading the relevant source before designing commands.

## Analysis order

1. Read repository instructions, primary README, manifests, and existing help.
2. Identify the product's user tasks and stable domain objects.
3. Locate existing CLI entry points, scripts, service routes, public library APIs,
   native project formats, and export/render paths.
4. Trace at least one read workflow and one material mutation from entry point to
   postcondition.
5. Record hard dependencies and how `doctor` can diagnose them.
6. Decide whether state is stateless, project-file based, service based, or a
   persistent session.

## Backend selection

Use the narrowest boundary that preserves product behavior:

| Project signal | Preferred adapter |
|---|---|
| Existing maintained CLI | Typed subprocess wrapper or direct reuse |
| Stable public Python/JS/Rust library API | Thin in-process or native-language wrapper |
| Local HTTP/RPC/MCP service | Protocol client with explicit health check |
| Native project file plus official headless renderer | Native-format editor plus real renderer |
| GUI action with internal command dispatcher | Call the dispatcher or scripting API |

Never use screen coordinates as the primary backend when a callable surface
exists. Never reproduce a renderer or business engine merely to make tests pass.

## Command coverage

Organize commands by user domain, normally including:

- lifecycle: create, open, save, close, status;
- inspect: info, list, get, schema, capabilities;
- primary operations: the product's core user jobs;
- import/export or render where applicable;
- configuration and session history where applicable.

Start with a coherent vertical slice. A smaller CLI that completes and verifies
real work is better than a broad command list backed by stubs.

## State and mutation questions

- What identity remains stable across commands?
- Where is state persisted, and can two processes write concurrently?
- Does a one-shot mutation auto-save before exit?
- Can the same command be repeated safely?
- What does `--dry-run` show, and what side effects does it suppress?
- Is undo/redo native, emulated safely, or explicitly unsupported?

For a persistent JSON session, write atomically and take an exclusive lock before
read-modify-write. For database or service state, use the product's transaction
boundary.

## Evidence to retain

Keep the project analysis report, CLI plan, real test names, installed command
path, and paths to generated artifacts. Do not store credentials, private user
data, or machine-specific absolute paths in reusable source.
