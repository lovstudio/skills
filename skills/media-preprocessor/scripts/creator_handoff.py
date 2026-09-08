#!/usr/bin/env python3
"""Export verified prepared media in original-source time, without regrading it."""
import argparse
from pathlib import Path

from media_preprocessor import read, write, sha, plan_digest, validate_plan, media_check, same_source, probe


def export_handoff(run_dir, destination, decode=False):
    root = Path(run_dir).resolve(strict=True)
    manifest = read(root / 'manifest.json')
    plan = read(root / 'plan.json')
    if manifest.get('status') != 'rendered':
        raise ValueError('Only complete rendered runs can be handed off')
    validate_plan(plan, manifest['source'])
    if plan_digest(plan) != manifest['plan_sha256']:
        raise ValueError('Plan changed after rendering')
    if not same_source(probe(manifest['source']['path']), manifest['source']):
        raise ValueError('Original source identity changed')
    selected = [s for s in plan['segments'] if s['decision'] != 'drop']
    if [s['id'] for s in selected] != [f['id'] for f in manifest['files']]:
        raise ValueError('Prepared coverage is incomplete or reordered')
    files = []
    for segment, entry in zip(selected, manifest['files']):
        path = (root / entry['file']).resolve(strict=True)
        if root not in path.parents or sha(path) != entry['sha256']:
            raise ValueError('Prepared path/hash mismatch: ' + entry['id'])
        if (abs(entry['source_start'] - segment['start']) > .025 or
                abs(entry['source_end'] - segment['end']) > .025 or
                abs(entry['duration'] - (segment['end'] - segment['start'])) > .025):
            raise ValueError('Prepared source mapping changed: ' + entry['id'])
        media_check(path, entry['duration'], manifest['source']['has_audio'], decode)
        files.append({**entry, 'path': str(path), 'local_start': 0,
                      'enhancement_applied': plan.get('grade', {}).get('mode') != 'neutral',
                      'grade': plan.get('grade', {})})
    result = {
        'schema': 'media-preprocess-handoff/v1', 'source': manifest['source'],
        'source_timebase': 'original-seconds', 'segment_timebase': 'local-seconds',
        'basis': plan['basis'], 'files': files, 'segments': plan['segments'],
        'manifest_sha256': sha(root / 'manifest.json'),
        'plan_sha256': manifest['plan_sha256'],
        'verification': {'file_hashes': 'passed', 'source_mapping': 'passed',
                         'full_decode': decode},
        'editorial_status': 'semantic-reviewed' if plan['basis'] == 'semantic-reviewed'
                            else 'full-recording-content-review-required',
        'audio_policy': 'Read original audio using original-source ranges',
        'publication': 'not-published',
    }
    target = Path(destination).resolve()
    if target.exists() and read(target) != result:
        raise ValueError('Existing handoff differs; choose a new revision path')
    target.parent.mkdir(parents=True, exist_ok=True)
    write(target, result)
    lines = ['# 可剪辑素材', '', f"内容状态：{result['editorial_status']}", '',
             '| 片段 | 原片秒数 | 取舍 | 视频 |', '|---|---|---|---|']
    for segment, entry in zip(selected, files):
        title = str(segment.get('title', entry['id'])).replace('|', '\\|').replace('\n', ' ')
        lines.append(f"| {title} | {entry['source_start']:.2f}–{entry['source_end']:.2f} | {segment['decision']} | [MP4](<{entry['path']}>) |")
    target.with_suffix('.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--decode', action='store_true')
    args = parser.parse_args()
    try:
        result = export_handoff(args.run, args.output, args.decode)
        print(f"Verified handoff: {len(result['files'])} files; {result['editorial_status']}")
    except (ValueError, KeyError, OSError) as error:
        parser.exit(2, f'error: {error}\n')


if __name__ == '__main__':
    main()
