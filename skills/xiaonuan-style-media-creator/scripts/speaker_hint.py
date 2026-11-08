#!/usr/bin/env python3
"""Write a readable transcript with an acoustic speaker hint per ASR segment.

Call-in guests usually reach the stream through a different audio path than the host's
microphone. For each segment the 4–7.5 kHz / 0.3–4 kHz energy ratio is measured and split
into two clusters; H (lower cluster) and G (higher) are hints only. When the clusters are
less than --min-gap dB apart every segment is marked "?". Confirm roles by reading.

Input: a Whisper-style JSON with "segments" [{start, end, text}] and the source media.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def main():
    import numpy as np
    import librosa
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--media', required=True)
    ap.add_argument('--transcript', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--min-gap', type=float, default=6.0)
    a = ap.parse_args()
    sr = 32000
    raw = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', a.media, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    segs = json.loads(Path(a.transcript).read_text())['segments']; feats = []
    for s in segs:
        seg = x[int(s['start'] * sr):int(s['end'] * sr)]
        if len(seg) < sr * 0.25: feats.append(None); continue
        S = np.abs(librosa.stft(seg, n_fft=1024, hop_length=320)) ** 2; f = librosa.fft_frequencies(sr=sr, n_fft=1024)
        e = S.sum(0); v = e > np.percentile(e, 50)
        feats.append(float(10 * np.log10((S[(f > 4000) & (f < 7500)][:, v].sum() + 1e-12) / (S[(f > 300) & (f < 4000)][:, v].sum() + 1e-12))))
    vals = np.array([v for v in feats if v is not None]); c = np.array([np.percentile(vals, 15), np.percentile(vals, 85)])
    for _ in range(20):
        lab = np.abs(vals[:, None] - c[None]).argmin(1); c = np.array([vals[lab == i].mean() if (lab == i).any() else c[i] for i in range(2)])
    lo, hi = sorted(c); thr = (lo + hi) / 2; gap = hi - lo
    lines = []
    for s, v in zip(segs, feats):
        spk = '?' if v is None or gap < a.min_gap else ('H' if v < thr - 1.5 else 'G' if v > thr + 1.5 else '?')
        m, sec = divmod(s['start'], 60); lines.append(f"[{int(m):02d}:{sec:04.1f}] {spk} {s['text'].strip()}")
    head = f"# centroids {lo:.1f}/{hi:.1f} dB, gap {gap:.1f} dB (hint only; confirm by reading)\n"
    Path(a.output).write_text(head + '\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'written', 'output': a.output, 'gap_db': round(float(gap), 1), 'segments': len(segs)}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
