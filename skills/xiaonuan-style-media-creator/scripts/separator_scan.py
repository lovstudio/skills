#!/usr/bin/env python3
"""Find test-tone separators (default 1 kHz) in every sample of a manifest.

A 0.25 s window counts when the peak inside [low, high] Hz is more than --ratio times the
median spectral magnitude and the window RMS is above --min-dbfs. Consecutive windows are
merged into events. Use it to locate colour-bar separators and splices; it does not look at
the picture, so confirm events with frames.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def main():
    import numpy as np
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--low', type=float, default=980)
    ap.add_argument('--high', type=float, default=1020)
    ap.add_argument('--ratio', type=float, default=2000)
    ap.add_argument('--min-dbfs', type=float, default=-15)
    a = ap.parse_args()
    out = {}
    for r in sorted(json.loads(Path(a.manifest).read_text())['samples'], key=lambda r: r.get('rank', 0)):
        raw = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', r['path'], '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], capture_output=True, check=True).stdout
        x = np.frombuffer(raw, dtype=np.float32); win = 4000; hits = []
        f = np.fft.rfftfreq(win, 1 / 16000); band = (f > a.low) & (f < a.high)
        for i in range(0, len(x) - win, win):
            seg = x[i:i + win]; X = np.abs(np.fft.rfft(seg * np.hanning(win)))
            if X[band].max() / (np.median(X) + 1e-9) > a.ratio and 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9) > a.min_dbfs:
                hits.append(i / 16000)
        events = []
        for t in hits:
            if events and t - events[-1][1] <= 0.26: events[-1][1] = t + 0.25
            else: events.append([t, t + 0.25])
        out[r['sample_id']] = {'rank': r.get('rank'), 'events': [[round(s, 2), round(e, 2)] for s, e in events]}
        print(json.dumps({'sample': r['sample_id'], 'events': out[r['sample_id']]['events']}), flush=True)
    Path(a.output).write_text(json.dumps({'method': f'0.25 s windows, {a.low}-{a.high} Hz peak/median > {a.ratio}, RMS > {a.min_dbfs} dBFS', 'results': out}, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
