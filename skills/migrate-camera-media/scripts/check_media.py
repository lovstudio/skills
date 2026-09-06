#!/usr/bin/env python3
"""Decode samples selected from a verified source manifest, never from globs."""
import argparse
import concurrent.futures as cf
import json
from pathlib import Path
import shutil
import subprocess
from camera_media import read, save, safe_rel, now, snapshot


def check(path, root, ffmpeg, ffprobe):
    result = {'path': str(path.relative_to(root)), 'passed': False}
    try:
        if path.suffix.lower() in ('.jpg', '.jpeg'):
            from PIL import Image
            with Image.open(path) as im:
                result['dimensions'] = list(im.size)
                result['frames_decoded'] = getattr(im, 'n_frames', 1)
                for i in range(result['frames_decoded']): im.seek(i); im.load()
        else:
            raw = subprocess.run([ffprobe, '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(path)],
                                 capture_output=True, text=True, check=True, timeout=60)
            info = json.loads(raw.stdout); duration = float(info['format']['duration'])
            if duration <= 0: raise ValueError('Invalid duration')
            result['duration_seconds'] = duration; result['samples'] = []
            for t in (0, duration/2, max(0, duration-1)):
                run = subprocess.run([ffmpeg, '-nostdin', '-hide_banner', '-v', 'error', '-threads', '2', '-ss', str(t),
                                      '-i', str(path), '-map', '0:v:0', '-frames:v', '1', '-progress', 'pipe:1', '-f', 'null', '-'],
                                     capture_output=True, text=True, check=True, timeout=90)
                frames = [int(line.split('=', 1)[1]) for line in run.stdout.splitlines() if line.startswith('frame=')]
                if run.stderr.strip() or not frames or max(frames) < 1: raise RuntimeError(run.stderr or 'No frame decoded')
                result['samples'].append(t)
            if any(s.get('codec_type') == 'audio' for s in info['streams']):
                run = subprocess.run([ffmpeg, '-nostdin', '-hide_banner', '-v', 'error', '-threads', '2', '-ss', str(duration/2),
                                      '-i', str(path), '-map', '0:a:0', '-t', '1', '-f', 'null', '-'],
                                     capture_output=True, text=True, check=True, timeout=60)
                if run.stderr.strip(): raise RuntimeError(run.stderr)
                result['audio_sample'] = 'passed'
        result['passed'] = True
    except Exception as exc: result['error'] = str(exc)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    manifest = read(args.report/'manifest.json')
    if manifest.get('status') != 'verified': parser.error('Complete copy and checksum verification first')
    root = Path(manifest['destination']); snapshot(root)
    files = [root/safe_rel(p) for p in manifest['snapshot']['files']]
    photos = {'.jpg', '.jpeg'}; movies = {'.mp4', '.mov', '.mxf', '.mts', '.m2ts'}
    selected = [p for p in files if p.suffix.lower() in photos | movies]
    ffmpeg, ffprobe = shutil.which('ffmpeg'), shutil.which('ffprobe')
    if any(p.suffix.lower() in movies for p in selected) and not (ffmpeg and ffprobe):
        parser.error('ffmpeg and ffprobe are required for movie samples')
    if any(p.suffix.lower() in photos for p in selected):
        try: import PIL
        except ImportError: parser.error('Pillow is required for JPEG/MPO decoding')
    with cf.ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda p: check(p, root, ffmpeg, ffprobe), selected))
    report = {'checked_at': now(), 'checked_files': len(results), 'passed': all(r['passed'] for r in results),
              'results': results, 'rsv_not_recovered': [str(p.relative_to(root)) for p in files if p.suffix.lower()=='.rsv'],
              'other_files_not_decoded': [str(p.relative_to(root)) for p in files if p not in selected],
              'scope': 'JPEG/MPO frames decoded; movie first/middle/last frame and a one-second audio sample decoded. No full-movie decode or human audiovisual review.'}
    save(args.report/'media-qc.json', report)
    print(json.dumps({'passed': report['passed'], 'checked_files': len(results),
                      'failed_files': [r for r in results if not r['passed']]}, ensure_ascii=False))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
