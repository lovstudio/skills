#!/usr/bin/env python3
"""Build one continuous audio bed for an edit plan.

Recording sections take `section length` seconds of voice starting at `in_seconds`
(the voice may run past a video freeze); separator sections get a 1 kHz tone placed a
fixed number of dB above the measured speech RMS. Voice is normalised with two-pass
loudnorm. No music is added: the style has no BGM in the body.
Requires ffmpeg; numpy for the speech RMS measurement.
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


def speech_rms_db(path):
    import numpy as np
    raw = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(path), '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32); w = 1600
    fr = np.array([np.sqrt(np.mean(x[i:i + w] ** 2)) for i in range(0, len(x) - w, w)])
    db = 20 * np.log10(fr + 1e-9); act = db[db > -50]
    return float(20 * np.log10(np.sqrt(np.mean((10 ** (act / 20)) ** 2))))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--plan', required=True)
    ap.add_argument('--voice', action='append', default=[], metavar='REF=WAV', help='voice track per source ref, aligned to in_seconds')
    ap.add_argument('--output', required=True, help='.m4a (AAC 192k) written for templates/remotion/public/audio')
    ap.add_argument('--sample-rate', type=int, default=48000)
    a = ap.parse_args()
    plan = json.loads(Path(a.plan).read_text(encoding='utf-8'))
    voices = dict(v.split('=', 1) for v in a.voice)
    target = plan['loudness']; sr = a.sample_rate
    with tempfile.TemporaryDirectory() as td:
        td = Path(td); parts = []
        for i, s in enumerate(plan['sections']):
            dur = s['end_seconds'] - s['start_seconds']; part = td / f'p{i:03d}.wav'
            if s['role'] == 'separator' or s['source']['type'] != 'recording':
                run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'anullsrc=r={sr}:cl=mono', '-t', f'{dur:.6f}', str(part)])
            else:
                ref = s['source']['ref']
                if ref not in voices:
                    raise SystemExit(json.dumps({'status': 'failed', 'message': f"missing --voice for ref '{ref}'"}))
                st = s['source']['in_seconds']
                run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', voices[ref], '-af',
                     f'atrim={st:.6f}:{st + dur:.6f},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,areverse,afade=t=in:d=0.008,areverse,apad,atrim=0:{dur:.6f}',
                     '-ar', str(sr), '-ac', '1', str(part)])
            parts.append(part)
        lst = td / 'list.txt'; lst.write_text(''.join(f"file '{p}'\n" for p in parts))
        concat = td / 'voice.wav'
        run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c', 'copy', str(concat)])
        m = loudness(concat)
        norm = td / 'voice-norm.wav'
        run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', str(concat), '-af',
             f"loudnorm=I={target['integrated_lufs']}:TP={min(target['true_peak_dbtp'], -1.0)}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
             f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true", '-ar', str(sr), str(norm)])
        rms = speech_rms_db(norm); tone_db = rms + target['separator_tone_db_over_speech']
        amp = 10 ** ((tone_db + 3.0103) / 20)            # sine peak for the requested RMS
        layers = [str(norm)]
        for i, s in enumerate(plan['sections']):
            if s['role'] != 'separator':
                continue
            dur = s['end_seconds'] - s['start_seconds']; tone = td / f'tone{i}.wav'
            run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'sine=frequency=1000:sample_rate={sr}:duration={dur:.6f}', '-af',
                 # lavfi sine defaults to amplitude 1/8, hence the factor 8
                 f'volume={amp * 8:.6f},afade=t=in:d=0.005,afade=t=out:st={max(0.0, dur - 0.005):.6f}:d=0.005,adelay={int(round(s["start_seconds"] * 1000))}',
                 '-ar', str(sr), '-ac', '1', str(tone)])
            layers.append(str(tone))
        mix = td / 'mix.wav'
        if len(layers) == 1:
            run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', layers[0], '-ac', '2', str(mix)])
        else:
            inputs = sum((['-i', l] for l in layers), [])
            run(['ffmpeg', '-nostdin', '-v', 'error', '-y', *inputs, '-filter_complex',
                 ''.join(f'[{k}:a]' for k in range(len(layers))) + f'amix=inputs={len(layers)}:duration=first:normalize=0[m]', '-map', '[m]', '-ac', '2', str(mix)])
        Path(a.output).parent.mkdir(parents=True, exist_ok=True)
        run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', str(mix), '-c:a', 'aac', '-b:a', '192k', a.output])
        final = loudness(mix)
    report = {'status': 'written', 'output': a.output, 'integrated_lufs': float(final['input_i']), 'true_peak_dbtp': float(final['input_tp']),
              'speech_rms_dbfs': round(rms, 2), 'tone_rms_dbfs': round(tone_db, 2), 'separators': len(layers) - 1}
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['true_peak_dbtp'] <= -1.0 else 2


if __name__ == '__main__':
    sys.exit(main())
