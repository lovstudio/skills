# Chapter Project Format

`chapter-project.json` is the contract shared by planning, Studio, rendering,
and editor export.

## Required shape

```json
{
  "schemaVersion": "1.0",
  "name": "Video chapter project",
  "video": {
    "src": "/path/to/video.mp4",
    "duration": 600,
    "width": 1920,
    "height": 1080,
    "fps": 30
  },
  "chapters": [
    {
      "id": "chapter-1",
      "start": 0,
      "end": 240,
      "title": "章节标题",
      "summary": "本章内容摘要"
    }
  ],
  "style": {
    "position": "bottom",
    "marginX": 96,
    "marginBottom": 72,
    "barHeight": 12,
    "gap": 8,
    "labelGap": 18,
    "fontFamily": "PingFang SC",
    "fontFile": null,
    "fontSize": 34,
    "textColor": "#F5F1E8",
    "activeColor": "#EB6637",
    "inactiveColor": "#FFFFFF38",
    "panelColor": "#101419CC",
    "cornerRadius": 6,
    "showTitle": true,
    "showIndex": true
  },
  "export": {
    "codec": "h264",
    "crf": 18,
    "preset": "medium",
    "alphaCodec": "prores_4444"
  }
}
```

## Invariants

- Use seconds as floating-point numbers.
- Start the first chapter at `0`.
- Set each chapter end to the next chapter start.
- Set the final chapter end to `video.duration`.
- Keep chapter IDs unique.
- Use CSS-compatible hex colors: `#RRGGBB` or `#RRGGBBAA`.
- Use an explicit font file for reproducible cross-platform title rendering.
- Keep video paths explicit; the browser still asks the user to select the local
  file because browsers do not open arbitrary filesystem paths.

