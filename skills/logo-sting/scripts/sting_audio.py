#!/usr/bin/env python3
"""Sonic logo for the logo sting, locked to the frames of a timing file (logo-sting-timing/v1) so that every hit
lands on the same frame as the picture.

  python3 sting_audio.py --timing timing.json --out sting.wav     # 48 kHz stereo 16-bit PCM, deterministic

Frames are local to the sting (frame 0 = its first frame):
  0          a soft low button lands the bar line the sting starts on, then the point of light inhales (a reverse
             swell) and is cut off by
  HITS       one stroke per beat: tight impact (kick + click + crack), a 150-400 Hz body thump and a 2-4 kHz snap
             (what phone speakers actually play), and a tuned metal hit rising D4 / A4 / D5 (then A5 D6 ...), panned
             with the stroke from left to right, each after the first led in by a short reverse suck
  GATE       riser + reverse of the big hit build to here, then everything is gated to near-silence until the bar:
             the suck-out
  BAR        the wordmark: sub-drop boom (55 -> 30 Hz, saturated so phones hear its harmonics; below 60 Hz cut
             ~3.9 dB), punch, body thump, transient, 2-4 kHz snap, noise crack with a bit-crushed edge (the negative
             frame / RGB split), an FM-bell D chord, high shimmer and air, a long stereo reverb
  PULSES     the glow breathes on the next beats: ping-pong echoes of the bell, decaying
  CUT        the picture cuts to black before the end; the tail is gated out by then
Everything is synthesised with numpy from fixed seeds; the length is exactly round(dur / fps * 48000) samples and the
true peak is normalised to -1 dBTP (4x oversampled estimate). Frame offsets that were designed at 30 fps (the 3-frame
margin before the gate, the fade at the cut) keep their duration at other rates.
"""
import argparse
import json
import math
import time
import wave
from pathlib import Path

import numpy as np

SR = 48000
SCHEMA = "logo-sting-timing/v1"

# Frames local to the sting, set from the timing file by configure() (defaults: the reference sting).
FPS = 30
HIT = [18, 36, 54]
BAR = 72
PULSES = [90, 108, 126]
DUR = 144
CUT = 140
GATE = 69
N = int(round(DUR / FPS * SR))

# Tone and level balance, set by measurement against the previous version (band RMS in the first 150 ms of each
# stroke / 300 ms of the big hit, relative to its own 400 Hz-2 kHz band): below 60 Hz on the big hit -3.9 dB,
# 150-400 Hz body +4 dB (strokes +4..+10, they had almost none), 2-4 kHz crack +4 dB (strokes +4..+7). Momentary
# loudness: strokes level with each other (pitch carries the rise), the big hit ~5 LU above them.
STROKE_LVL = (0.56, 0.62, 0.58)
STROKE_BODY, STROKE_SNAP = 0.8, 2.0
BIG_BODY, BIG_SNAP = 1.2, 2.0
SUB_SHELF_HZ, SUB_SHELF_DB = 75, -5.0  # RBJ shelf; nets ~-3.9 dB below 60 Hz after the limiter and soft clip
LIMIT_DB = -6.0  # look-ahead limiter threshold under the raw peak: shaves the stacked onset, keeps the sting dense
DRIVE = 1.6  # master soft clip
LAND = 0.7  # the button on frame 0
TP_DB = -1.0


def at(frame):
    return int(round(frame / FPS * SR))


def tt(sec):
    return np.arange(int(sec * SR)) / SR


def f30(k):
    """k frames at 30 fps (the rate the sting was designed at), as frames at FPS."""
    return int(math.floor(k * FPS / 30 + 0.5))


def configure(t):
    """Take FPS, HIT, BAR, PULSES, DUR, CUT and GATE from a logo-sting-timing/v1 object."""
    global FPS, HIT, BAR, PULSES, DUR, CUT, GATE, N
    if t.get("schema") != SCHEMA:
        raise ValueError(f"not a {SCHEMA} file (schema {t.get('schema')!r})")
    FPS = t["fps"]
    HIT, BAR, PULSES = [int(h) for h in t["hits"]], int(t["bar"]), [int(p) for p in t["pulses"]]
    DUR, CUT, GATE = int(t["dur"]), int(t["cut"]), int(t["gate"])
    if not (FPS > 0 and HIT and 0 < HIT[0] and all(a < b for a, b in zip(HIT, HIT[1:]))):
        raise ValueError("timing: fps must be positive and hits strictly increasing after frame 0")
    if not (HIT[-1] + f30(3) < GATE < BAR < CUT <= DUR and all(BAR < p for p in PULSES)):
        raise ValueError(f"timing out of order: need last hit + {f30(3)} < gate < bar < cut <= dur and pulses after "
                         f"the bar (hits {HIT}, gate {GATE}, bar {BAR}, pulses {PULSES}, cut {CUT}, dur {DUR})")
    N = int(round(DUR / FPS * SR))


# ------------------------------------------------------------------------------------------------ DSP


def onepole_lp(x, fc):
    """Causal one-pole low-pass; fc scalar or per-sample array (Hz). x mono."""
    c = np.broadcast_to(np.asarray(fc, float), x.shape)
    a = np.exp(-2 * np.pi * c / SR)
    y = np.empty_like(x)
    p = 0.0
    for i in range(len(x)):
        p = (1 - a[i]) * x[i] + a[i] * p
        y[i] = p
    return y


def onepole_hp(x, fc):
    return x - onepole_lp(x, fc)


def biquad(x, b, a):
    """Direct form I biquad, mono or stereo (n, 2)."""
    if x.ndim == 2:
        return np.stack([biquad(x[:, c], b, a) for c in range(x.shape[1])], axis=1)
    b = np.asarray(b, float) / a[0]
    a = np.asarray(a, float) / a[0]
    y = np.empty_like(x)
    x1 = x2 = y1 = y2 = 0.0
    b0, b1, b2, a1, a2 = b[0], b[1], b[2], a[1], a[2]
    for i in range(len(x)):
        xi = x[i]
        yi = b0 * xi + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, xi, y1, yi
        y[i] = yi
    return y


def low_shelf(x, f0, db, s=1.0):
    """RBJ cookbook low shelf (causal): `db` below f0, flat above."""
    A = 10 ** (db / 40)
    w0 = 2 * np.pi * f0 / SR
    cw, sw = np.cos(w0), np.sin(w0)
    alpha = sw / 2 * np.sqrt((A + 1 / A) * (1 / s - 1) + 2)
    sa = 2 * np.sqrt(A) * alpha
    b = [A * ((A + 1) - (A - 1) * cw + sa), 2 * A * ((A - 1) - (A + 1) * cw), A * ((A + 1) - (A - 1) * cw - sa)]
    a = [(A + 1) + (A - 1) * cw + sa, -2 * ((A - 1) + (A + 1) * cw), (A + 1) + (A - 1) * cw - sa]
    return biquad(x, b, a)


def fft_filter(x, lo=None, hi=None, order=2):
    """Zero-phase Butterworth-magnitude band filter via FFT (for sustained material, not transients)."""
    n = x.shape[0]
    nfft = 1 << int(np.ceil(np.log2(n * 2)))
    X = np.fft.rfft(x, n=nfft, axis=0)
    fr = np.fft.rfftfreq(nfft, 1 / SR)
    Hm = np.ones_like(fr)
    if hi:
        Hm *= 1 / np.sqrt(1 + (fr / hi) ** (2 * order))
    if lo:
        Hm *= 1 / np.sqrt(1 + (lo / np.maximum(fr, 1e-3)) ** (2 * order))
    if x.ndim == 2:
        Hm = Hm[:, None]
    return np.fft.irfft(X * Hm, n=nfft, axis=0)[:n]


def convolve(x, ir):
    """x mono (n,) or stereo (n,2); ir stereo (m,2) -> (n+m-1, 2)."""
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    n = x.shape[0] + ir.shape[0] - 1
    nfft = 1 << int(np.ceil(np.log2(n)))
    y = np.fft.irfft(np.fft.rfft(x, nfft, axis=0) * np.fft.rfft(ir, nfft, axis=0), nfft, axis=0)
    return y[:n]


def make_ir(dur, rt60, seed, predelay=0.014, hf_damp=0.4, width=1.0):
    """Stereo diffuse tail: decorrelated noise, exponential decay, highs dying faster than lows. Unit energy."""
    r = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    tau = rt60 / 6.91
    ir = np.zeros((n, 2))
    for ch in range(2):
        noise = r.standard_normal(n)
        low = fft_filter(noise, hi=3000, order=1)
        high = noise - low
        ir[:, ch] = low * np.exp(-t / tau) + high * np.exp(-t / (tau * hf_damp))
    mid = ir.mean(axis=1, keepdims=True)
    ir = mid + (ir - mid) * width
    ir *= np.clip(t / 0.01, 0, 1)[:, None]
    pd = int(predelay * SR)
    ir = np.vstack([np.zeros((pd, 2)), ir])[:n]
    return ir / np.sqrt((ir ** 2).sum(axis=0, keepdims=True))


def att(n, sec):
    return np.clip(np.arange(n) / max(1, sec * SR), 0, 1)


def pan(x, p):
    """Constant-power pan of a mono signal, p in [-1, 1]."""
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1)


def place(buf, sig, start, gain=1.0):
    if sig.ndim == 1:
        sig = np.stack([sig, sig], axis=1) * np.sqrt(0.5)
    if start < 0:
        sig = sig[-start:]
        start = 0
    end = min(buf.shape[0], start + sig.shape[0])
    if end > start:
        buf[start:end] += sig[: end - start] * gain


# ------------------------------------------------------------------------------------------------ voices


def kick(f0, f1, tau_p, decay, dur=0.6, drive=1.8):
    t = tt(dur)
    fr = f1 + (f0 - f1) * np.exp(-t / tau_p)
    y = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t / decay) * att(len(t), 0.0015)
    return np.tanh(drive * y) / np.tanh(drive)


def click(seed, dur=0.012, decay=0.0018):
    r = np.random.default_rng(seed)
    t = tt(dur)
    return onepole_hp(r.standard_normal(len(t)), 2500) * np.exp(-t / decay)


def crack(seed, decay=0.05, lo=1800, body=900, dur=0.35):
    r = np.random.default_rng(seed)
    t = tt(dur)
    n = r.standard_normal(len(t))
    hi = onepole_hp(n, lo) * np.exp(-t / decay)
    mid = onepole_lp(onepole_hp(n, body * 0.6), body * 1.6) * np.exp(-t / (decay * 1.5)) * 0.7
    return (hi + mid) * att(len(t), 0.0008)


def body(f0, f1, decay, seed, dur=0.4, noise=0.5, drive=1.4):
    """The 150-400 Hz body that small speakers reproduce: a short tom (f0 -> f1) plus a burst of band noise."""
    t = tt(dur)
    fr = f1 + (f0 - f1) * np.exp(-t / 0.025)
    tone = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t / decay)
    nz = fft_filter(np.random.default_rng(seed).standard_normal(len(t)), lo=150, hi=400, order=4)  # stationary noise, enveloped after
    nz = nz / (np.sqrt((nz ** 2).mean()) + 1e-9) * 0.5 * np.exp(-t / (decay * 0.5))
    y = (tone + noise * nz) * att(len(t), 0.001)
    return np.tanh(drive * y) / np.tanh(drive)


def snap(seed, decay=0.022, dur=0.2, lo=2000, hi=4000):
    """A 2-4 kHz crack: band-passed noise with a hard attack (the phone-speaker 'hit')."""
    t = tt(dur)
    nz = fft_filter(np.random.default_rng(seed).standard_normal(len(t)), lo=lo, hi=hi, order=4)  # filtered, then enveloped
    y = nz * np.exp(-t / decay) * att(len(t), 0.0004)
    return y / (np.abs(y).max() + 1e-9)


def bitcrush(x, hold=8, bits=6):
    idx = (np.arange(len(x)) // hold) * hold
    y = x[idx]
    q = 2 ** (bits - 1)
    return np.round(y * q) / q


def bell(fc, ratio, index, idecay, adecay, dur, detune=0.0025):
    """Stereo FM bell (carrier fc, modulator fc*ratio), slightly detuned L/R."""
    t = tt(dur)
    out = []
    for d in (-detune, detune):
        c = fc * (1 + d)
        I = index * np.exp(-t / idecay)
        out.append(np.sin(2 * np.pi * c * t + I * np.sin(2 * np.pi * c * ratio * t)) * np.exp(-t / adecay))
    y = np.stack(out, axis=1)
    return y * att(len(t), 0.0012)[:, None]


def shimmer(seed, dur, decay, n=56, lo=2600, hi=10500):
    r = np.random.default_rng(seed)
    t = tt(dur)
    y = np.zeros((len(t), 2))
    for ch in range(2):
        for _ in range(n):
            fr = lo * (hi / lo) ** r.random()
            amp = (lo / fr) ** 0.6 * (0.5 + r.random())
            trem = 0.55 + 0.45 * np.sin(2 * np.pi * (3 + 7 * r.random()) * t + r.random() * 6.28)
            y[:, ch] += amp * np.sin(2 * np.pi * fr * t + r.random() * 6.28) * trem
    y /= n ** 0.5
    return y * (att(len(t), 0.02) * np.exp(-t / decay))[:, None]


def air(seed, dur, decay, a=0.04, lo=2200, hi=8000):
    r = np.random.default_rng(seed)
    t = tt(dur)
    y = fft_filter(r.standard_normal((len(t), 2)), lo=lo, hi=hi, order=2)
    return y * (att(len(t), a) * np.exp(-t / decay))[:, None]


def riser(seed, dur, f0=350, f1=9000):
    """Noise through a rising low-pass (and a rising tone an octave under the target), swelling to the end."""
    r = np.random.default_rng(seed)
    t = tt(dur)
    u = t / t[-1]
    cut = f0 * (f1 / f0) ** (u ** 1.4)
    out = []
    for ch in range(2):
        n = r.standard_normal(len(t))
        out.append(onepole_hp(onepole_lp(onepole_lp(n, cut), cut), 150))
    y = np.stack(out, axis=1)
    tone_f = 146.83 * 2 ** (u ** 2)  # D3 -> D4
    ph = 2 * np.pi * np.cumsum(tone_f) / SR
    tone = sum(np.sin(k * ph) / k for k in range(1, 7)) * 0.22
    tone = onepole_lp(tone, 600 + 4000 * u ** 2)
    y += tone[:, None]
    return y * (u ** 2.4)[:, None]


def reverse_swell(dry, ir, length):
    """The reverberated sound played backwards: grows from nothing and stops dead at its end."""
    wet = convolve(dry, ir)
    seg = wet[: int(length * SR)][::-1].copy()
    seg *= att(len(seg), 0.08)[:, None]
    fo = int(0.0015 * SR)
    seg[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return seg


# ------------------------------------------------------------------------------------------------ build


def ramp(n, power):
    return (np.arange(n) / max(1, n - 1)) ** power


def build():
    # Two buses: everything up to the bar (gated out for the suck-out, tails included) and the bar onwards.
    pre = np.zeros((N, 2))
    post = np.zeros((N, 2))
    wet_pre = np.zeros((N, 2))  # reverb sends (high-passed before the reverb so the low end stays tight)
    wet_post = np.zeros((N, 2))
    ir_hit = make_ir(1.4, 1.1, seed=31)
    ir_big = make_ir(2.4, 2.0, seed=47, width=1.25)

    # ---- 0: the groove stops dead on this bar line; a soft low button lands it (well under the strokes)
    place(pre, kick(120, 46, 0.02, 0.07, dur=0.35, drive=1.3), 0, LAND)
    place(pre, body(220, 160, 0.05, seed=9, dur=0.3, noise=0.35), 0, 0.45 * LAND)
    place(pre, pan(click(99, dur=0.01, decay=0.0012), 0), 0, 0.25 * LAND)
    place(wet_pre, body(220, 160, 0.05, seed=9, dur=0.3, noise=0.35), 0, 0.3 * LAND)

    # ---- 0 -> HIT[0]: the point of light breathes in. Reverse swell (reverb of a short crack + ping, played
    # backwards) and a rising shimmer, both forced to grow, cut dead on the first stroke.
    h0 = at(HIT[0])
    L0 = HIT[0] / FPS
    dry = crack(5, decay=0.03, lo=1500, dur=0.3) + bell(880.0, 3.5, 2.5, 0.04, 0.12, 0.3)[:, 0] * 0.5
    sw = reverse_swell(dry, ir_big, L0)
    sw *= ramp(len(sw), 1.6)[:, None]
    place(pre, sw / (np.abs(sw).max() + 1e-9), h0 - len(sw), 0.42)
    ch = shimmer(7, L0, 99, n=24, lo=3200, hi=9000)
    place(pre, ch * ramp(len(ch), 2.2)[:, None], h0 - len(ch), 0.2)
    t = tt(L0)
    u = t / t[-1]
    whine = np.sin(2 * np.pi * np.cumsum(440 * 2 ** (1.6 * u ** 2)) / SR) * u ** 3
    place(pre, pan(whine, 0), h0 - len(whine), 0.045)

    # ---- the strokes: impact + body + snap + tuned metal hit D4 / A4 / D5 (then on up: A5 D6 A6 ...), panned
    # with the stroke across -0.32..0.32
    notes = [293.66, 440.0, 587.33]
    while len(notes) < len(HIT):
        notes.append(notes[-2] * 2)
    pans = [-0.32 + 0.64 * i / (len(HIT) - 1) for i in range(len(HIT))] if len(HIT) > 1 else [0.0]
    for i, h in enumerate(HIT):
        s0 = at(h)
        lvl = STROKE_LVL[i % len(STROKE_LVL)]
        pg = np.array([math.cos((pans[i] + 1) * math.pi / 4), math.sin((pans[i] + 1) * math.pi / 4)]) * math.sqrt(2)
        place(pre, pan(kick(175, 54 + 3 * i, 0.024, 0.1, dur=0.45, drive=1.5), pans[i] * 0.3), s0, 0.9 * lvl)
        place(pre, pan(click(100 + i), pans[i]), s0, 0.5 * lvl)
        bd = body([300, 330, 360][i % 3], [180, 196, 214][i % 3], 0.07, seed=150 + i, dur=0.35)
        place(pre, pan(bd, pans[i] * 0.5), s0, STROKE_BODY * lvl)
        place(pre, pan(snap(170 + i, decay=0.02), pans[i]), s0, STROKE_SNAP * lvl)
        cr = crack(200 + i, decay=0.038, dur=0.3)
        place(pre, pan(cr, pans[i]), s0, 0.34 * lvl)
        metal = (bell(notes[i], 3.5, 3.0, 0.06, 0.42, 1.0) * 0.4 + bell(notes[i] * 2, 1.4, 1.6, 0.04, 0.24, 1.0) * 0.18) * pg * lvl
        place(pre, metal, s0, 1.0)
        place(wet_pre, metal, s0, 0.55)
        place(wet_pre, pan(cr, pans[i]), s0, 0.3 * lvl)
        place(wet_pre, pan(bd, pans[i] * 0.5), s0, 0.3 * lvl)
        if i > 0:
            # a short reverse suck into the stroke
            dry = bell(notes[i] * 2, 3.5, 2.0, 0.04, 0.1, 0.4)[:, 0] + crack(300 + i, decay=0.03, dur=0.4) * 0.7
            sk = reverse_swell(dry, ir_hit, 0.2)
            sk *= ramp(len(sk), 1.4)[:, None]
            place(pre, sk / (np.abs(sk).max() + 1e-9), s0 - len(sk), 0.16)

    # ---- the build to the suck-out: noise/tone riser and a reverse swell of the big hit's own crack and bells,
    # both stopping dead at GATE
    sg = at(GATE)
    rs = riser(61, (GATE - HIT[-1]) / FPS)
    place(pre, rs / (np.abs(rs).max() + 1e-9), sg - len(rs), 0.42)
    dry = crack(77, decay=0.05, lo=1200, dur=0.5) + bell(587.33, 3.5, 2.6, 0.05, 0.16, 0.5)[:, 0] * 0.6 + bell(880.0, 3.5, 2.0, 0.05, 0.14, 0.5)[:, 0] * 0.4
    rv = reverse_swell(dry, ir_big, (GATE - HIT[-1] - f30(3)) / FPS)
    rv *= ramp(len(rv), 2.0)[:, None]
    place(pre, rv / (np.abs(rv).max() + 1e-9), sg - len(rv), 0.7)

    # ---- the big hit on the bar
    sb = at(BAR)
    big_len = (DUR - BAR) / FPS + 0.1
    t = tt(2.0)
    fr = 30 + 25 * np.exp(-t / 0.32)  # sub drop ~55 -> 30 Hz
    sub = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t / 0.62) * att(len(t), 0.004)
    sub = np.tanh(2.0 * sub) / np.tanh(2.0)  # harmonics (90, 150 Hz) so phone speakers hear the boom
    low = sub * 0.9
    k = kick(230, 52, 0.026, 0.2, drive=2.0) * 0.8
    low[: len(k)] += k
    place(post, low_shelf(low, SUB_SHELF_HZ, SUB_SHELF_DB), sb)  # below 60 Hz down ~3.5 dB, the harmonics kept
    bb = body(250, 140, 0.13, seed=410, dur=0.7, noise=0.6)
    place(post, pan(bb, 0), sb, BIG_BODY)
    place(wet_post, pan(bb, 0), sb, 0.25)
    place(post, click(400, dur=0.02, decay=0.003), sb, 0.75)
    snL, snR = snap(404, decay=0.045, dur=0.35), snap(405, decay=0.045, dur=0.35)
    place(post, np.stack([snL, snR], axis=1), sb, BIG_SNAP)
    place(wet_post, np.stack([snL, snR], axis=1), sb, 0.3)
    crL = crack(401, decay=0.1, lo=1200, body=700, dur=0.6)
    crR = crack(403, decay=0.1, lo=1200, body=700, dur=0.6)
    place(post, np.stack([crL, crR], axis=1), sb, 0.36)
    crush = bitcrush(crack(402, decay=0.03, lo=900, dur=0.09), hold=7, bits=5)  # the negative frame's digital edge
    place(post, pan(crush, 0), sb, 0.2)
    chord = [(146.83, 1.0, 1.0, 0.15, 0.9, 0.3), (293.66, 1.4, 2.6, 0.22, 1.25, 0.42), (440.0, 1.4, 2.2, 0.2, 1.15, 0.34),
             (587.33, 3.5, 2.8, 0.09, 1.1, 0.3), (739.99, 3.5, 2.4, 0.09, 1.0, 0.2), (880.0, 2.0, 1.8, 0.08, 0.95, 0.2),
             (1174.66, 3.5, 1.5, 0.06, 0.75, 0.1)]
    bells = np.zeros((int(big_len * SR), 2))
    for fc, ra, ix, idc, adc, g in chord:
        bells += bell(fc, ra, ix, idc, adc, big_len, detune=0.003)[: len(bells)] * g
    shim = shimmer(71, big_len, 0.95)
    place(post, bells, sb, 0.6)
    place(post, shim, sb, 0.2)
    place(post, air(81, big_len, 0.75), sb, 0.08)
    place(wet_post, bells, sb, 0.5)
    place(wet_post, shim, sb, 0.3)
    place(wet_post, np.stack([crL, crR], axis=1), sb, 0.45)

    # ---- the glow breathes on the following beats: ping-pong echoes of a bright bell ping and a soft low pulse
    ping = np.zeros((int(0.9 * SR), 2))
    for fc, g in ((587.33, 0.5), (880.0, 0.36), (1174.66, 0.2)):
        ping += bell(fc, 3.5, 1.8, 0.05, 0.32, 0.9, detune=0.002) * g
    ping = ping.mean(axis=1)
    for k, p in enumerate(PULSES):
        g = [0.56, 0.38, 0.24][k] if k < 3 else 0.1
        e = fft_filter(ping, hi=[8000, 5500, 4000, 3000][min(k, 3)], order=1)
        e = pan(e, -0.65 if k % 2 == 0 else 0.65)
        place(post, e, at(p), g)
        place(wet_post, e, at(p), g * 0.7)
        place(post, kick(95, 46, 0.03, 0.09, dur=0.35, drive=1.2), at(p), 0.2 * (1 - 0.3 * k))

    # ---- reverb (send high-passed at 250 Hz); the post reverb starts after the bar (pre-delay), nothing leaks back
    def verb(send):
        wet = convolve(fft_filter(send, lo=250, order=2), ir_big)[:N]
        return fft_filter(wet, hi=9000, order=1) * 0.5

    pre += verb(wet_pre)
    post += verb(wet_post)
    post[:sb] = 0  # zero-phase filters above may smear a few samples before the bar: keep the suck-out clean

    # ---- suck-out: the pre bus fades in 6 ms to near-silence (-46 dB) at GATE and never comes back
    env = np.ones(N)
    f0 = int(0.006 * SR)
    env[sg: sg + f0] = 0.005 + (1 - 0.005) * (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, f0)))
    env[sg + f0: sb] = 0.005
    env[sb:] = 0
    buf = pre * env[:, None] + post

    # ---- gate the tail out with the cut to black
    g0, g1 = at(CUT - f30(2)), at(CUT + f30(1))
    env = np.ones(N)
    env[g0:g1] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, g1 - g0))
    env[g1:] = 0
    return buf * env[:, None]


def true_peak(x, os=4):
    n = x.shape[0]
    nfft = 1 << int(np.ceil(np.log2(n)))
    X = np.fft.rfft(x, nfft, axis=0)
    Y = np.zeros((nfft * os // 2 + 1, x.shape[1]), complex)
    Y[: X.shape[0]] = X
    y = np.fft.irfft(Y, nfft * os, axis=0) * os
    return float(np.max(np.abs(y)))


def limit(x, thr, look=0.0015, rel=0.06):
    """Look-ahead peak limiter (stereo-linked): the gain ramps down over `look` before a peak, recovers over `rel`."""
    L = int(look * SR)
    g = np.minimum(1.0, thr / np.maximum(np.abs(x).max(axis=1), 1e-12))
    gmin = np.lib.stride_tricks.sliding_window_view(np.concatenate([g, np.ones(L)]), L + 1).min(axis=1)
    gs = np.convolve(np.concatenate([np.ones(L), gmin]), np.ones(L + 1) / (L + 1), mode="valid")
    c = 1 - math.exp(-1 / (rel * SR))
    env = np.empty_like(gs)
    e = 1.0
    for i in range(len(gs)):
        e = min(gs[i], e + c * (gs[i] - e))
        env[i] = e
    return x * env[:, None]


def master(x):
    # DC / sub-sonic out, shave the onset spikes (the big hit's first milliseconds stack every transient) so the
    # sting is dense rather than peaky, glue with a gentle soft clip, then normalise the true peak to TP_DB
    x = np.stack([onepole_hp(x[:, c], 22) for c in range(2)], axis=1)
    x = x / np.max(np.abs(x))
    x = limit(x, 10 ** (LIMIT_DB / 20))
    x = x / np.max(np.abs(x))
    x = np.tanh(DRIVE * x) / np.tanh(DRIVE)
    target = 10 ** (TP_DB / 20)
    x *= target / true_peak(x)
    return x


def save(x, out):
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    r = np.random.default_rng(1021)
    dither = (r.random(x.shape) - r.random(x.shape)) / 32768
    pcm = np.clip(np.round((x + dither) * 32767), -32768, 32767).astype("<i2")
    with wave.open(str(out), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main():
    ap = argparse.ArgumentParser(description="Synthesise the logo sting's sound from a timing JSON (logo-sting-timing/v1).")
    ap.add_argument("--timing", required=True, help="timing JSON from sting_timing.py")
    ap.add_argument("--out", required=True, help="WAV to write (48 kHz stereo 16-bit)")
    args = ap.parse_args()
    try:
        configure(json.loads(Path(args.timing).read_text(encoding="utf-8")))
    except (ValueError, KeyError, TypeError) as e:
        raise SystemExit(f"sting_audio: error: {args.timing}: {e}")
    t0 = time.time()
    x = master(build())
    save(x, args.out)
    print(f"wrote {args.out}  {x.shape[0] / SR:.3f} s ({x.shape[0]} samples)  peak {20 * np.log10(np.max(np.abs(x))):.2f} dBFS"
          f"  in {time.time() - t0:.1f} s")
    print(f"frames (local, {FPS} fps): point 0, strokes {HIT}, gate {GATE}, wordmark/bar {BAR}, pulses {PULSES}, "
          f"cut {CUT}, dur {DUR}")


if __name__ == "__main__":
    main()
