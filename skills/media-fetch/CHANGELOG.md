# Changelog

## [0.4.0] - 2026-08-26

### Added

- make aria2 the primary transport backend
- treat qBittorrent as an optional search, queue-management, and seeding adapter
- support direct HTTP inputs, opaque output names, RPC progress, and job-specific ports in aria2 acquisition
- detect RPC-resident completion through aria2.tellStopped and terminate the worker cleanly
- migrate legacy transport preferences and document the aria2-first workflow

## [0.3.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## 0.2.0

- Added an aria2 fallback runner with DHT, PeX, LSD, bounded trackers, `.aria2`
  continuation state, bounded restarts, and structured transport events.
- Separated advertised source health from live probe evidence and final verification.
- Added a Simplified Chinese subtitle handoff with exact-release matching, UTF-8 SRT
  preservation, and explicit opt-in boundaries for learning gloss and ASS output.
- Added the LovStudio Skill Card, pricing card, sanitized evidence bundle, and the
  《指环王》三部曲 user case.

## 0.1.0

- Added a four-module discovery, selection, acquisition, and verification Skill Kit.
- Added portable media preferences and a default download destination.
- Added qBittorrent search, ranking, capacity preflight, parallel probing, stall recovery, and media verification helpers.
