#!/bin/zsh
set -euo pipefail
SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$SKILL_ROOT/.venv/bin/python"
CLI="$SKILL_ROOT/scripts/synology_cli.py"
FAKE="$SKILL_ROOT/scripts/fake_dsm_server.py"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/sync-with-synology-e2e.XXXXXX")"
PIDS=()

cleanup() {
  for pid in "${PIDS[@]:-}"; do
    kill "$pid" >/dev/null 2>&1 || true
  done
  if [[ "${KEEP_E2E:-0}" == "1" ]]; then
    echo "kept test workspace: $TMP"
  else
    rm -rf "$TMP"
  fi
}
trap cleanup EXIT

start_fake() {
  local root="$1" corrupt="${2:-}"
  mkdir -p "$root"
  local args=(--root "$root" --cert "$TMP/cert.pem" --key "$TMP/key.pem" --print-port)
  if [[ -n "$corrupt" ]]; then
    args+=(--corrupt-name "$corrupt")
  fi
  "$PY" "$FAKE" "${args[@]}" > "$TMP/server-port.txt" 2> "$TMP/server.err" &
  local pid=$!
  PIDS+=("$pid")
  local port=""
  for _ in {1..50}; do
    port="$(head -n 1 "$TMP/server-port.txt" 2>/dev/null || true)"
    [[ -n "$port" ]] && break
    sleep 0.1
  done
  if [[ -z "$port" ]]; then
    cat "$TMP/server.err" >&2 || true
    echo "fake DSM did not start" >&2
    exit 1
  fi
  echo "$port"
}

openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout "$TMP/key.pem" -out "$TMP/cert.pem" -days 2 \
  -subj '/CN=127.0.0.1' -addext 'subjectAltName=IP:127.0.0.1' >/dev/null 2>&1

PORT="$(start_fake "$TMP/remote")"
URL="https://127.0.0.1:$PORT"
BASE_ARGS=(--base-url "$URL" --username test --dsm-version 6 --no-cert-verify)

echo "[0/8] QuickConnect resolver unit test"
"$PY" "$SKILL_ROOT/scripts/test_quickconnect_resolver.py"

SOURCE_DIR="${SYNOLOGY_UPLOADER_TEST_SOURCE:-$HOME/Music/MP3}"
if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "test source not found: $SOURCE_DIR" >&2
  exit 1
fi
mkdir -p "$TMP/source" "$TMP/trash" "$TMP/audit"
cp -R "$SOURCE_DIR"/. "$TMP/source"/

echo "[1/8] doctor"
SYNO_PASSWORD=mock "$PY" "$CLI" doctor "${BASE_ARGS[@]}" > "$TMP/doctor.json"

echo "[2/8] dry-run on real source"
SYNO_PASSWORD=mock "$PY" "$CLI" run \
  --source "$SOURCE_DIR" --remote-dir /home/Music/MP3 \
  "${BASE_ARGS[@]}" --dry-run --delete-mode none --json > "$TMP/dry.jsonl"

echo "[3/8] verified upload + localized trash on a copy"
SYNO_PASSWORD=mock "$PY" "$CLI" run \
  --source "$TMP/source" --remote-dir /home/Music/MP3 \
  "${BASE_ARGS[@]}" --delete-mode trash \
  --trash-dir "$TMP/trash" --audit-log "$TMP/audit/normal.jsonl" --json > "$TMP/normal.jsonl"

[[ "$(find "$TMP/source" -type f | wc -l | tr -d ' ')" == "0" ]]
[[ "$(find "$TMP/trash" -type f | wc -l | tr -d ' ')" -gt 0 ]]

echo "[4/8] remote MD5 comparison"
"$PY" - "$SOURCE_DIR" "$TMP/remote/home/Music/MP3" <<'PY'
import hashlib, pathlib, sys
source = pathlib.Path(sys.argv[1])
remote = pathlib.Path(sys.argv[2])
for src in sorted(source.glob('*.mp3')):
    dst = remote / src.name
    if not dst.is_file():
        raise SystemExit(f'missing remote file: {dst}')
    if hashlib.md5(src.read_bytes()).digest() != hashlib.md5(dst.read_bytes()).digest():
        raise SystemExit(f'md5 mismatch: {src.name}')
print(f'verified {len(list(source.glob("*.mp3")))} files')
PY

echo "[5/8] idempotency"
mkdir -p "$TMP/idem-source" "$TMP/idem-trash" "$TMP/unlink-source"
FIRST_MP3="$(find "$SOURCE_DIR" -maxdepth 1 -type f -name '*.mp3' | sort | head -n 1)"
cp "$FIRST_MP3" "$TMP/idem-source/"
SYNO_PASSWORD=mock "$PY" "$CLI" run \
  --source "$TMP/idem-source" --remote-dir /home/Music/MP3 \
  "${BASE_ARGS[@]}" --delete-mode trash --trash-dir "$TMP/idem-trash" --json > "$TMP/idem.jsonl"
"$PY" - "$TMP/idem.jsonl" <<'PY'
import json, sys
summary = json.loads(open(sys.argv[1], encoding='utf-8').read().strip().splitlines()[-1])
assert summary['ok'] is True, summary
assert summary['totals']['skipped'] == 1, summary
assert summary['totals']['deleted'] == 1, summary
PY

echo "[6/8] unlink mode"
cp "$FIRST_MP3" "$TMP/unlink-source/"
SYNO_PASSWORD=mock "$PY" "$CLI" run \
  --source "$TMP/unlink-source" --remote-dir /home/Music/MP3 \
  "${BASE_ARGS[@]}" --delete-mode unlink --json > "$TMP/unlink.jsonl"
"$PY" - "$TMP/unlink.jsonl" <<'PY'
import json, sys
summary = json.loads(open(sys.argv[1], encoding='utf-8').read().strip().splitlines()[-1])
assert summary['ok'] is True, summary
assert summary['totals']['deleted'] == 1, summary
PY
[[ "$(find "$TMP/unlink-source" -type f | wc -l | tr -d ' ')" == "0" ]]

echo "[7/8] failure protection"
CORRUPT_PORT="$(start_fake "$TMP/corrupt-remote" 'dhy-piano.mp3')"
mkdir -p "$TMP/corrupt-source"
cp "$SOURCE_DIR/dhy-piano.mp3" "$TMP/corrupt-source/"
if SYNO_PASSWORD=mock "$PY" "$CLI" run \
  --source "$TMP/corrupt-source" --remote-dir /home/Music/MP3 \
  --base-url "https://127.0.0.1:$CORRUPT_PORT" --username test --dsm-version 6 --no-cert-verify \
  --delete-mode trash --trash-dir "$TMP/corrupt-trash" --json > "$TMP/corrupt.jsonl"; then
  echo "corrupt upload unexpectedly succeeded" >&2
  exit 1
fi
[[ "$(find "$TMP/corrupt-source" -type f | wc -l | tr -d ' ')" == "1" ]]

echo "[8/8] complete"
echo "PASS: QuickConnect resolution + doctor + dry-run + verified upload/prune + MD5 + idempotency + unlink + failure protection"
