import React from 'react';
import { AbsoluteFill, Img, staticFile } from 'remotion';
import { C, FONT, outlined } from './layout';
import { useFonts } from './fonts';
import type { CoverSpec } from './types';

// a cut-out is shown at most 10% above its pixel size: blown-up portraits look soft on a phone
const MAX_UPSCALE = 1.1;

// visual width of a line: CJK = 1 em, Latin/digits ≈ 0.58 em
const ems = (s: string) => [...s].reduce((n, ch) => n + (/[\u0000-ÿ]/.test(ch) ? 0.58 : 1), 0);

// One visual for both slots (style-grammar §7): 3:4 Channels card and 16:9 Bilibili card.
export const Cover: React.FC<{ spec: CoverSpec; ratio: '34' | '169' }> = ({ spec, ratio }) => {
  useFonts();
  const wide = ratio === '169';
  const Wd = wide ? 1920 : 1080, Hd = wide ? 1080 : 1440;
  const lines = spec.headline ?? [];
  const textW = wide ? 1060 : Wd - 110;
  const longest = Math.max(1, ...lines.map(ems));
  const size = Math.min(wide ? 210 : 196, Math.floor(textW / longest));
  const cards = (spec.cards ?? []).slice(0, 3);
  return (
    <AbsoluteFill style={{ background: C.ink, overflow: 'hidden' }}>
      {spec.bg ? (
        <Img src={staticFile(spec.bg)} style={{ position: 'absolute', width: '100%', height: '100%', objectFit: 'cover',
          filter: 'blur(8px) brightness(0.4) saturate(1.2)', transform: 'scale(1.08)' }} />
      ) : null}
      <AbsoluteFill style={{ background: wide
        ? `radial-gradient(circle at 72% 58%, ${C.orange} 0%, #A83C00 20%, rgba(58,22,0,0.92) 44%, rgba(11,7,5,0.97) 74%)`
        : `radial-gradient(circle at 62% 70%, ${C.orange} 0%, #A83C00 22%, rgba(58,22,0,0.92) 46%, rgba(11,7,5,0.97) 76%)` }} />
      {/* evidence cards behind the author */}
      {cards.map((c, i) => {
        const pos = wide
          ? [{ l: 90, t: 640, r: -6 }, { l: 520, t: 700, r: 5 }, { l: 880, t: 610, r: -3 }][i]
          : [{ l: 40, t: 860, r: -7 }, { l: 330, t: 930, r: 5 }, { l: 120, t: 1130, r: -2 }][i];
        const cw = wide ? 420 : 400;
        return (
          <Img key={c} src={staticFile(c)} style={{ position: 'absolute', left: pos.l, top: pos.t, width: cw, height: cw * 0.64,
            objectFit: 'cover', objectPosition: '50% 0%', borderRadius: 18, border: `6px solid ${C.amber}`,
            boxShadow: '0 18px 40px rgba(0,0,0,0.6), 0 0 30px rgba(255,140,0,0.45)', transform: `rotate(${pos.r}deg)` }} />
        );
      })}
      {spec.cutout ? (
        <Img src={staticFile(spec.cutout)} style={{ position: 'absolute', bottom: 0,
          right: wide ? 40 : -30, objectFit: 'contain',
          height: Math.min(wide ? Hd * 0.96 : Hd * 0.64, spec.cutoutPx ? spec.cutoutPx[1] * MAX_UPSCALE : Infinity),
          filter: 'drop-shadow(0 0 28px rgba(255,150,30,0.75)) drop-shadow(0 20px 30px rgba(0,0,0,0.6))' }} />
      ) : null}
      <div style={{ position: 'absolute', left: wide ? 80 : 55, top: wide ? 90 : 70, width: textW,
        transform: 'skewX(-6deg) rotate(-2deg)', transformOrigin: '0 0' }}>
        {lines.map((ln, i) => (
          <div key={i} style={{ fontFamily: FONT.sans, fontWeight: 900, fontSize: size, lineHeight: 1.06, whiteSpace: 'nowrap',
            color: (spec.accent ?? []).includes(i) ? C.yellow : C.white, ...outlined(Math.round(size * 0.1)),
            textShadow: `${Math.round(size * 0.06)}px ${Math.round(size * 0.06)}px 0 #000, 0 0 50px rgba(255,120,0,0.6)`,
            marginLeft: i % 2 === 1 ? size * 0.35 : 0 }}>{ln}</div>
        ))}
        {spec.tag ? (
          <div style={{ display: 'inline-block', marginTop: size * 0.18, marginLeft: lines.length % 2 === 1 ? size * 0.35 : 0,
            padding: wide ? '14px 34px' : '12px 30px', borderRadius: 16, background: C.yellow, color: '#111',
            fontFamily: FONT.sans, fontWeight: 900, fontSize: wide ? 68 : 60, border: '6px solid #000',
            boxShadow: '8px 8px 0 #000', transform: 'rotate(-3deg)' }}>{spec.tag}</div>
        ) : null}
      </div>
      {spec.logo ? (
        <Img src={staticFile(spec.logo)} style={{ position: 'absolute', height: wide ? 70 : 64,
          right: wide ? undefined : 50, left: wide ? 80 : undefined, top: wide ? undefined : 56, bottom: wide ? 60 : undefined,
          filter: 'drop-shadow(0 3px 6px rgba(0,0,0,0.7))' }} />
      ) : null}
    </AbsoluteFill>
  );
};
