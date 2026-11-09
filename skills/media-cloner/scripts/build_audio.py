#!/usr/bin/env python3
"""Build one continuous, loudness-normalised audio bed for a style-template render.

Audio plan (JSON, paths relative to the plan file):
{
  "total_seconds": 72.5, "sample_rate": 48000,
  "target": {"integrated_lufs": -16, "true_peak_dbtp": -1.5},
  "voice": [{"at_seconds": 0, "src": "media/talk.wav", "in_seconds": 12.0, "duration_seconds": 10.2}],
  "tones": [{"at_seconds": 10.2, "duration_seconds": 0.8, "frequency_hz": 1000, "db_over_speech": 9}],
  "music": [{"at_seconds": 0, "src": "media/bed.wav", "in_seconds": 0, "duration_seconds": 72.5,
             "db_under_speech": 18, "fade_seconds": 1.5}]
}
Voice clips get 8 ms edge fades and are placed on one timeline, then normalised with two-pass
loudnorm. Tones and music are set relative to the measured speech RMS, so a separator keeps the
same relation to speech that the reference measured. Only use media you own or have licensed.
Requires ffmpeg; numpy for the speech RMS.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f'{cmd[0]} exit={p.returncode}: {p.stderr[-600:]}')
    return p


def loudness(path):
    err = run(['ffmpeg', '-nostdin', '-hide_banner', '-i', str(path), '-af', 'loudnorm=print_format=json', '-f', 'null', '-']).stderr
    return json.loads(err[err.rindex('{'):err.rindex('}') + 1])


def rms_db(path):
    import numpy as np
    raw = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(path), '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    w = 1600
    frames = np.array([np.sqrt(np.mean(x[i:i + w] ** 2)) for i in range(0, max(0, len(x) - w), w)])
    db = 20 * np.log10(frames + 1e-9)
    active = db[db > -50]
    if not len(active):
        raise RuntimeError(f'{Path(path).name}: no active signal above -50 dBFS')
    return float(20 * np.log10(np.sqrt(np.mean((10 ** (active / 20)) ** 2))))


def clip(src, start, dur, sr, out, fade=0.008):
    probe = run(['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=index', '-of', 'csv=p=0', str(src)]).stdout
    if not probe.strip():
        raise SystemExit(json.dumps({'status': 'failed', 'message': f'{Path(src).name} has no audio stream; point voice clips at the voice track'}))
    run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', str(src), '-af',
         f'atrim={start:.6f}:{start + dur:.6f},asetpts=PTS-STARTPTS,afade=t=in:d={fade},areverse,afade=t=in:d={fade},areverse,'
         f'apad,atrim=0:{dur:.6f}', '-ar', str(sr), '-ac', '1', str(out)])


def place(layers, total, sr, out):
    """Sum mono layers [(path, at_seconds, gain_db)] onto a silent timeline of `total` seconds."""
    inputs = ['-f', 'lavfi', '-t', f'{total:.6f}', '-i', f'anullsrc=r={sr}:cl=mono']
    graph = []
    for k, (path, at, gain) in enumerate(layers, 1):
        inputs += ['-i', str(path)]
        graph.append(f'[{k}:a]volume={gain:.4f}dB,adelay={int(round(at * sr))}S:all=1[l{k}]')
    mix = '[0:a]' + ''.join(f'[l{k}]' for k in range(1, len(layers) + 1))
    graph.append(f'{mix}amix=inputs={len(layers) + 1}:duration=first:normalize=0[m]')
    run(['ffmpeg', '-nostdin', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(graph), '-map', '[m]',
         '-ar', str(sr), '-ac', '1', str(out)])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--plan', required=True, help='audio plan JSON')
    ap.add_argument('--output', required=True, help='.m4a (AAC 192 kbps stereo), e.g. work/remotion/public/audio/mix.m4a')
    ap.add_argument('--work-dir', help='keep intermediate WAV files here for inspection')
    a = ap.parse_args()
    plan_path = Path(a.plan).expanduser().resolve()
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    base = plan_path.parent
    sr, total, target = int(plan.get('sample_rate', 48000)), float(plan['total_seconds']), plan['target']
    true_peak = min(float(target.get('true_peak_dbtp', -1.0)), -1.0)
    if not plan.get('voice'):
        raise SystemExit(json.dumps({'status': 'failed', 'message': 'audio plan has no voice clips'}))
    with tempfile.TemporaryDirectory() as tmp:
        td = Path(a.work_dir).expanduser().resolve() if a.work_dir else Path(tmp)
        td.mkdir(parents=True, exist_ok=True)
        voice = []
        for k, v in enumerate(plan['voice']):
            if v['at_seconds'] + v['duration_seconds'] > total + 0.05:
                raise SystemExit(json.dumps({'status': 'failed', 'message': f'voice clip {k} runs past total_seconds'}))
            part = td / f'v{k:03d}.wav'
            clip(base / v['src'], float(v['in_seconds']), float(v['duration_seconds']), sr, part)
            voice.append((part, float(v['at_seconds']), 0.0))
        timeline = td / 'voice.wav'
        place(voice, total, sr, timeline)
        m = loudness(timeline)
        normed = td / 'voice-norm.wav'
        run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', str(timeline), '-af',
             f"loudnorm=I={target['integrated_lufs']}:TP={true_peak}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
             f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true",
             '-ar', str(sr), '-ac', '1', str(normed)])
        speech = rms_db(normed)
        layers = [(normed, 0.0, 0.0)]
        for k, t in enumerate(plan.get('tones', [])):
            dur = float(t['duration_seconds'])
            tone = td / f't{k:03d}.wav'
            peak_db = speech + float(t.get('db_over_speech', 9)) + 3.0103   # sine peak for the requested RMS
            # lavfi sine defaults to amplitude 1/8; the factor 8 restores full scale before the gain
            run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'lavfi', '-i',
                 f"sine=frequency={t.get('frequency_hz', 1000)}:sample_rate={sr}:duration={dur:.6f}", '-af',
                 f'volume={8 * 10 ** (peak_db / 20):.6f},afade=t=in:d=0.005,afade=t=out:st={max(0.0, dur - 0.005):.6f}:d=0.005',
                 '-ar', str(sr), '-ac', '1', str(tone)])
            layers.append((tone, float(t['at_seconds']), 0.0))
        for k, mu in enumerate(plan.get('music', [])):
            dur, fade = float(mu['duration_seconds']), float(mu.get('fade_seconds', 1.0))
            bed = td / f'm{k:03d}.wav'
            run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', str(base / mu['src']), '-af',
                 f"atrim={float(mu.get('in_seconds', 0)):.6f}:{float(mu.get('in_seconds', 0)) + dur:.6f},asetpts=PTS-STARTPTS,"
                 f'afade=t=in:d={fade},afade=t=out:st={max(0.0, dur - fade):.6f}:d={fade}', '-ar', str(sr), '-ac', '1', str(bed)])
            gain = speech - float(mu.get('db_under_speech', 18)) - rms_db(bed)
            layers.append((bed, float(mu['at_seconds']), gain))
        mix = td / 'mix.wav'
        place(layers, total, sr, mix)
        out = Path(a.output).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', str(mix), '-ac', '2', '-c:a', 'aac', '-b:a', '192k', str(out)])
    # Measure the delivered file: the mono-to-stereo upmix lowers each channel by 3 dB at equal loudness.
    final = loudness(out)
    report = {'status': 'written', 'output': str(out), 'integrated_lufs': float(final['input_i']),
              'true_peak_dbtp': float(final['input_tp']), 'speech_rms_dbfs': round(speech, 2),
              'voice_clips': len(voice), 'tones': len(plan.get('tones', [])), 'music_layers': len(plan.get('music', []))}
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['true_peak_dbtp'] <= -1.0 else 2


if __name__ == '__main__':
    sys.exit(main())
