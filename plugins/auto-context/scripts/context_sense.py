#!/usr/bin/env python3
"""AutoContext: Context pollution detector for Claude Code.

Runs as UserPromptSubmit hook. Analyzes conversation transcript size/length,
injects a lightweight context hygiene prompt when thresholds are exceeded.

Design: dumb script + smart prompt. The script does fast quantitative checks;
Claude does the qualitative judgment with full context visibility.
"""

import json
import os
import sys
import time

# --- Thresholds (tune these) ---
LINE_THRESHOLD = 40       # transcript entries before first trigger
SIZE_THRESHOLD = 150_000  # transcript bytes (~150KB)
COOLDOWN_ENTRIES = 10     # min entries between re-triggers per session

# State file tracks cooldown per session
STATE_DIR = os.path.expanduser("~/.claude")
STATE_FILE = os.path.join(STATE_DIR, ".auto-context-state.json")


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception:
        pass


def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except Exception:
        sys.exit(0)

    session_id = hook_input.get("session_id", "")
    transcript_path = hook_input.get("transcript_path", "")

    if not transcript_path or not os.path.exists(transcript_path):
        sys.exit(0)

    # --- Measure ---
    try:
        file_size = os.path.getsize(transcript_path)
        with open(transcript_path) as f:
            line_count = sum(1 for _ in f)
    except Exception:
        sys.exit(0)

    # --- Check thresholds ---
    signals = []
    if line_count > LINE_THRESHOLD:
        signals.append(f"{line_count} entries")
    if file_size > SIZE_THRESHOLD:
        signals.append(f"~{file_size // 1024}KB")

    if not signals:
        sys.exit(0)

    # --- Cooldown ---
    state = load_state()
    last = state.get(session_id, {})
    if line_count - last.get("line_count", 0) < COOLDOWN_ENTRIES:
        sys.exit(0)

    state[session_id] = {"line_count": line_count, "ts": time.time()}
    # Prune stale sessions (keep 20 most recent)
    if len(state) > 20:
        by_ts = sorted(state.items(), key=lambda kv: kv[1].get("ts", 0))
        state = dict(by_ts[-20:])
    save_state(state)

    # --- Inject ---
    context = (
        "<auto-context>\n"
        f"[AutoContext] context load: {', '.join(signals)}.\n"
        "Before proceeding, briefly assess context relevance to the new request:\n"
        "- High relevance -> continue normally, say nothing about context\n"
        "- Mixed -> mentally deprioritize stale context, proceed\n"
        "- Low relevance -> suggest user run /fork or /btw for a clean slate\n"
        "Keep assessment to 1 sentence max. Skip entirely if context is healthy.\n"
        "</auto-context>"
    )

    print(json.dumps({"hookSpecificOutput": {"additionalContext": context}}))
    sys.exit(0)


if __name__ == "__main__":
    main()
