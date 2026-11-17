// Copied verbatim from lov-logo-sting 0.2.0 (assets/remotion/LogoSting.tsx): the shared media end of every video Skill.
import React from 'react';
import {AbsoluteFill, Audio, Easing, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

// Closing brand sting (lov-logo-sting). Self-contained: imports only react and remotion, so it can be dropped into any
// Remotion 4 project. Data contract: references/spec-contract.md (logo spec, timing, sound).

// ------------------------------------------------------------------------------------------------ contract

type P = [number, number];
/** [x0, y0, x1, y1]. Typed as number[] so a JSON import of the spec (arrays infer as number[]) type-checks as is. */
type Box = readonly number[];

export type LogoShape = {d: string; box: Box; c?: readonly number[]; rule?: string};

/** logo-sting-spec/v1 (scripts/logo_spec.py). Path data is verbatim from the official SVG, in its own user units. */
export type LogoStingSpec = {
  schema?: string;
  source?: string;
  viewBox?: number[];
  mark: LogoShape[];
  word: LogoShape[];
  markBox: Box;
  wordBox: Box | null;
  logoBox: Box;
  colors: {final: string; accent: string; hot: string; background?: string};
};

/** logo-sting-timing/v1 (scripts/sting_timing.py). Integer frames local to the first frame of the sting. */
export type LogoStingTiming = {
  schema?: string;
  fps: number;
  beat?: number;
  hits: number[];
  bar: number;
  pulses: number[];
  dur: number;
  cut: number;
  gate: number;
};

export type LogoStingProps = {
  spec: LogoStingSpec;
  timing: LogoStingTiming;
  /** sting.wav: a path under public/ (staticFile) or an http(s) URL; omitted = silent picture */
  audioSrc?: string;
  /** sting gain inside the host mix */
  gain?: number;
  /** 'point': start from a centred point of light (hand-off from a scene that collapses to a point); 'black': from black */
  intro?: 'point' | 'black';
};

// ------------------------------------------------------------------------------------------------ helpers

const E = {
  outCubic: Easing.out(Easing.cubic),
  inCubic: Easing.in(Easing.cubic),
  outExpo: Easing.out(Easing.exp),
  inOutSine: Easing.inOut(Easing.sin),
  linear: (t: number) => t,
};
const clamp01 = (x: number) => Math.min(1, Math.max(0, x));
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

/** 0..1 progress of `frame` through [start, start+dur], eased and clamped. */
const prog = (frame: number, start: number, dur: number, ease: (t: number) => number) =>
  interpolate(frame, [start, start + Math.max(1, dur)], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});

/** Deterministic PRNG (mulberry32). */
const rng = (seed: number) => {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
};

const rgb = (hex: string): [number, number, number] => {
  let h = hex.trim().replace(/^#/, '');
  if (h.length === 3) h = h.replace(/./g, (c) => c + c);
  const n = parseInt(h.slice(0, 6), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
};
const rgba = (hex: string, a: number) => {
  const [r, g, b] = rgb(hex);
  return `rgba(${r},${g},${b},${a})`;
};
/** hue (deg) and saturation (0..1) of a colour, HSL */
const hueSat = (hex: string): [number, number] => {
  const [r, g, b] = rgb(hex).map((v) => v / 255);
  const mx = Math.max(r, g, b);
  const mn = Math.min(r, g, b);
  const d = mx - mn;
  if (d === 0) return [0, 0];
  const l = (mx + mn) / 2;
  const s = d / (1 - Math.abs(2 * l - 1));
  const h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return [(h * 60 + 360) % 360, s];
};

const centre = (b: Box): P => [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2];
/** 'evenodd' only when the spec says so (contract: no `rule` = nonzero). */
const fillRule = (rule?: string): 'evenodd' | 'nonzero' => (rule === 'evenodd' ? 'evenodd' : 'nonzero');

// each stroke lands from its own side: down, up, down-left (cycled for marks of more than three strokes); in units of a
// 100.4-unit-tall logo, scaled with the logo box height
const DIR_CYCLE: P[] = [
  [0, -26],
  [0, 26],
  [8, -20],
];
// shake / spark seeds of the first three strokes; further strokes get their own
const STROKE_SEEDS = [11, 23, 37];

type Impact = {f: number; at: P | null; amp: number; split: number; ring: number; sparks: number; seed: number; streak: number; big: boolean};

/** Deterministic camera shake from the impacts (`fr` = fps / 30: the shake keeps its duration at any frame rate). */
const shakeAt = (f: number, imps: Impact[], fr: number): P => {
  let x = 0;
  let y = 0;
  for (const im of imps) {
    const t = (f - im.f) / fr;
    if (t < 0 || t > 9) continue;
    const k = (1 - t / 10) ** 2;
    const r = rng(im.seed * 101 + Math.floor(t) * 7 + 3);
    x += (r() - 0.5) * 2 * im.amp * k;
    y += (r() - 0.5) * 2 * im.amp * k;
  }
  return [x, y];
};

const Layer: React.FC<{W: number; H: number; blur?: number; opacity?: number; children: React.ReactNode}> = ({W, H, blur, opacity = 1, children}) => (
  <svg
    width={W}
    height={H}
    viewBox={`0 0 ${W} ${H}`}
    style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', filter: blur ? `blur(${blur}px)` : undefined, opacity}}
  >
    {children}
  </svg>
);

// ------------------------------------------------------------------------------------------------ the sting

/**
 * The closing brand sting (4.8 s at the reference timing). A point of light inhales and implodes; the mark's strokes
 * slam in one per beat (shake, RGB split, shockwave, sparks); the build pulls light in sideways along an anamorphic
 * flare, goes dark for three frames with the sound (the suck-out); on the bar line a negative frame, the camera snaps
 * back to the full lockup and the wordmark lands with a shockwave and a light sweep; then a clean hold breathing on the
 * beat, and a hard cut to black.
 * Logo shapes are only moved or scaled uniformly as whole shapes, never edited; from bar + 9 frames on every shape sits
 * at its exact place in the lockup.
 * No radial ray pattern anywhere (a disc with radiating lines reads as the rising-sun flag to a mainland audience):
 * inbound streaks, sparks and flashes are all biased horizontal, the only round elements are thin shockwave rings.
 */
export const LogoSting: React.FC<LogoStingProps> = ({spec, timing, audioSrc, gain = 0.95, intro = 'point'}) => {
  const f = useCurrentFrame();
  const {width: W, height: H} = useVideoConfig();
  const diag = Math.hypot(W, H);

  // ------------------------------------------------------------ layout: portrait, landscape, square
  // Pixel sizes were tuned on a 1080-px short side and scale by u, so 1080×1920 and 1920×1080 match the reference.
  const short = Math.min(W, H);
  const u = short / 1080;
  const SQ = Math.abs(W - H) <= 0.05 * Math.max(W, H);
  const V = !SQ && H > W;
  const pick = <T,>(portrait: T, landscape: T, square: T): T => (SQ ? square : V ? portrait : landscape);

  // ------------------------------------------------------------ timing (frames local to the sting)
  // Hits, bar, pulses, gate and cut come from the timing file that also drives sting.wav, so picture and sound stay
  // locked. Durations inside the animation were designed at 30 fps; F() keeps them in seconds at any frame rate.
  const fr = timing.fps / 30;
  const F = (n: number) => n * fr;
  const HIT = timing.hits; // the strokes, one per beat (18 36 54 at the reference)
  const LAST = HIT[HIT.length - 1];
  const BAR = timing.bar; // wordmark + big hit on the bar line (72)
  const PULSES = timing.pulses; // breathing glow + sting echoes (90 108 126)
  const SUCK = timing.gate; // the sting gates to near-silence here; the picture inhales with it (69)
  const DUR = timing.dur;
  const CUT = timing.cut; // hard cut to black for the last frames (140)
  const BLACK = DUR - CUT;

  // ------------------------------------------------------------ brand geometry and colours (from the logo spec)
  const [lx0, ly0, lx1, ly1] = spec.logoBox;
  const LOGO_W = lx1 - lx0;
  const LOGO_H = ly1 - ly0;
  const MARK_W = spec.markBox[2] - spec.markBox[0];
  const MARK_H = spec.markBox[3] - spec.markBox[1];
  const MARK_C = centre(spec.markBox);
  const WORD_C = spec.wordBox ? centre(spec.wordBox) : MARK_C;
  const LOGO_C = centre(spec.logoBox);
  const STROKE_C: P[] = spec.mark.map((m): P => (m.c ? [m.c[0], m.c[1]] : centre(m.box)));
  const k = LOGO_H / 100.4; // logo-unit offsets below were designed on a 100.4-unit-tall lockup
  const DIRS: P[] = spec.mark.map((_, i) => [DIR_CYCLE[i % 3][0] * k, DIR_CYCLE[i % 3][1] * k]);
  const FINAL = spec.colors.final; // the logo's resting colour
  const ACC = spec.colors.accent; // glows, flares, sparks, rings
  const HOT = spec.colors.hot; // the accent lifted toward white for the hottest light
  const BG = spec.colors.background ?? '#000000';

  // ------------------------------------------------------------ camera: mark-only build, then the lockup
  // final lockup: 700 px wide in 9:16 and 840 px in 16:9 (generous margins), kept as fractions of the frame width; a
  // tall lockup (or a mark alone) is held to 30 % of the short side in height
  const sF = Math.min((pick(700 / 1080, 840 / 1920, 0.6) * W) / LOGO_W, (0.3 * short) / LOGO_H);
  // the build shows the mark alone, as wide on screen as the reference mark (700/286 × 1.9 and 840/286 × 1.6 times its
  // 91.6 units: ~0.39–0.40 of the short side), held to 55 % of the short side in height
  const sM = Math.min((pick((700 / 286) * 1.9 * 91.6, (840 / 286) * 1.6 * 91.6, 428) * u) / MARK_W, (0.55 * short) / MARK_H);
  const lock = f >= BAR;
  const charge = lock ? 0 : prog(f, LAST + F(4), SUCK - LAST - F(4), E.inCubic); // the inhale before the bar
  const suck = lock ? 0 : prog(f, SUCK - F(1), F(3), E.outCubic); // 69 .7, 70 .96, 71 1: dark, the mark alone
  const s = lock
    ? sF * (1 + 0.1 * (1 - prog(f, BAR, F(16), E.outExpo))) * (1 + 0.022 * prog(f, BAR + F(10), CUT - BAR - F(10), E.inOutSine))
    : sM * (1 + 0.05 * prog(f, HIT[0], BAR - HIT[0], E.linear)) * (1 - 0.045 * charge) * (1 - 0.03 * suck);
  const c = lock ? LOGO_C : MARK_C;

  // impacts: the strokes build in intensity (amp, RGB split, ring, sparks, streak) up to the last one, then the bar
  const N = HIT.length;
  const ramp = (a: number, b: number, i: number) => lerp(a, b, N > 1 ? i / (N - 1) : 1);
  const [ring0, ring1] = pick([380, 460], [340, 420], [360, 440]);
  const IMP: Impact[] = [
    ...HIT.map((h, i) => ({
      f: h,
      at: STROKE_C[i] ?? MARK_C,
      amp: ramp(7, 11, i) * u,
      split: ramp(9, 13, i) * u,
      ring: ramp(ring0, ring1, i) * u,
      sparks: Math.round(ramp(26, 34, i)),
      seed: STROKE_SEEDS[i] ?? 1000 + 37 * i,
      streak: ramp(0.5, 0.7, i),
      big: false,
    })),
    {f: BAR, at: null, amp: 22 * u, split: 30 * u, ring: diag * 0.62, sparks: 72, seed: 53, streak: 1, big: true},
  ];
  const [dx, dy] = shakeAt(f, IMP, fr);
  const ox = W / 2 + dx - c[0] * s;
  const oy = H / 2 + dy - c[1] * s;
  const toS = (p: P): P => [ox + p[0] * s, oy + p[1] * s];
  const camTf = `translate(${ox} ${oy}) scale(${s})`;

  // ------------------------------------------------------------ shapes in play this frame
  const barHeat = lock ? 1 - prog(f, BAR, F(22), E.outCubic) : 0;
  const shapes: {d: string; rule: 'evenodd' | 'nonzero'; tf: string; heat: number}[] = [];
  const ghosts: {d: string; rule: 'evenodd' | 'nonzero'; tf: string; o: number}[] = [];
  spec.mark.forEach((m, i) => {
    const h = HIT[i] ?? BAR;
    if (f < h) return;
    const kk = 1 - prog(f, h, F(7), E.outExpo);
    const [cx, cy] = STROKE_C[i];
    const [mx, my] = DIRS[i];
    const rule = fillRule(m.rule);
    const tfAt = (q: number) => `translate(${mx * q} ${my * q}) translate(${cx} ${cy}) scale(${1 + 0.5 * q}) translate(${-cx} ${-cy})`;
    shapes.push({d: m.d, rule, tf: tfAt(kk), heat: Math.max(1 - prog(f, h, F(18), E.outCubic), barHeat)});
    const t = (f - h) / fr;
    if (t < 3) {
      // motion trail behind the slam: the same shape further back along its path (blurred), never stretched
      const trail = (back: number) => `translate(${mx * (kk + back)} ${my * (kk + back)}) translate(${cx} ${cy}) scale(${1 + 0.5 * kk}) translate(${-cx} ${-cy})`;
      ghosts.push({d: m.d, rule, tf: trail(0.9), o: 0.3 * (1 - t / 3)});
      ghosts.push({d: m.d, rule, tf: trail(1.9), o: 0.14 * (1 - t / 3)});
    }
  });
  if (lock) {
    const kk = 1 - prog(f, BAR, F(9), E.outExpo);
    const [cx, cy] = WORD_C;
    spec.word.forEach((w) =>
      shapes.push({d: w.d, rule: fillRule(w.rule), tf: `translate(${cx} ${cy}) scale(${1 + 0.08 * kk}) translate(${-cx} ${-cy})`, heat: barHeat}),
    );
  }

  // ------------------------------------------------------------ light levels
  const lastPulse = [...PULSES].reverse().find((p) => p <= f);
  const pulse = lastPulse !== undefined && f < CUT ? 1 - prog(f, lastPulse, F(16), E.outCubic) : 0;
  const baseGlow = lock ? 0.22 + 0.24 * pulse : (0.14 + 0.6 * charge) * (1 - 0.85 * suck);
  const split = Math.max(0, ...IMP.map((im) => (f >= im.f ? im.split * (1 - prog(f, im.f, F(7), E.outCubic)) : 0)));
  const sd = split / s;
  const inverted = f >= BAR && f < BAR + Math.max(1, Math.round(fr)); // one negative frame on the bar line

  // ------------------------------------------------------------ point of light (0 .. first hit): breathe, then implode
  const grow = prog(f, 0, HIT[0] - F(6), E.outCubic);
  const implode = prog(f, HIT[0] - F(6), F(5), E.inCubic);
  const live = 1 - implode;
  const pointOn = intro !== 'black' && f < HIT[0];
  // frame 0 matches a hand-off from a scene that ends on a point (6 px white core, 58 px white glow, a short white
  // flare); from there it warms to the accent as it grows
  const coreR = 6 * u * (1 + 0.6 * grow) * (1 - 0.6 * implode);
  const haloR = ((58 + 170 * grow) * live + 10) * u;
  const streakL = (18 * u + W * 0.32 * grow) * live;

  // ------------------------------------------------------------ screen-space FX
  const under: React.ReactNode[] = []; // below the logo: inbound particles, the charge flare
  const over: React.ReactNode[] = []; // above the logo: rings, streaks, sparks, embers
  const glowOver: React.ReactNode[] = []; // blurred twins of rings and streaks
  const flashes: React.ReactNode[] = [];
  const ringsUnder: React.ReactNode[] = []; // shockwaves pass behind the shapes
  const ringsGlow: React.ReactNode[] = [];

  // inbound light: into the point before the first stroke, into the mark before the suck-out. Every streak is
  // horizontal, rushing in from the left or right along its own lane of a narrow band (denser near the axis), so the
  // pull reads as an anamorphic flare and never as lines radiating from a disc.
  const inbound = (seed: number, n: number, from: number, to: number, ctr: P, r0: number, r1: number, band: number) => {
    const r = rng(seed);
    for (let i = 0; i < n; i++) {
      const side = r() < 0.5 ? -1 : 1;
      const R = r0 + r() * (r1 - r0);
      const st = from + r() * (to - from) * 0.45;
      const w = 1.2 + r() * 2.2;
      const lane = (r() - 0.5) * (0.3 + 0.7 * r()) * band;
      const p = prog(f, st, to - st, E.inCubic);
      if (f < st || p >= 1) continue;
      const d = R * (1 - p);
      const tail = Math.min(R * 0.3, (40 + 260 * p) * u);
      const y = ctr[1] + lane;
      under.push(
        <line
          key={`in${seed}-${i}`}
          x1={ctr[0] + side * d}
          y1={y}
          x2={ctr[0] + side * (d + tail)}
          y2={y}
          stroke={i % 3 === 0 ? ACC : HOT}
          strokeWidth={w * u}
          strokeLinecap="round"
          opacity={(0.25 + 0.65 * p) * clamp01(d / (70 * u))}
        />,
      );
    }
  };
  if (pointOn) inbound(401, 22, F(4), HIT[0] - F(1), [W / 2, H / 2], 200 * u, pick(520, 700, 520) * u, 46 * u);
  const charging = !lock && f >= LAST + F(3);
  const mc = toS(MARK_C);
  if (charging) inbound(733, 40, LAST + F(3), SUCK, mc, 360 * u, pick(620, 940, 620) * u, pick(300, 240, 260) * u);
  // the charge flare: a horizontal anamorphic line through the mark that stretches with the charge and snaps shut
  // into the mark on the suck-out
  const flareHalf = W * (0.16 + 0.3 * charge) * (1 - 0.88 * suck);
  const chargeFlare = charging && (
    <>
      <div
        style={{
          position: 'absolute',
          left: mc[0] - flareHalf,
          top: mc[1] - 9 * u,
          width: flareHalf * 2,
          height: 18 * u,
          filter: `blur(${7 * u}px)`,
          background: `linear-gradient(90deg, ${rgba(ACC, 0)} 0%, ${rgba(ACC, 0.7)} 38%, ${rgba(HOT, 0.95)} 50%, ${rgba(ACC, 0.7)} 62%, ${rgba(ACC, 0)} 100%)`,
          opacity: (0.2 + 0.8 * charge) * (1 - 0.9 * suck),
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: mc[0] - flareHalf,
          top: mc[1] - 1.5 * u,
          width: flareHalf * 2,
          height: 3 * u,
          background: 'linear-gradient(90deg, rgba(255,255,255,0), rgba(255,255,255,0.9) 40%, #FFFFFF 50%, rgba(255,255,255,0.9) 60%, rgba(255,255,255,0))',
          opacity: 0.35 + 0.65 * charge,
        }}
      />
    </>
  );

  for (const im of IMP) {
    const t = (f - im.f) / fr; // in 30-fps frames
    if (t < 0 || t > 34) continue;
    const o: P = im.at ? toS(im.at) : toS(LOGO_C);
    const rd = im.big ? 24 : 16;
    // shockwave ring
    const q = prog(t, 0, rd, E.outCubic);
    if (q < 1) {
      const rr = lerp((im.big ? 140 : 70) * u, im.ring, q);
      const sw = lerp((im.big ? 18 : 10) * u, 1.2 * u, q);
      const op = (1 - q) ** 1.3;
      ringsUnder.push(<circle key={`ring${im.f}`} cx={o[0]} cy={o[1]} r={rr} fill="none" stroke="#FFFFFF" strokeWidth={sw} opacity={op * 0.95} />);
      ringsGlow.push(<circle key={`ringg${im.f}`} cx={o[0]} cy={o[1]} r={rr} fill="none" stroke={ACC} strokeWidth={sw * 3.2} opacity={op} />);
      if (im.big) {
        const q2 = prog(t, 3, 26, E.outCubic);
        if (t >= 3 && q2 < 1) {
          const r2 = lerp(40 * u, diag * 0.45, q2);
          ringsUnder.push(<circle key="ring2" cx={o[0]} cy={o[1]} r={r2} fill="none" stroke={HOT} strokeWidth={lerp(8 * u, 1 * u, q2)} opacity={(1 - q2) ** 1.5 * 0.8} />);
          ringsGlow.push(<circle key="ring2g" cx={o[0]} cy={o[1]} r={r2} fill="none" stroke={ACC} strokeWidth={lerp(26 * u, 4 * u, q2)} opacity={(1 - q2) ** 1.5} />);
        }
      }
    }
    // anamorphic streak through the impact
    const qs = prog(t, 0, im.big ? 18 : 11, E.outCubic);
    if (qs < 1) {
      const half = W * im.streak * (0.45 + 0.55 * prog(t, 0, 8, E.outCubic));
      const gid = `lgStreak${im.f}`;
      const defs = (
        <defs key={`d${gid}`}>
          <linearGradient id={gid} gradientUnits="userSpaceOnUse" x1={o[0] - half} y1={0} x2={o[0] + half} y2={0}>
            <stop offset="0" stopColor={ACC} stopOpacity={0} />
            <stop offset="0.38" stopColor={ACC} stopOpacity={0.7} />
            <stop offset="0.5" stopColor="#FFFFFF" stopOpacity={1} />
            <stop offset="0.62" stopColor={ACC} stopOpacity={0.7} />
            <stop offset="1" stopColor={ACC} stopOpacity={0} />
          </linearGradient>
        </defs>
      );
      const h0 = (im.big ? 4 : 2.5) * u;
      over.push(defs, <rect key={`st${im.f}`} x={o[0] - half} y={o[1] - h0 / 2} width={half * 2} height={h0} fill={`url(#${gid})`} opacity={1 - qs} />);
      glowOver.push(
        <defs key={`dg${gid}`}>
          <linearGradient id={`${gid}g`} gradientUnits="userSpaceOnUse" x1={o[0] - half} y1={0} x2={o[0] + half} y2={0}>
            <stop offset="0" stopColor={ACC} stopOpacity={0} />
            <stop offset="0.5" stopColor={ACC} stopOpacity={1} />
            <stop offset="1" stopColor={ACC} stopOpacity={0} />
          </linearGradient>
        </defs>,
        <rect key={`stg${im.f}`} x={o[0] - half} y={o[1] - h0 * 4} width={half * 2} height={h0 * 8} fill={`url(#${gid}g)`} opacity={(1 - qs) * 0.9} />,
      );
    }
    // sparks: decelerating streaks, a little gravity, sprayed sideways (within ±26° of horizontal) so the burst
    // never reads as rays around the flash; the bar's sparks rise from the whole lockup (a band through its middle)
    const r = rng(im.seed * 7919);
    for (let i = 0; i < im.sparks; i++) {
      const ang = (r() < 0.5 ? 0 : Math.PI) + (r() - 0.5) * 0.9;
      const v = ((im.big ? 16 : 11) + r() * (im.big ? 50 : 30)) * u;
      const life = (im.big ? 14 : 9) + r() * (im.big ? 18 : 11);
      const jx = r();
      const jy = r();
      const w = (1.4 + r() * 2.4) * u;
      const hot = r();
      if (t > life) continue;
      const src: P = im.big ? toS([lx0 + jx * LOGO_W, ly0 + 18.6 * k + jy * 64 * k]) : [o[0] + (jx - 0.5) * 60 * u, o[1] + (jy - 0.5) * 160 * u];
      const tau = 7;
      const d1 = v * tau * (1 - Math.exp(-t / tau));
      const d0 = v * tau * (1 - Math.exp(-Math.max(0, t - 1.5) / tau));
      const g = 0.22 * u * t * t * 0.5;
      const ux = Math.cos(ang);
      const uy = Math.sin(ang);
      const life01 = t / life;
      over.push(
        <line
          key={`sp${im.f}-${i}`}
          x1={src[0] + ux * d0}
          y1={src[1] + uy * d0 + 0.22 * u * Math.max(0, t - 1.5) ** 2 * 0.5}
          x2={src[0] + ux * d1}
          y2={src[1] + uy * d1 + g}
          stroke={life01 < 0.3 || hot > 0.75 ? '#FFFFFF' : life01 < 0.65 ? HOT : ACC}
          strokeWidth={w * (1 - life01 * 0.6)}
          strokeLinecap="round"
          opacity={1 - life01}
        />,
      );
    }
    // flash of light behind the impact: a wide anamorphic ellipse, not a disc
    const fq = prog(t, 0, im.big ? 14 : 9, E.outCubic);
    if (fq < 1) {
      const R = pick(560, 520, 540) * u * (im.big ? 2.2 : 1);
      const Ry = R * 0.42;
      flashes.push(
        <div
          key={`fl${im.f}`}
          style={{
            position: 'absolute',
            left: o[0] - R,
            top: o[1] - Ry,
            width: R * 2,
            height: Ry * 2,
            background: `radial-gradient(closest-side, ${rgba(HOT, 0.55)} 0%, ${rgba(ACC, 0.22)} 46%, ${rgba(ACC, 0)} 100%)`,
            opacity: (1 - fq) * (im.big ? 1 : 0.75),
          }}
        />,
      );
    }
  }

  // embers kicked out by the big hit, then drifting up through the hold
  if (lock) {
    const t = (f - BAR) / fr;
    const lc = toS(LOGO_C);
    const vis = prog(f, BAR + F(1), F(10), E.outCubic);
    for (let i = 0; i < 44; i++) {
      const r = rng(9001 + i * 13);
      const x0 = lc[0] + (r() - 0.5) * W * pick(0.86, 0.7, 0.86);
      const y0 = lc[1] + (r() - 0.5) * pick(980, 760, 760) * u;
      const vy = (0.35 + r() * 1.25) * u;
      const size = (1.3 + r() * 2.6) * u;
      const ph = r() * Math.PI * 2;
      const col = r() < 0.6 ? ACC : HOT;
      const kick = 70 * u * (1 - Math.exp(-t / 8));
      const dxk = x0 - lc[0];
      const dyk = y0 - lc[1];
      const dl = Math.hypot(dxk, dyk) || 1;
      const x = x0 + (dxk / dl) * kick + Math.sin(t * 0.05 + ph) * 10 * u;
      const y = y0 + (dyk / dl) * kick - vy * t;
      const tw = 0.3 + 0.7 * Math.sin(t * 0.09 + ph) ** 2;
      over.push(<circle key={`em${i}`} cx={x} cy={y} r={size} fill={col} opacity={vis * tw * (0.5 + 0.5 * pulse) * 0.85} />);
    }
  }

  // ------------------------------------------------------------ logo drawing helpers (logo units, inside camTf)
  const paths = (fill: string, opacity: (h: number) => number, key: string, extra = '') =>
    shapes.map((sh, i) => (
      <path key={`${key}${i}`} d={sh.d} fillRule={sh.rule} fill={fill} fillOpacity={clamp01(opacity(sh.heat))} transform={`${extra} ${sh.tf}`} />
    ));

  // light sweep across the lockup right after the bar: a white band clipped to the shapes (the shapes dip to 86 %
  // while it passes so the band reads brighter than them) and a blurred hot twin that blooms past their edges.
  // The band leans 18° about the lockup's centre line; on that line its centre runs from 38.71 units left of the
  // lockup to 65.29 units past its right edge (per 100.4 units of lockup height, like its width and height).
  const sweepA = BAR + F(3);
  const sweepD = F(22);
  const sweepOn = lock && f >= sweepA && f <= sweepA + sweepD;
  const sweepP = prog(f, sweepA, sweepD, E.inOutSine);
  const sx = lerp(lx0 - 38.7134 * k, lx1 + 65.2866 * k, sweepP);
  const dip = lock ? 1 - 0.14 * Math.min(prog(f, sweepA - F(2), F(4), E.outCubic), 1 - prog(f, sweepA + sweepD - F(4), F(5), E.inOutSine)) : 1;
  const sweep = (id: string, hot: boolean) => (
    <>
      <defs>
        <clipPath id={`${id}c`}>
          {shapes.map((sh, i) => (
            <path key={i} d={sh.d} clipRule={sh.rule} transform={sh.tf} />
          ))}
        </clipPath>
        <linearGradient id={`${id}g`} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor={hot ? ACC : '#FFFFFF'} stopOpacity={0} />
          <stop offset="0.35" stopColor={hot ? ACC : '#FFFFFF'} stopOpacity={hot ? 0.8 : 0.5} />
          <stop offset="0.5" stopColor={hot ? HOT : '#FFFFFF'} stopOpacity={1} />
          <stop offset="0.65" stopColor={hot ? ACC : '#FFFFFF'} stopOpacity={hot ? 0.8 : 0.5} />
          <stop offset="1" stopColor={hot ? ACC : '#FFFFFF'} stopOpacity={0} />
        </linearGradient>
      </defs>
      <g transform={camTf}>
        <g clipPath={`url(#${id}c)`}>
          <rect
            x={sx - 34 * k}
            y={LOGO_C[1] - 71.6 * k}
            width={68 * k}
            height={140 * k}
            fill={`url(#${id}g)`}
            transform={`translate(0 ${LOGO_C[1]}) skewX(-18) translate(0 ${-LOGO_C[1]})`}
          />
        </g>
      </g>
    </>
  );

  const bgGlow = lock ? 0.1 + 0.08 * pulse + 0.3 * barHeat : 0.05 * charge * (1 - suck);

  // ------------------------------------------------------------ the negative frame on the bar line
  // warm light ground capped at ~85 % luma (the brightest frame, on a phone at night), dark shapes, the RGB fringes
  // kept: a designed negative rather than a CSS invert. The ground takes the hot colour's hue at 40 % saturation,
  // drifting a few degrees warmer in the centre and redder at the edge (with the reference film's hot colour this
  // reproduces its hand-picked ground to within rounding).
  const [negH, negS] = hueSat(HOT);
  const neg = (dh: number, l: number) => `hsl(${(negH + dh).toFixed(2)}, ${(Math.min(0.4, negS) * 100).toFixed(2)}%, ${l}%)`;
  const negative = (
    <AbsoluteFill style={{background: `radial-gradient(ellipse 80% 70% at 50% 50%, ${neg(4, 85.1)} 0%, ${neg(2.9, 79.6)} 45%, ${neg(-2.7, 64.5)} 100%)`}}>
      <Layer W={W} H={H}>
        <g transform={camTf}>
          {paths(ACC, () => 0.95, 'nr', `translate(${-sd} ${sd * 0.2})`)}
          {paths('#19A9C9', () => 0.85, 'nb', `translate(${sd} ${-sd * 0.2})`)}
          {paths('#0B0B0C', () => 1, 'nw')}
        </g>
      </Layer>
    </AbsoluteFill>
  );

  const audio = audioSrc ? (/^(https?:|data:|blob:)/.test(audioSrc) ? audioSrc : staticFile(audioSrc.replace(/^\.?\//, ''))) : null;

  return (
    <AbsoluteFill style={{background: BG}}>
      {inverted && negative}
      {!inverted && f < CUT && (
        <AbsoluteFill style={{background: BG}}>
          <AbsoluteFill style={{background: `radial-gradient(ellipse 62% 40% at 50% 50%, ${rgba(ACC, bgGlow)} 0%, ${rgba(ACC, 0)} 72%)`}} />
          {flashes}
          {chargeFlare}
          <Layer W={W} H={H}>{under}</Layer>
          <Layer W={W} H={H} blur={10 * u}>
            {ringsGlow}
          </Layer>
          <Layer W={W} H={H}>{ringsUnder}</Layer>

          {/* logo glow: wide accent, tight hot */}
          <Layer W={W} H={H} blur={pick(34, 30, 32) * u}>
            <g transform={camTf}>{paths(ACC, (h) => baseGlow + 0.85 * h, 'gw')}</g>
          </Layer>
          <Layer W={W} H={H} blur={9 * u}>
            <g transform={camTf}>{paths(HOT, (h) => (0.9 * h + 0.35 * charge) * (1 - 0.8 * suck), 'gt')}</g>
          </Layer>
          {ghosts.length > 0 && (
            <Layer W={W} H={H} blur={7 * u}>
              <g transform={camTf}>
                {ghosts.map((g, i) => (
                  <path key={`gh${i}`} d={g.d} fillRule={g.rule} fill={HOT} fillOpacity={g.o} transform={g.tf} />
                ))}
              </g>
            </Layer>
          )}

          {/* the logo: RGB split fringes, then the shapes in their resting colour */}
          <Layer W={W} H={H}>
            <g transform={camTf}>
              {sd > 0.02 && paths('#FF2E4A', () => 0.9, 'r', `translate(${-sd} ${sd * 0.2})`)}
              {sd > 0.02 && paths('#19E3FF', () => 0.9, 'b', `translate(${sd} ${-sd * 0.2})`)}
              {paths(FINAL, () => dip, 'w')}
            </g>
          </Layer>

          {sweepOn && (
            <>
              <Layer W={W} H={H} blur={16 * u}>
                {sweep('lgSwB', true)}
              </Layer>
              <Layer W={W} H={H}>{sweep('lgSw', false)}</Layer>
            </>
          )}

          <Layer W={W} H={H} blur={10 * u}>
            {glowOver}
          </Layer>
          <Layer W={W} H={H}>{over}</Layer>

          {/* the point of light handed over at the exact centre */}
          {pointOn && (
            <>
              <div
                style={{
                  position: 'absolute',
                  left: W / 2 - haloR,
                  top: H / 2 - haloR,
                  width: haloR * 2,
                  height: haloR * 2,
                  borderRadius: '50%',
                  background: 'radial-gradient(circle, rgba(255,255,255,0.5) 0%, rgba(255,255,255,0.16) 28%, rgba(255,255,255,0) 70%)',
                  opacity: 1 - 0.5 * grow,
                }}
              />
              <div
                style={{
                  position: 'absolute',
                  left: W / 2 - haloR,
                  top: H / 2 - haloR,
                  width: haloR * 2,
                  height: haloR * 2,
                  borderRadius: '50%',
                  background: `radial-gradient(circle, ${rgba(HOT, 0.6)} 0%, ${rgba(ACC, 0.24)} 30%, ${rgba(ACC, 0)} 70%)`,
                  opacity: grow,
                }}
              />
              <div
                style={{
                  position: 'absolute',
                  left: W / 2 - streakL,
                  top: H / 2 - 6 * u,
                  width: streakL * 2,
                  height: 12 * u,
                  filter: `blur(${5 * u}px)`,
                  background: `linear-gradient(90deg, ${rgba(ACC, 0)} 0%, ${rgba(ACC, 0.75)} 35%, #FFFFFF 50%, ${rgba(ACC, 0.75)} 65%, ${rgba(ACC, 0)} 100%)`,
                  opacity: 0.85 * grow * live,
                }}
              />
              <div
                style={{
                  position: 'absolute',
                  left: W / 2 - streakL,
                  top: H / 2 - 1 * u,
                  width: streakL * 2,
                  height: 2 * u,
                  background: 'linear-gradient(90deg, rgba(255,255,255,0), rgba(255,255,255,0.75), rgba(255,255,255,0))',
                  opacity: live,
                }}
              />
              <div
                style={{
                  position: 'absolute',
                  left: W / 2 - coreR,
                  top: H / 2 - coreR,
                  width: coreR * 2,
                  height: coreR * 2,
                  borderRadius: '50%',
                  background: '#FFFFFF',
                  boxShadow: `0 0 ${(10 + 14 * grow) * u}px ${(3 + 5 * grow) * u}px rgba(255,255,255,0.9), 0 0 ${coreR * 6}px ${coreR * 2}px ${rgba(ACC, 0.55 * grow)}`,
                }}
              />
            </>
          )}

          {/* vignette */}
          <AbsoluteFill style={{background: `radial-gradient(ellipse 85% 70% at 50% 50%, ${rgba(BG, 0)} 55%, ${rgba(BG, 0.55)} 100%)`}} />
        </AbsoluteFill>
      )}
      {audio && (
        <Sequence from={0} durationInFrames={Math.max(1, Math.round(DUR))} layout="none">
          <Audio src={audio} volume={(af) => gain * Math.min(prog(af, 0, F(1), E.linear), 1 - prog(af, DUR - BLACK, BLACK, E.linear))} />
        </Sequence>
      )}
    </AbsoluteFill>
  );
};
