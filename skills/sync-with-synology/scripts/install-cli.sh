#!/bin/zsh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN_DIR="${HOME}/.local/bin"
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/synology-cli" <<EOF
#!/bin/zsh
exec "$ROOT/.venv/bin/python" "$ROOT/scripts/synology_cli.py" "\$@"
EOF
chmod +x "$BIN_DIR/synology-cli"
"$ROOT/scripts/install.sh" >/dev/null
echo "Installed: $BIN_DIR/synology-cli"
