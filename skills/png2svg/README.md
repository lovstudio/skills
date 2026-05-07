# lovstudio:png2svg

![Version](https://img.shields.io/badge/version-1.0.1-CC785C)

Convert PNG images into high-quality SVG files with optional white-background removal, vtracer spline vectorization, and svgo compression.

Part of [lovstudio general skills](https://github.com/lovstudio/general-skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx lovstudio skills add png2svg -g -y
```

## Dependencies

```bash
brew install imagemagick
cargo install vtracer
npm install -g svgo
```

`npx svgo` also works when `svgo` is not installed globally.

## Workflow

```bash
magick input.png -fuzz 15% -transparent white -channel A -threshold 50% +channel input.temp.png
vtracer --input input.temp.png --output output.svg --mode spline --filter_speckle 8 --color_precision 8 --corner_threshold 120 --segment_length 6 --path_precision 5
npx svgo output.svg -o output.svg --multipass
rm -f input.temp.png
```

## Options

| Variable | Default | Description |
|---|---|---|
| `INPUT_PNG` | required | Source PNG path |
| `OUTPUT_SVG` | input basename with `.svg` | Target SVG path |
| `KEEP_BG` | `false` | Keep the original background instead of removing white |

## License

MIT
