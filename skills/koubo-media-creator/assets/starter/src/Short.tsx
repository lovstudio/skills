import React from 'react';
import {
  AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig,
} from 'remotion';
import { BADGE_Y, BROLL_FULL, C, CALLOUT_Y, CAPTION_Y, FONT, H, SAFE, SPLIT, W, outlined } from './layout';
import { useFonts } from './fonts';
import type { Caption, Layout, Shot, Timeline } from './types';

const clamp = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;

const shotAt = (tl: Timeline, frame: number): Shot | undefined => {
  let last: Shot | undefined;
  for (const s of tl.shots) {
    if (frame >= s.from && frame < s.to) return s;
    if (s.from <= frame) last = s;
  }
  return last;
};

// ---------- the author: one continuous mezzanine, framed per layout ----------
const Presenter: React.FC<{ tl: Timeline; layout: Layout; lineIndex: number }> = ({ tl, layout, lineIndex }) => {
  const frame = useCurrentFrame();
  const p = tl.presenter;
  if (frame >= tl.speechFrames || layout === 'broll') {
    // keep the decoder warm but invisible while evidence is full screen
    return p.kind === 'video' ? (
      <AbsoluteFill style={{ opacity: 0 }}><OffthreadVideo src={staticFile(p.src)} muted style={{ width: W, height: H }} /></AbsoluteFill>
    ) : null;
  }
  const top = layout === 'split' ? SPLIT.presenterTop : 0;
  const boxH = H - top;
  // split: put the face at 42% of the lower box; face: alternate 1.0 / 1.08 punch-in per line (hides jump cuts)
  const offset = layout === 'split' ? Math.min(0, Math.max(boxH - H, boxH * 0.42 - p.faceY * H)) : 0;
  const punch = layout === 'face' && lineIndex % 2 === 1 ? 1.08 : 1.0;
  const drift = p.kind === 'image' ? 1 + 0.04 * ((frame % 300) / 300) : 1;
  if (p.placeholder) {
    return (
      <div style={{ position: 'absolute', left: 0, top, width: W, height: boxH, overflow: 'hidden',
        background: `radial-gradient(circle at 50% 45%, #2A1408 0%, ${C.ink} 70%)`, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: layout === 'split' ? 'flex-start' : 'center', paddingTop: layout === 'split' ? 210 : 0, gap: 22 }}>
        <Img src={staticFile(p.src)} style={{ width: 360, height: 360, borderRadius: '50%', objectFit: 'cover',
          border: `8px solid ${C.amber}`, transform: `scale(${punch})` }} />
        <div style={{ fontFamily: FONT.sans, fontWeight: 800, fontSize: 30, color: 'rgba(255,255,255,0.55)' }}>出镜位 · 录制后替换为口播画面</div>
      </div>
    );
  }
  const media = p.kind === 'video'
    ? <OffthreadVideo src={staticFile(p.src)} muted style={{ width: W, height: H }} />
    : <Img src={staticFile(p.src)} style={{ width: W, height: H, objectFit: 'cover', objectPosition: `50% ${p.faceY * 100}%` }} />;
  return (
    <div style={{ position: 'absolute', left: 0, top, width: W, height: boxH, overflow: 'hidden', background: '#000' }}>
      <div style={{ position: 'absolute', left: 0, top: offset, width: W, height: H,
        transform: `scale(${punch * drift})`, transformOrigin: `50% ${p.faceY * 100}%` }}>
        {media}
      </div>
    </div>
  );
};

// ---------- on-screen evidence: fitted image/video with focus push, red boxes and a label ----------
const Broll: React.FC<{ s: Shot; fps: number }> = ({ s, fps }) => {
  const frame = useCurrentFrame();
  const t = frame - s.from;
  const len = Math.max(1, s.to - s.from);
  const panel = s.layout === 'split'
    ? { top: SPLIT.brollTop, h: SPLIT.brollBottom - SPLIT.brollTop }
    : { top: BROLL_FULL.top, h: BROLL_FULL.bottom - BROLL_FULL.top };
  const iw = s.w ?? W, ih = s.h ?? panel.h;
  const fit = s.fit ?? 'cover';
  const k = fit === 'cover' ? Math.max(W / iw, panel.h / ih) : Math.min(W / iw, panel.h / ih);
  const dw = iw * k, dh = ih * k;
  const x = (W - dw) / 2;
  // tall screenshots: show the top unless a focus says otherwise
  let y = fit === 'cover' && dh > panel.h ? 0 : (panel.h - dh) / 2;
  let zoom = 1 + 0.06 * (t / len);
  let ox = 0.5, oy = 0.5;
  if (s.focus) {
    const [fx, fy, fw, fh] = s.focus;
    const target = Math.min(2.2, 0.85 * Math.min(W / (fw * dw), panel.h / (fh * dh)));
    const p = interpolate(t, [0, len * 0.6], [0, 1], { ...clamp, easing: (v) => 1 - (1 - v) ** 3 });
    zoom = 1 + (Math.max(1, target) - 1) * p;
    ox = fx + fw / 2;
    oy = fy + fh / 2;
    if (fit === 'cover' && dh > panel.h) y = Math.min(0, Math.max(panel.h - dh, panel.h / 2 - oy * dh));
  }
  const pop = interpolate(t, [0, 4], [0.96, 1], clamp);
  const boxPop = (i: number) => {
    const f = t - 6 - i * 4;
    return { o: interpolate(f, [0, 3], [0, 1], clamp), sc: interpolate(f, [0, 5], [1.18, 1], clamp) };
  };
  const labelTop = s.layout === 'split' ? SAFE.top + 10 : panel.top + 24;
  return (
    <div style={{ position: 'absolute', left: 0, top: panel.top, width: W, height: panel.h, overflow: 'hidden', background: '#000' }}>
      <div style={{ position: 'absolute', left: x, top: y, width: dw, height: dh,
        transform: `scale(${zoom * pop})`, transformOrigin: `${ox * 100}% ${oy * 100}%` }}>
        {s.kind === 'video'
          ? <Sequence from={s.from} layout="none"><OffthreadVideo src={staticFile(s.src!)} muted startFrom={Math.round((s.start ?? 0) * fps)} style={{ width: dw, height: dh }} /></Sequence>
          : <Img src={staticFile(s.src!)} style={{ width: dw, height: dh }} />}
        {(s.boxes ?? []).map((b, i) => {
          const { o, sc } = boxPop(i);
          return (
            <div key={i} style={{ position: 'absolute', left: b[0] * dw, top: b[1] * dh, width: b[2] * dw, height: b[3] * dh,
              border: `${Math.max(5, 7 / zoom)}px solid ${C.red}`, borderRadius: 10, opacity: o, transform: `scale(${sc})`,
              boxShadow: '0 0 14px rgba(255,45,45,0.55)' }} />
          );
        })}
      </div>
      {s.layout === 'split' ? (
        <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, height: 60,
          background: 'linear-gradient(to bottom, rgba(0,0,0,0), rgba(0,0,0,0.55))' }} />
      ) : null}
      {s.label ? (
        <div style={{ position: 'absolute', left: SAFE.side, top: labelTop - panel.top, fontFamily: FONT.sans, fontWeight: 900,
          fontSize: 76, color: C.amber, ...outlined(12), textShadow: '0 6px 0 rgba(0,0,0,0.6)', transform: 'skewX(-6deg)',
          opacity: interpolate(t, [0, 3], [0, 1], clamp) }}>{s.label}</div>
      ) : null}
    </div>
  );
};

// ---------- big orange call-out (《功能名》 / 第 N 招 / 怎么分工？) ----------
const Callout: React.FC<{ s: Shot }> = ({ s }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (!s.callout) return null;
  const sp = spring({ frame: frame - s.from, fps, config: { damping: 12, stiffness: 220 } });
  const top = CALLOUT_Y[s.layout];
  const size = Math.min(104, Math.floor((W - 2 * SAFE.side) / Math.max(4, [...s.callout].length * 0.92)));
  return (
    <div style={{ position: 'absolute', left: SAFE.side, right: SAFE.side, top, textAlign: 'center', fontFamily: FONT.sans,
      fontWeight: 900, fontSize: size, lineHeight: 1.1, color: C.yellow, ...outlined(16),
      textShadow: `0 10px 0 #000, 0 0 36px rgba(255,122,0,0.65)`,
      transform: `scale(${0.6 + 0.4 * sp}) rotate(-3deg)`, opacity: Math.min(1, sp * 1.4) }}>
      {s.callout}
    </div>
  );
};

// ---------- captions: white heavy outline, emphasis in yellow ----------
const CaptionView: React.FC<{ c: Caption; layout: Layout }> = ({ c, layout }) => {
  const frame = useCurrentFrame();
  const t = frame - c.from;
  const sc = interpolate(t, [0, 3], [0.92, 1], clamp);
  const parts: { s: string; hl: boolean }[] = [];
  let rest = c.text;
  const words = [...c.hl].sort((a, b) => b.length - a.length);
  while (rest.length) {
    let best = -1, word = '';
    for (const w of words) {
      const i = rest.indexOf(w);
      if (i >= 0 && (best < 0 || i < best)) { best = i; word = w; }
    }
    if (best < 0) { parts.push({ s: rest, hl: false }); break; }
    if (best > 0) parts.push({ s: rest.slice(0, best), hl: false });
    parts.push({ s: word, hl: true });
    rest = rest.slice(best + word.length);
  }
  const y = CAPTION_Y[layout];
  return (
    <div style={{ position: 'absolute', left: SAFE.side, right: SAFE.side, top: y - 50, textAlign: 'center', fontFamily: FONT.sans,
      fontWeight: 900, fontSize: 68, lineHeight: 1.25, color: C.white, ...outlined(12),
      textShadow: '0 5px 0 rgba(0,0,0,0.55)', transform: `scale(${sc})` }}>
      {parts.map((p, i) => (
        <span key={i} style={p.hl ? { color: C.hl, fontSize: 78 } : undefined}>{p.s}</span>
      ))}
    </div>
  );
};

// ---------- end card: the author's own follow card ----------
const EndCard: React.FC<{ tl: Timeline }> = ({ tl }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const e = tl.end;
  const t = frame - e.from;
  if (t < 0) return null;
  const sp = spring({ frame: t, fps, config: { damping: 14, stiffness: 160 } });
  return (
    <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 42%, ${C.orange} 0%, #8A3000 24%, ${C.ember} 48%, ${C.ink} 78%)` }}>
      {e.covers.length ? (
        <AbsoluteFill style={{ display: 'flex', flexWrap: 'wrap', gap: 18, padding: '200px 40px', opacity: 0.22,
          alignContent: 'flex-start', justifyContent: 'center' }}>
          {e.covers.slice(0, 12).map((c, i) => (
            <Img key={i} src={staticFile(c)} style={{ width: 300, height: 400, objectFit: 'cover', borderRadius: 14 }} />
          ))}
        </AbsoluteFill>
      ) : null}
      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center', flexDirection: 'column', gap: 34,
        transform: `scale(${0.85 + 0.15 * sp})`, opacity: Math.min(1, sp * 1.5), paddingBottom: 120 }}>
        {e.avatar ? (
          <Img src={staticFile(e.avatar)} style={{ width: 300, height: 300, borderRadius: '50%', objectFit: 'cover',
            border: `10px solid ${C.amber}`, boxShadow: '0 0 60px rgba(255,140,0,0.7)' }} />
        ) : null}
        {tl.logo ? <Img src={staticFile(tl.logo)} style={{ height: 120, objectFit: 'contain' }} /> : (
          <div style={{ fontFamily: FONT.sans, fontWeight: 900, fontSize: 84, color: C.white, ...outlined(10) }}>{e.name}</div>
        )}
        {e.line ? (
          <div style={{ fontFamily: FONT.sans, fontWeight: 800, fontSize: 48, color: C.yellow, ...outlined(8), textAlign: 'center',
            padding: '0 80px' }}>{e.line}</div>
        ) : null}
        <div style={{ marginTop: 10, padding: '18px 76px', borderRadius: 999, background: C.orange, fontFamily: FONT.sans,
          fontWeight: 900, fontSize: 52, color: C.white, boxShadow: '0 8px 0 #7A2A00',
          transform: `scale(${1 + 0.05 * Math.sin(t / 5)})` }}>＋ 关注</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const Short: React.FC<{ tl: Timeline }> = ({ tl }) => {
  useFonts();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const shot = shotAt(tl, frame);
  const layout: Layout = shot?.layout ?? 'face';
  const lineIds = [...new Set(tl.shots.map((s) => s.line))];
  const lineIndex = shot ? lineIds.indexOf(shot.line) : 0;
  const cap = tl.captions.find((c) => frame >= c.from && frame < c.to);
  const inSpeech = frame < tl.speechFrames;
  return (
    <AbsoluteFill style={{ backgroundColor: '#000' }}>
      <Presenter tl={tl} layout={layout} lineIndex={lineIndex} />
      {inSpeech && shot?.src ? <Broll s={shot} fps={fps} /> : null}
      {inSpeech && shot?.missing ? (
        <div style={{ position: 'absolute', left: 0, top: 0, width: W, height: shot.layout === 'split' ? SPLIT.brollBottom : H,
          background: '#141414', display: 'flex', alignItems: 'center', justifyContent: 'center', color: C.amber,
          fontFamily: FONT.sans, fontWeight: 800, fontSize: 40 }}>素材待补：{shot.missing}</div>
      ) : null}
      {inSpeech && shot ? <Callout s={shot} /> : null}
      {inSpeech && cap ? <CaptionView c={cap} layout={layout} /> : null}
      {inSpeech && tl.logo ? (
        <Img src={staticFile(tl.logo)} style={{ position: 'absolute', right: SAFE.side, top: SAFE.top + 14, height: 46,
          opacity: 0.82, filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.6))' }} />
      ) : inSpeech && tl.watermark ? (
        <div style={{ position: 'absolute', right: SAFE.side, top: SAFE.top + 12, fontFamily: FONT.sans, fontWeight: 800,
          fontSize: 30, color: 'rgba(255,255,255,0.72)', ...outlined(4, 'rgba(0,0,0,0.5)') }}>{tl.watermark}</div>
      ) : null}
      {tl.animatic && inSpeech ? (
        <div style={{ position: 'absolute', left: SAFE.side, top: BADGE_Y, padding: '6px 16px', borderRadius: 10,
          background: 'rgba(0,0,0,0.6)', color: C.yellow, fontFamily: FONT.sans, fontWeight: 800, fontSize: 26 }}>
          样片 · 配音与出镜为占位
        </div>
      ) : null}
      <EndCard tl={tl} />
      <Audio src={staticFile(tl.audio)} />
    </AbsoluteFill>
  );
};
