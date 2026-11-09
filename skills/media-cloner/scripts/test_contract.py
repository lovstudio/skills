#!/usr/bin/env python3
"""Contract tests for lov-media-cloner on synthetic media.

Needs ffmpeg and Python packages jsonschema and numpy; the whole-file measurement step also
needs opencv-python-headless and pillow (skipped with a notice when missing). Run:
  uv run --with jsonschema --with numpy --with opencv-python-headless --with pillow python scripts/test_contract.py
"""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
CLONER, MEASURE, AUDIO = (SKILL / 'scripts' / n for n in ('cloner.py', 'measure.py', 'build_audio.py'))
DIMS = ['thinking', 'narrative', 'language', 'delivery', 'visual', 'subtitles', 'editing_audio', 'coupling']
passed = []


def call(script, *args, expect=0):
    p = subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True)
    text = p.stdout.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = json.loads(text.splitlines()[-1]) if text else {}
    if expect is not None and p.returncode != expect:
        raise AssertionError(f'{script.name} {args[:1]} exit {p.returncode} (expected {expect}): {text[-600:]} {p.stderr[-400:]}')
    return data


def check(name, condition, detail=''):
    if not condition:
        raise AssertionError(f'{name} failed {detail}')
    passed.append(name)


def make_media(path, tone):
    graph = 'sine=f=300:d=4,volume=0.8[a];anoisesrc=a=0.004:d=4[n];'
    if tone:
        graph += 'sine=f=1000:d=0.75,volume=6,adelay=1000:all=1[t];[a][n][t]amix=inputs=3:duration=first:normalize=0[o]'
    else:
        graph += '[a][n]amix=inputs=2:duration=first:normalize=0[o]'
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc2=size=360x640:rate=25:d=4',
                    '-filter_complex', graph, '-map', '0:v', '-map', '[o]', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-shortest', str(path)], check=True)


TEXT = {'s1': ['大家好，今天聊一个问题。', '你最大的问题不是渠道，而是定位。', '对不对？'],
        's2': ['先说结论。', '你最大的问题不是钱，而是时间。', '我说实话。'],
        's3': ['第一，看市场。', '第二，看你自己。', '你最大的问题不是能力，而是选择。'],
        'h1': ['这是留出样本。', '冻结之前不能读。', '谢谢。']}


def rule(i, dim, evidence, eligible=3, strength='preferred'):
    return {'id': f'{dim}.rule_{i}', 'dimension': dim, 'observation': f'{dim} observation', 'instruction': f'{dim} instruction',
            'strength': strength, 'eligible_sample_count': eligible, 'confidence': 'medium', 'scope': 'all samples',
            'exceptions': [], 'validation': {'method': 'read', 'criterion': 'present'}, 'evidence': evidence}


def draft_for(root):
    q = lambda sid, t, text, **kw: {'kind': 'quote', 'sample_id': sid, 't': t, 'q': text, **kw}
    rules = [rule(0, 'thinking', [q('s1', 1.5, '你最大的问题不是渠道', key='k1'), q('s2', 1.6, '不是钱，而是时间'), q('s3', 2.9, '而是选择')]),
             rule(1, 'narrative', [q('s2', 0.0, '先说结论')], eligible=1),
             rule(2, 'language', [{'use': 'k1'}, q('s2', 3.2, '我说实话')], eligible=2),
             rule(3, 'delivery', [{'kind': 'measurement', 'sample_id': 's1', 'file': 'measurements/training-metrics.json', 'field': 'metrics.han_per_min'}], eligible=1),
             rule(4, 'visual', [{'kind': 'visual', 'sample_id': 's1', 'start': 0.5, 'end': 0.5, 'description': 'test card frame',
                                'local_reference': 'research/measurements/*/contact.jpg'}], eligible=1, strength='optional'),
             rule(5, 'subtitles', [q('s3', 0.0, '第一，看市场')], eligible=1),
             rule(6, 'editing_audio', [{'kind': 'measurement', 'sample_id': 's1', 'file': 'measurements/tones.train.json', 'field': 'results.s1.events'}], eligible=1),
             rule(7, 'coupling', [q('s1', 3.0, '对不对')], eligible=1)]
    return {'schema': 'media-cloner-draft/v1', 'style_id': 'lov-synthetic-style-media-creator', 'display_name': '合成测试风格',
            'version': '0.1.0', 'status': 'ready_with_limits', 'transcript_source': 'synthetic whisper JSON',
            'dimensions': [{'id': d, 'summary': f'{d} summary'} for d in DIMS], 'rules': rules,
            'measurement_files': [{'from': str(root / 'research' / 'training-metrics.json'), 'to': 'measurements/training-metrics.json'},
                                  {'from': str(root / 'research' / 'tones' / 'tones.train.json'), 'to': 'measurements/tones.train.json'}],
            'metrics': {}, 'narrative_templates': [{'id': 'answer_first'}], 'layout_templates': [{'id': 'test_card_9x16'}],
            'audio_visual_triggers': [], 'guardrails': ['no impersonation', 'no source footage', 'no invented facts'],
            'limits': [{'id': 'synthetic', 'detail': 'synthetic media only'}], 'provenance': {'sample_date': 'test'}}


def main():
    if not shutil.which('ffmpeg'):
        print(json.dumps({'status': 'skipped', 'reason': 'ffmpeg missing'}))
        return 0
    have_cv = all(importlib.util.find_spec(m) for m in ('cv2', 'PIL', 'numpy'))
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        r = call(CLONER, 'init', '--slug', 'synthetic', '--creator', '合成博主', '--platform', 'test', '--root', td)
        root = Path(r['project'])
        check('init skeleton', (root / 'research' / 'sources.json').is_file() and (root / 'style-pack').is_dir())
        call(CLONER, 'init', '--slug', 'synthetic', '--creator', 'x', '--root', td, expect=1)
        check('init refuses an existing project', True)
        sources_path = root / 'research' / 'sources.json'
        src = json.loads(sources_path.read_text())
        raw_dir = root / 'research' / 'transcripts' / 'raw'
        for rank, sid in enumerate(['s1', 's2', 's3', 'h1'], 1):
            make_media(root / 'research' / 'sources' / f'{sid}.mp4', tone=(sid == 's1'))
            src['samples'].append({'sample_id': sid, 'rank': rank, 'partition': 'holdout' if sid == 'h1' else 'train',
                                   'title': f'样本 {sid}', 'source_url': f'https://example.com/{sid}', 'path': f'sources/{sid}.mp4'})
            segs = [{'start': k * 1.3, 'end': k * 1.3 + 1.2, 'text': t} for k, t in enumerate(TEXT[sid])]
            (raw_dir / f'{rank:02d}-{sid}.whisper.json').write_text(json.dumps({'segments': segs, 'language': 'zh'}, ensure_ascii=False))
        sources_path.write_text(json.dumps(src, ensure_ascii=False, indent=1))
        check('register', call(CLONER, 'register', '--sources', sources_path)['registered'] == 4)
        call(CLONER, 'freeze-split', '--sources', sources_path, expect=1)
        check('freeze-split needs era_scope and selection', True)
        src = json.loads(sources_path.read_text())
        src.update(era_scope='synthetic era', selection='3 train + 1 holdout chosen before analysis')
        sources_path.write_text(json.dumps(src, ensure_ascii=False, indent=1))
        split = call(CLONER, 'freeze-split', '--sources', sources_path)
        check('freeze-split', split['status'] == 'split_frozen' and split['holdout_ids'] == ['h1'])
        norm_dir = root / 'research' / 'transcripts' / 'normalized'
        sealed = call(MEASURE, 'import', '--manifest', sources_path, '--partition', 'holdout', '--input', raw_dir, '--out', norm_dir, expect=1)
        check('holdout sealed before freeze', 'sealed' in sealed['message'])
        check('import train transcripts', call(MEASURE, 'import', '--manifest', sources_path, '--input', raw_dir, '--out', norm_dir)['imported'] == 3)
        doc = json.loads((norm_dir / 's1.json').read_text())
        check('transcript schema', doc['schema'] == 'media-cloner-transcript/v1' and doc['segments'][1]['text'] == TEXT['s1'][1])
        tones_path = root / 'research' / 'tones' / 'tones.train.json'
        call(MEASURE, 'tones', '--manifest', sources_path, '--out', tones_path)
        events = json.loads(tones_path.read_text())['results']
        check('tone scan finds the 1 kHz separator', events['s1']['events'] and abs(events['s1']['events'][0][0] - 1.0) <= 0.25
              and not events['s2']['events'] and 'h1' not in events, str(events))
        meas_dir = root / 'research' / 'measurements'
        if have_cv:
            call(MEASURE, 'media', '--manifest', sources_path, '--out', meas_dir)
            m = json.loads((meas_dir / 's1' / 'metrics.json').read_text())
            check('media measurement', m['duration_seconds'] > 3.9 and (meas_dir / 's1' / 'contact.jpg').is_file()
                  and not (meas_dir / 'h1').exists())
        else:
            print(json.dumps({'notice': 'opencv/pillow missing: media measurement not exercised'}))
            (meas_dir / 's1').mkdir(parents=True, exist_ok=True)
            (meas_dir / 's1' / 'contact.jpg').write_bytes(b'placeholder')
        metrics = call(CLONER, 'metrics', '--sources', sources_path, '--transcripts', norm_dir, '--tones', tones_path,
                       '--measurements', meas_dir, '--out', root / 'research' / 'training-metrics.json')
        tm = json.loads((root / 'research' / 'training-metrics.json').read_text())
        check('metrics are training-only', metrics['samples'] == 3 and 'han_per_min' in tm['metrics']
              and all(r['sample_id'] != 'h1' for r in tm['per_sample']))
        draft_path = root / 'research' / 'rules-draft.json'
        pack = root / 'style-pack' / 'synthetic-v0.1'
        bad = draft_for(root)
        bad['rules'][1]['evidence'] = [{'kind': 'quote', 'sample_id': 'h1', 't': 0, 'q': '这是留出样本'}]
        draft_path.write_text(json.dumps(bad, ensure_ascii=False))
        fail = call(CLONER, 'build', '--draft', draft_path, '--sources', sources_path, '--transcripts', norm_dir, '--out', pack, expect=1)
        check('build rejects holdout evidence', any('holdout' in e['error'] for e in fail['errors']) and not pack.exists())
        bad = draft_for(root)
        bad['rules'][0]['evidence'][1]['q'] = '这句话并不存在'
        draft_path.write_text(json.dumps(bad, ensure_ascii=False))
        fail = call(CLONER, 'build', '--draft', draft_path, '--sources', sources_path, '--transcripts', norm_dir, '--out', pack, expect=1)
        check('build rejects unresolvable quotes', any(e['error'] == 'quote not found in transcript' for e in fail['errors'])
              and (root / 'research' / 'rules-draft.build-report.json').is_file())
        bad = draft_for(root)
        bad['rules'][0]['eligible_sample_count'] = 2
        draft_path.write_text(json.dumps(bad, ensure_ascii=False))
        call(CLONER, 'build', '--draft', draft_path, '--sources', sources_path, '--transcripts', norm_dir, '--out', pack, expect=1)
        check('build rejects a denominator below support', not pack.exists())
        draft_path.write_text(json.dumps(draft_for(root), ensure_ascii=False))
        built = call(CLONER, 'build', '--draft', draft_path, '--sources', sources_path, '--transcripts', norm_dir, '--out', pack,
                     '--project-root', root)
        check('build', built['rules'] == 8 and built['evidence'] == 10 and built['warnings'] == 0, str(built))
        profile = json.loads((pack / 'style-profile.json').read_text())
        ev = [json.loads(l) for l in (pack / 'evidence.jsonl').read_text().splitlines()]
        check('quotes are exact substrings', all(e['quote'] in e['source_excerpt'] for e in ev if e['kind'] == 'quote'))
        check('evidence reuse by key', profile['rules'][2]['evidence_ids'][0] == profile['rules'][0]['evidence_ids'][0])
        check('support derived from evidence', profile['rules'][0]['support_count'] == 3 and profile['holdout_sample_ids'] == ['h1'])
        check('measurement copies stay training-only', 'h1' not in (pack / 'measurements' / 'tones.train.json').read_text())
        v = call(CLONER, 'verify', '--pack', pack, '--sources', sources_path, '--transcripts', norm_dir)
        check('verify', v['status'] == 'passed' and v['transcripts_checked'])
        z = call(CLONER, 'freeze', '--pack', pack, '--sources', sources_path, '--transcripts', norm_dir)
        check('freeze', z['status'] == 'frozen' and (pack / 'FROZEN.json').is_file())
        call(CLONER, 'build', '--draft', draft_path, '--sources', sources_path, '--transcripts', norm_dir, '--out', pack, expect=1)
        check('frozen pack cannot be rebuilt in place', True)
        check('holdout unsealed after freeze',
              call(MEASURE, 'import', '--manifest', sources_path, '--partition', 'holdout', '--frozen', pack, '--input', raw_dir, '--out', norm_dir)['imported'] == 1)
        original = (pack / 'style-profile.json').read_text()
        (pack / 'style-profile.json').write_text(original.replace('thinking instruction', 'thinking instruction!'))
        tampered = call(CLONER, 'verify', '--pack', pack, expect=1)
        check('tamper detected after freeze', any('changed after freeze' in p for p in tampered['problems']))
        call(MEASURE, 'import', '--manifest', sources_path, '--partition', 'holdout', '--frozen', pack, '--input', raw_dir, '--out', norm_dir, expect=1)
        check('tampered pack keeps holdout sealed', True)
        (pack / 'style-profile.json').write_text(original)
        call(CLONER, 'holdout-init', '--pack', pack)
        report_path = pack / 'holdout-report.json'
        report = json.loads(report_path.read_text())
        results = report['samples']['h1']['results']
        for k, rid in enumerate(results):
            results[rid] = {'result': ['hit', 'partial', 'miss', 'not_applicable'][k % 4], 'note': 'read in full'}
        report['checked_at'] = '2026-01-01'
        missing = dict(results)
        missing.pop(next(iter(missing)))
        report['samples']['h1']['results'] = missing
        report_path.write_text(json.dumps(report, ensure_ascii=False))
        check('holdout-check flags missing pairs', call(CLONER, 'holdout-check', '--pack', pack, expect=1)['status'] == 'incomplete')
        report['samples']['h1']['results'] = results
        report_path.write_text(json.dumps(report, ensure_ascii=False))
        hc = call(CLONER, 'holdout-check', '--pack', pack, '--write-summary')
        check('holdout-check', hc['status'] == 'passed' and hc['summary']['recorded'] == 8 and hc['summary']['hit'] == 2)
        check('status after holdout', call(CLONER, 'status', '--project', root)['stage'] == 'holdout_checked')
        (root / 'deliverables' / 'guide.md').write_text('# guide\n')
        check('status after guide', call(CLONER, 'status', '--project', root)['stage'] == 'guide_written')
        voice = td / 'voice.wav'
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'anoisesrc=color=pink:a=0.3:d=6',
                        '-af', 'tremolo=f=4:d=0.8', str(voice)], check=True)
        voices = [{'at_seconds': 0, 'src': 'voice.wav', 'in_seconds': 0, 'duration_seconds': 2.0},
                  {'at_seconds': 2.8, 'src': 'voice.wav', 'in_seconds': 3.0, 'duration_seconds': 2.2}]
        plan = td / 'audio-plan.json'
        plan.write_text(json.dumps({'total_seconds': 5.0, 'target': {'integrated_lufs': -16, 'true_peak_dbtp': -1.5}, 'voice': voices}))
        audio = call(AUDIO, '--plan', plan, '--output', td / 'voice-only.m4a')
        check('audio bed loudness', audio['true_peak_dbtp'] <= -1.0 and abs(audio['integrated_lufs'] + 16) < 1.0, str(audio))
        plan.write_text(json.dumps({'total_seconds': 5.0, 'target': {'integrated_lufs': -16, 'true_peak_dbtp': -1.5}, 'voice': voices,
                                    'tones': [{'at_seconds': 2.0, 'duration_seconds': 0.8, 'frequency_hz': 1000, 'db_over_speech': 9}]}))
        call(AUDIO, '--plan', plan, '--output', td / 'mix.m4a')
        import numpy as np
        raw = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(td / 'mix.m4a'), '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'],
                             capture_output=True, check=True).stdout
        x = np.frombuffer(raw, dtype=np.float32)
        level = lambda a, b: 20 * np.log10(np.sqrt(np.mean(x[int(a * 16000):int(b * 16000)] ** 2)) + 1e-9)
        gap = level(2.15, 2.65) - level(0.2, 1.8)
        check('separator tone sits about 9 dB over speech', 6.5 < gap < 11.5, f'{gap:.1f} dB')
    for text, expected in [('复刻一下小红书博主的这个视频风格，他的 ID 是「某某」', True),
                           ('参考这个抖音账号的视频风格，做成风格包和剪辑模板', True),
                           ('Clone this creator\'s video style from their channel', True),
                           ('只要下载这个视频链接', False), ('模仿这篇公众号文章的文风改写', False),
                           ('克隆这个博主的声音', False), ('用晓暖的风格把这段连麦录像剪成切片', False)]:
        check(f'route: {text}', call(CLONER, 'route', '--request', text)['activate'] is expected)
    check('doctor', call(CLONER, 'doctor', expect=None)['missing'] == [])
    print(json.dumps({'status': 'passed', 'checks': len(passed)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except AssertionError as exc:
        print(json.dumps({'status': 'failed', 'passed_before_failure': len(passed), 'error': str(exc)}, ensure_ascii=False))
        sys.exit(1)
