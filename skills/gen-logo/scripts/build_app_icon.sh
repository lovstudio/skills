#!/usr/bin/env bash

set -euo pipefail

usage() {
  echo "Usage: $0 --mark PATH --output PATH --layout-output PATH (--background COLOR | --background-image PATH) [--occupancy 0.68] [--size 1024]" >&2
}

mark_path=""
output_path=""
layout_output_path=""
background_color=""
background_image=""
occupancy="0.68"
canvas_size="1024"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mark)
      mark_path="${2:-}"
      shift 2
      ;;
    --output)
      output_path="${2:-}"
      shift 2
      ;;
    --layout-output)
      layout_output_path="${2:-}"
      shift 2
      ;;
    --background)
      background_color="${2:-}"
      shift 2
      ;;
    --background-image)
      background_image="${2:-}"
      shift 2
      ;;
    --occupancy)
      occupancy="${2:-}"
      shift 2
      ;;
    --size)
      canvas_size="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ -z "$mark_path" || -z "$output_path" || -z "$layout_output_path" ]]; then
  usage
  exit 2
fi

if [[ ! -f "$mark_path" ]]; then
  echo "Mark file not found: $mark_path" >&2
  exit 2
fi

if [[ -n "$background_color" && -n "$background_image" ]]; then
  echo "Choose either --background or --background-image." >&2
  exit 2
fi

if [[ -z "$background_color" && -z "$background_image" ]]; then
  echo "A full-bleed background is required." >&2
  exit 2
fi

if [[ -n "$background_image" && ! -f "$background_image" ]]; then
  echo "Background image not found: $background_image" >&2
  exit 2
fi

if ! [[ "$canvas_size" =~ ^[0-9]+$ ]] || [[ "$canvas_size" -lt 16 ]]; then
  echo "--size must be an integer of at least 16." >&2
  exit 2
fi

if ! awk -v value="$occupancy" 'BEGIN { exit !(value >= 0.60 && value <= 0.78) }'; then
  echo "--occupancy must be between 0.60 and 0.78." >&2
  exit 2
fi

if ! command -v magick >/dev/null 2>&1; then
  echo "ImageMagick 7 is required." >&2
  exit 2
fi

mkdir -p "$(dirname "$output_path")" "$(dirname "$layout_output_path")"

target_size="$(awk -v size="$canvas_size" -v ratio="$occupancy" 'BEGIN { printf "%d", (size * ratio) + 0.5 }')"

mark_channels="$(magick identify -format '%[channels]' "$mark_path")"
if [[ "$mark_channels" != *a* ]]; then
  echo "The mark must contain an alpha channel: ${mark_channels}." >&2
  exit 2
fi

read -r alpha_min alpha_max < <(
  magick "$mark_path" -alpha extract -format '%[fx:minima] %[fx:maxima]\n' info:
)
if ! awk -v low="$alpha_min" -v high="$alpha_max" \
  'BEGIN { exit !(low <= 0.01 && high >= 0.5) }'; then
  echo "The mark must contain both transparent background and visible content." >&2
  exit 2
fi

magick "$mark_path" -alpha extract -threshold 1% -trim -format '%w %h\n' info: | {
  read -r trimmed_width trimmed_height
  if [[ "$trimmed_width" -lt 1 || "$trimmed_height" -lt 1 ]]; then
    echo "The mark has no visible alpha content." >&2
    exit 2
  fi
}

magick "$mark_path" -trim +repage \
  -resize "${target_size}x${target_size}" \
  -gravity center -background none -extent "${canvas_size}x${canvas_size}" \
  "PNG32:${layout_output_path}"

if [[ -n "$background_image" ]]; then
  magick "$background_image" \
    -resize "${canvas_size}x${canvas_size}^" \
    -gravity center -extent "${canvas_size}x${canvas_size}" \
    "$layout_output_path" -compose over -composite \
    -alpha remove -alpha off "PNG24:${output_path}"
else
  magick -size "${canvas_size}x${canvas_size}" "canvas:${background_color}" \
    "$layout_output_path" -compose over -composite \
    -alpha remove -alpha off "PNG24:${output_path}"
fi

read -r output_width output_height output_channels < <(
  magick identify -format '%w %h %[channels]\n' "$output_path"
)

if [[ "$output_width" != "$canvas_size" || "$output_height" != "$canvas_size" ]]; then
  echo "Unexpected output size: ${output_width}x${output_height}." >&2
  exit 1
fi

if [[ "$output_channels" == *a* ]]; then
  echo "App icon still contains alpha: ${output_channels}." >&2
  exit 1
fi

read -r visible_width visible_height < <(
  magick "$layout_output_path" -alpha extract -threshold 1% -trim -format '%w %h\n' info:
)

actual_occupancy="$(awk -v w="$visible_width" -v h="$visible_height" -v size="$canvas_size" 'BEGIN { long = w > h ? w : h; printf "%.3f", long / size }')"

echo "Built app icon: $output_path"
echo "Layout proof: $layout_output_path"
echo "Canvas: ${canvas_size}x${canvas_size}, visible mark occupancy: ${actual_occupancy}"
