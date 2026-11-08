#!/usr/bin/env python3
"""Sample frames every N seconds, OCR them with macOS Vision, and summarise the on-screen
text layout per sample: top title (lines, height, persistence), subtitle zone (coverage,
characters per line, box height and position), top-left card, and punctuation in subtitles.

Manifest: sources.json {"samples": [{"sample_id", "rank", "path", "duration_seconds", "partition"}]}.
Requires ffmpeg and swiftc (Xcode command line tools). Frames stay in --output; they are
analysis material, not reusable assets.
"""
import argparse
import json
import re
import statistics as st
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]


def ocr_binary(out):
    binary = out / '.bin' / 'ocr_frames'
    if not binary.exists():
        binary.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['swiftc', '-O', str(SKILL / 'scripts' / 'ocr_frames.swift'), '-o', str(binary)], check=True)
    return binary


def summarise(frames, duration, wall=None):
    wall = re.compile(wall) if wall else None
    cx = lambda b: b['x'] + b['width'] / 2
    rows = []
    for fr in frames:
        texts = [x for x in fr['texts'] if x['confidence'] > 0.3 and not (wall and wall.match(x['text']))]
        top = [x for x in texts if x['bbox']['y'] < 0.17 and abs(cx(x['bbox']) - 0.5) < 0.2 and x['bbox']['height'] > 0.018]
        sub = [x for x in texts if 0.66 < x['bbox']['y'] < 0.88 and abs(cx(x['bbox']) - 0.5) < 0.17 and x['bbox']['height'] < 0.04]
        card = [x for x in texts if x['bbox']['x'] < 0.45 and x['bbox']['y'] < 0.42 and cx(x['bbox']) < 0.4]
        rows.append({'t': fr['time_seconds'], 'top': top, 'sub': sub, 'card': card if len(card) >= 3 else []})
    first = [r for r in rows if r['t'] <= 6 and r['top']]
    title = [x['text'] for x in first[0]['top']] if first else []
    def has_title(r):
        joined = ''.join(x['text'] for x in r['top'])
        return bool(title) and any(len(set(l) & set(joined)) >= max(3, int(len(set(l)) * 0.5)) for l in title)
    until = 0
    for r in rows:
        if has_title(r): until = r['t']
        elif r['t'] - until > 4: break
    subs = [x for r in rows for x in r['sub']]
    chars = [len(re.sub(r'\s', '', x['text'])) for x in subs]
    punct = [x['text'] for x in subs if re.search(r'[，。？！、,?!；;：:]', x['text']) and not re.search(r'\d,\d', x['text'])]
    return {
        'title_lines': title, 'title_visible_until_s': until,
        'title_height_frac_median': round(st.median([x['bbox']['height'] for r in rows if has_title(r) for x in r['top']]), 4) if until else None,
        'subtitle_frame_ratio': round(sum(1 for r in rows if r['sub']) / max(1, len(rows)), 3),
        'subtitle_chars_median': st.median(chars) if chars else None,
        'subtitle_box_height_frac_median': round(st.median([x['bbox']['height'] for x in subs]), 4) if subs else None,
        'subtitle_box_top_frac_median': round(st.median([x['bbox']['y'] for x in subs]), 4) if subs else None,
        'subtitle_max_lines_per_frame': max((len(r['sub']) for r in rows), default=0),
        'subtitle_boxes_with_punctuation': len(punct), 'subtitle_boxes': len(subs),
        'card_times': [r['t'] for r in rows if r['card']], 'duration_seconds': duration}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--every', type=float, default=2.0, help='seconds between sampled frames')
    ap.add_argument('--wall-regex', default=None, help='regex for background signage to ignore, e.g. "^[择偶定位\\s]{1,4}$"')
    ap.add_argument('--partition', default=None, help='only summarise this partition (e.g. train) to keep holdout unseen')
    a = ap.parse_args()
    out = Path(a.output); out.mkdir(parents=True, exist_ok=True)
    samples = json.loads(Path(a.manifest).read_text())['samples']
    binary = ocr_binary(out); summary = {}
    for r in sorted(samples, key=lambda r: r.get('rank', 0)):
        if a.partition and r.get('partition') != a.partition:
            continue
        d = out / r['sample_id']; frames_dir = d / 'frames'; ocr = d / 'ocr.json'
        if not ocr.exists():
            frames_dir.mkdir(parents=True, exist_ok=True)
            subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', r['path'], '-vf', f'fps={1 / a.every},scale=720:-2', '-q:v', '3',
                            '-start_number', '0', str(frames_dir / 'f-%05d.jpg')], check=True)
            for f in sorted(frames_dir.glob('f-*.jpg')):
                f.rename(frames_dir / f"t-{int(f.stem[2:]) * a.every:08.3f}.jpg")
            subprocess.run([str(binary), str(frames_dir), str(ocr)], check=True)
        summary[r['sample_id']] = {'rank': r.get('rank'), **summarise(json.loads(ocr.read_text()), r.get('duration_seconds'), a.wall_regex)}
        print(json.dumps({'sample': r['sample_id'], 'title_until': summary[r['sample_id']]['title_visible_until_s'],
                          'subtitle_ratio': summary[r['sample_id']]['subtitle_frame_ratio']}, ensure_ascii=False), flush=True)
    (out / 'layout-summary.json').write_text(json.dumps({'method': f'Vision OCR every {a.every} s', 'samples': summary}, ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
