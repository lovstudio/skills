#!/bin/bash
# Dev mode: symlink installed skills to source repo, Ctrl+C to stop and restore
# Usage: bash dev.sh [skill-dir]  (default: all skills)

SOURCE_ROOT="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$HOME/.claude/skills"
LINKED=()

link_skill() {
  local dir="$1"
  local name="$(basename "$dir")"
  local target="$SKILLS_DIR/$name"

  if [ -d "$target" ] && [ ! -L "$target" ]; then
    mv "$target" "$target.bak"
  fi
  rm -f "$target"
  ln -s "$dir" "$target"
  LINKED+=("$name")
  echo "  ✓ $name → $dir"
}

cleanup() {
  echo ""
  for name in "${LINKED[@]}"; do
    local target="$SKILLS_DIR/$name"
    rm -f "$target"
    if [ -d "$target.bak" ]; then
      mv "$target.bak" "$target"
      echo "  Restored $name from backup."
    else
      echo "  Removed $name symlink."
    fi
  done
  echo "Dev mode OFF."
  exit 0
}
trap cleanup INT TERM

echo "Dev mode ON:"

if [ -n "$1" ]; then
  link_skill "$SOURCE_ROOT/skills/$1"
else
  for d in "$SOURCE_ROOT"/skills/lovstudio-*/; do
    [ -f "$d/SKILL.md" ] && link_skill "$d"
  done
fi

echo ""
echo "Edit source freely. New CC sessions pick up changes."
echo "Ctrl+C to stop."
echo ""

while true; do sleep 86400; done
