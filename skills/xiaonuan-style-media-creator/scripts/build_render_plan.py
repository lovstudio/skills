#!/usr/bin/env python3
"""Turn a validated edit plan into render data for templates/remotion.

Recording sections become video segments (OffthreadVideo from `in_seconds`); when the
source span is shorter than the section, the remainder is a freeze frame so a voice tail
can finish. Separator sections become colour bars. Title, card, call-in window and
single-line subtitles are converted to frame ranges on the same timeline.
"""
import argparse
import json
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--plan', required=True, help='edit-plan.json that passed style_media.py validate-plan')
    ap.add_argument('--media', action='append', default=[], metavar='REF=PUBLIC_PATH',
                    help='map a section source ref to a file under templates/remotion/public, e.g. mezz=media/mezz.mp4')
    ap.add_argument('--audio', default='audio/mix.m4a', help='audio bed path under public/ (from build_audio.py)')
    ap.add_argument('--output', required=True)
    a = ap.parse_args()
    plan = json.loads(Path(a.plan).read_text(encoding='utf-8'))
    media = dict(m.split('=', 1) for m in a.media)
    fps = plan['fps']; F = lambda s: int(round(s * fps))
    total = F(plan['duration_seconds'])
    video, bars = [], None
    for s in plan['sections']:
        start, frames = F(s['start_seconds']), F(s['end_seconds']) - F(s['start_seconds'])
        if s['role'] == 'separator':
            bars = {'from': start, 'frames': frames}
            continue
        src = s['source']
        if src['type'] != 'recording':
            print(json.dumps({'status': 'failed', 'message': f"section {s['id']} has no recording; only recording sections can be rendered"}, ensure_ascii=False))
            return 1
        if src['ref'] not in media:
            print(json.dumps({'status': 'failed', 'message': f"missing --media mapping for ref '{src['ref']}'"}, ensure_ascii=False))
            return 1
        sf = F(src['in_seconds'])
        avail = F(src['out_seconds']) - sf if 'out_seconds' in src else frames
        live = min(frames, avail)
        video.append({'from': start, 'frames': live, 'src': media[src['ref']], 'startFrom': sf})
        if live < frames:
            video.append({'from': start + live, 'frames': frames - live, 'src': media[src['ref']], 'freeze': sf + live - 1})
    if bars is None:
        bars = {'from': total, 'frames': 0}
    t = plan['title']
    card = plan.get('card')
    out = {
        'fps': fps, 'width': 1080, 'height': 1920, 'frames': total, 'video': video, 'bars': bars, 'audio': a.audio,
        'title': {'lines': t['lines'], 'fromF': F(t['start_seconds']), 'toF': F(t['end_seconds'])},
        'card': None if not card else {'header': card['header'], 'lines': card['lines'], 'fromF': F(card['start_seconds']), 'toF': F(card['end_seconds'])},
        'callIn': {'fromF': 0, 'toF': total} if plan['call_in_window']['enabled'] else None,
        'subtitles': [{'fromF': F(c['start_seconds']), 'toF': F(c['end_seconds']), 'text': c['text']} for s in plan['sections'] for c in s['subtitles']],
    }
    Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    Path(a.output).write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'written', 'output': a.output, 'frames': total, 'segments': len(video), 'subtitles': len(out['subtitles'])}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
