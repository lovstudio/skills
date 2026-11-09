import React from 'react';
import { AbsoluteFill, Img, staticFile } from 'remotion';
import { T, color, units } from './tokens';

export type TitleLine = { text: string; fill?: string; accent_words?: string[] };

const pieces = (text: string, words: string[]) => {
  const out: { t: string; accent: boolean }[] = [];
  let rest = text;
  while (rest.length) {
    const hit = words.map((w) => ({ w, i: rest.indexOf(w) })).filter((x) => x.w && x.i >= 0).sort((a, b) => a.i - b.i)[0];
    if (!hit) { out.push({ t: rest, accent: false }); break; }
    if (hit.i > 0) out.push({ t: rest.slice(0, hit.i), accent: false });
    out.push({ t: hit.w, accent: true });
    rest = rest.slice(hit.i + hit.w.length);
  }
  return out;
};

// Two stacked layers: a fat outline behind, the fill on top, so the stroke never eats the glyphs.
export const Stroked: React.FC<{ text: string; size: number; fill: string; font: string; stroke: number; strokeColor: string;
  weight: number; lineHeight: number; letterSpacing?: number; accentWords?: string[] }> = (
  { text, size, fill, font, stroke, strokeColor, weight, lineHeight, letterSpacing = 0, accentWords = [] }) => {
  const base: React.CSSProperties = { fontFamily: font, fontSize: size, fontWeight: weight, lineHeight, whiteSpace: 'pre', letterSpacing };
  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      {stroke > 0 && <div style={{ ...base, color: strokeColor, WebkitTextStroke: `${stroke}px ${strokeColor}` }}>{text}</div>}
      <div style={{ ...base, position: stroke > 0 ? 'absolute' : 'relative', inset: 0,
        WebkitTextStroke: stroke > 0 ? `${Math.max(1, size * 0.02)}px currentColor` : undefined }}>
        {pieces(text, accentWords).map((p, i) => <span key={i} style={{ color: p.accent ? color('accent') : fill }}>{p.t}</span>)}
      </div>
    </div>
  );
};

// All lines share one size, fitted so the longest line fills widthFrac of the frame.
export const TitleBlock: React.FC<{ lines: TitleLine[]; top?: number; maxSize?: number; width?: number }> = (
  { lines, top = T.title.top, maxSize = T.title.maxSize, width = T.canvas.width }) => {
  const longest = Math.max(1, ...lines.map((l) => units(l.text)));
  const size = Math.min(maxSize, Math.floor((width * T.title.widthFrac) / (longest * T.title.advanceEm)));
  return (
    <AbsoluteFill style={{ top, height: 'auto', alignItems: 'center', display: 'flex', flexDirection: 'column', gap: T.title.gap }}>
      {lines.map((l, i) => (
        <Stroked key={i} text={l.text} size={size} fill={color(l.fill ?? 'plain')} accentWords={l.accent_words} font={T.fonts.title}
          stroke={T.title.stroke} strokeColor={color(T.title.strokeColor)} weight={T.title.weight} lineHeight={T.title.lineHeight}
          letterSpacing={T.title.letterSpacing} />
      ))}
    </AbsoluteFill>
  );
};

export const Subtitle: React.FC<{ text: string }> = ({ text }) => {
  const rows = text.split('\n');
  const longest = Math.max(1, ...rows.map(units));
  const size = Math.min(T.subtitle.size, Math.floor(T.subtitle.maxWidth / (longest * T.subtitle.advanceEm)));
  return (
    <AbsoluteFill style={{ top: T.subtitle.top, height: 'auto', alignItems: 'center', display: 'flex', flexDirection: 'column' }}>
      <div style={{ filter: T.subtitle.shadow || undefined, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        {rows.map((r, i) => (
          <Stroked key={i} text={r} size={size} fill={color(T.subtitle.fill)} font={T.fonts.body} weight={T.subtitle.weight}
            stroke={T.subtitle.stroke} strokeColor={color(T.subtitle.strokeColor)} lineHeight={T.subtitle.lineHeight}
            letterSpacing={T.subtitle.letterSpacing} />
        ))}
      </div>
    </AbsoluteFill>
  );
};

export const Card: React.FC<{ header: string; lines: string[] }> = ({ header, lines }) => (
  <div style={{ position: 'absolute', left: T.card.left, top: T.card.top, fontFamily: T.fonts.body,
    filter: 'drop-shadow(0 2px 3px rgba(0,0,0,0.6))' }}>
    <div style={{ fontSize: T.card.headerSize, fontWeight: 900, color: color(T.card.headerFill),
      WebkitTextStroke: `1.5px ${color(T.card.headerStroke)}`, marginBottom: 8 }}>{header}</div>
    {lines.map((l, i) => (
      <div key={i} style={{ fontSize: T.card.bodySize, lineHeight: T.card.lineHeight, color: color(T.card.bodyFill), fontWeight: 500,
        WebkitTextStroke: '0.6px rgba(0,0,0,0.55)' }}>{l}</div>
    ))}
  </div>
);

export const Pip: React.FC<{ avatar?: string; top?: number }> = ({ avatar = T.pip.avatar, top }) => (
  <div style={{ position: 'absolute', left: T.canvas.width - T.pip.right - T.pip.w,
    top: top ?? T.canvas.height - T.safe.bottom - T.pip.bottom - T.pip.h, width: T.pip.w, height: T.pip.h,
    background: color(T.pip.fill), borderRadius: T.pip.radius, display: 'flex', alignItems: 'center', justifyContent: 'center',
    boxShadow: '0 4px 14px rgba(0,0,0,0.35)' }}>
    <Img src={staticFile(avatar)} style={{ width: T.pip.w * 0.72, height: T.pip.w * 0.72 }} />
  </div>
);

const Row: React.FC<{ colors: string[]; height: string; flex?: number[] }> = ({ colors, height, flex }) => (
  <div style={{ display: 'flex', height }}>
    {colors.map((c, i) => <div key={i} style={{ flex: flex?.[i] ?? 1, background: c }} />)}
  </div>
);

// kind: "bars" (test-card bars from tokens.separator), "black", "white", or any colour token / CSS colour.
export const Separator: React.FC<{ kind?: string }> = ({ kind = 'bars' }) => {
  if (kind !== 'bars') return <AbsoluteFill style={{ background: kind === 'black' ? '#000' : kind === 'white' ? '#FFF' : color(kind) }} />;
  const b = T.separator.bars;
  return (
    <AbsoluteFill style={{ background: '#000' }}>
      <Row colors={b.top} height="67%" />
      <Row colors={b.mid} height="8%" />
      <Row colors={b.bottom} height="25%" flex={[1.25, 1.25, 2.5]} />
    </AbsoluteFill>
  );
};
