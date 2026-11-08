import React from 'react';
import { AbsoluteFill, Img, staticFile } from 'remotion';
import { CARD, COLOR, FONT, SUB, TITLE, W, WINDOW, units } from './style';

export type TitleLine = { text: string; fill: 'yellow' | 'red' | 'white'; red_words?: string[] };

const fillOf = (f: TitleLine['fill']) => (f === 'yellow' ? COLOR.yellow : f === 'red' ? COLOR.red : COLOR.white);

// Two stacked layers: a fat dark stroke behind, the fill on top (keeps glyphs from being eaten by the stroke).
const Stroked: React.FC<{ text: string; size: number; fill: string; redWords?: string[]; font: string; stroke: number; strokeColor: string; weight?: number }> = ({ text, size, fill, redWords = [], font, stroke, strokeColor, weight = 400 }) => {
  const parts: { t: string; red: boolean }[] = [];
  let rest = text;
  while (rest.length) {
    const hit = redWords.map((w) => ({ w, i: rest.indexOf(w) })).filter((x) => x.i >= 0).sort((a, b) => a.i - b.i)[0];
    if (!hit) { parts.push({ t: rest, red: false }); break; }
    if (hit.i > 0) parts.push({ t: rest.slice(0, hit.i), red: false });
    parts.push({ t: hit.w, red: true });
    rest = rest.slice(hit.i + hit.w.length);
  }
  const base: React.CSSProperties = { fontFamily: font, fontSize: size, fontWeight: weight, lineHeight: 1.12, whiteSpace: 'pre', letterSpacing: 1 };
  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <div style={{ ...base, color: strokeColor, WebkitTextStroke: `${stroke}px ${strokeColor}` }}>{text}</div>
      <div style={{ ...base, position: 'absolute', inset: 0, WebkitTextStroke: `${Math.max(1, size * 0.02)}px currentColor` }}>
        {parts.map((p, i) => <span key={i} style={{ color: p.red ? COLOR.red : fill }}>{p.t}</span>)}
      </div>
    </div>
  );
};

export const TopTitle: React.FC<{ lines: TitleLine[]; top?: number; maxSize?: number }> = ({ lines, top = TITLE.top, maxSize = TITLE.maxSize }) => (
  <AbsoluteFill style={{ top, height: 'auto', alignItems: 'center', display: 'flex', flexDirection: 'column', gap: TITLE.gap }}>
    {lines.map((l, i) => {
      // One size for both lines (as in the source); the longer line fills ~90% width.
      // Smiley Sans advances ≈0.754 em per CJK unit (measured on the first render).
      const longest = Math.max(...lines.map((x) => units(x.text)));
      const size = Math.min(maxSize, Math.floor((W * 0.9) / Math.max(1, longest * 0.754)));
      return <Stroked key={i} text={l.text} size={size} fill={fillOf(l.fill)} redWords={l.red_words} font={FONT.title} stroke={TITLE.stroke} strokeColor={COLOR.stroke} />;
    })}
  </AbsoluteFill>
);

export const Subtitle: React.FC<{ text: string }> = ({ text }) => {
  const size = Math.min(SUB.size, Math.floor(SUB.maxWidth / Math.max(1, units(text))));
  return (
    <AbsoluteFill style={{ top: SUB.top, height: 'auto', alignItems: 'center', display: 'flex', flexDirection: 'column' }}>
      <div style={{ filter: 'drop-shadow(0 2px 2px rgba(0,0,0,0.55))' }}>
        <Stroked text={text} size={size} fill={COLOR.subFill} font={FONT.serif} weight={700} stroke={SUB.stroke} strokeColor={COLOR.subStroke} />
      </div>
    </AbsoluteFill>
  );
};

export const GuestCard: React.FC<{ header: string; lines: string[] }> = ({ header, lines }) => (
  <div style={{ position: 'absolute', left: CARD.left, top: CARD.top, fontFamily: FONT.serif, filter: 'drop-shadow(0 2px 3px rgba(0,0,0,0.6))' }}>
    <div style={{ fontSize: CARD.headerSize, fontWeight: 900, color: COLOR.cardHeader, WebkitTextStroke: '1.5px #2a1a00', marginBottom: 8 }}>{header}</div>
    {lines.map((l, i) => (
      <div key={i} style={{ fontSize: CARD.bodySize, lineHeight: CARD.lineHeight, color: '#FFFFFF', fontWeight: 500, WebkitTextStroke: '0.6px rgba(0,0,0,0.55)' }}>{l}</div>
    ))}
  </div>
);

export const CallInWindow: React.FC<{ avatar?: string; top?: number }> = ({ avatar = 'img/avatar.svg', top = WINDOW.top }) => (
  <div style={{ position: 'absolute', left: WINDOW.left, top, width: WINDOW.w, height: WINDOW.h, background: COLOR.window,
    borderRadius: WINDOW.radius, display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 14px rgba(0,0,0,0.35)' }}>
    <Img src={staticFile(avatar)} style={{ width: WINDOW.w * 0.72, height: WINDOW.w * 0.72 }} />
  </div>
);

// SMPTE-like test bars as seen in the source separator (5 saturated bars, reverse strip, pluge row).
export const ColorBars: React.FC = () => {
  const top = ['#EAC80C', '#2EE8C4', '#22D63A', '#B813C6', '#D2122E'];
  const mid = ['#000000', '#B813C6', '#000000', '#2EE8C4', '#000000'];
  return (
    <AbsoluteFill style={{ background: '#000' }}>
      <div style={{ display: 'flex', height: '67%' }}>{top.map((c, i) => <div key={i} style={{ flex: 1, background: c }} />)}</div>
      <div style={{ display: 'flex', height: '8%' }}>{mid.map((c, i) => <div key={i} style={{ flex: 1, background: c }} />)}</div>
      <div style={{ display: 'flex', height: '25%' }}>
        <div style={{ flex: 1.25, background: '#E8DDF0' }} /><div style={{ flex: 1.25, background: '#4B0E8C' }} /><div style={{ flex: 2.5, background: '#000' }} />
      </div>
    </AbsoluteFill>
  );
};
