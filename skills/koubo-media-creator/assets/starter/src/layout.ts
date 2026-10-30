// The only layout constants for the 1080×1920 talking-head short (references/style-grammar.md §4–§5).
// WeChat Channels covers the top ~160 px (status bar / nav) and the bottom ~260 px (description, actions).
export const W = 1080;
export const H = 1920;
export const SAFE = { top: 160, bottom: 260, side: 46 };

// split: evidence on top, the author below; captions sit on the seam
// the evidence panel starts below the very top so the status bar never hides it (top-to-edge panels
// lose their first ~100 px on phones)
export const SPLIT = { brollTop: 100, brollBottom: 1010, presenterTop: 880 };
export const CAPTION_Y = { split: 1010, face: 1330, broll: 1500 } as const;
// full-screen evidence: framed between the safe areas
export const BROLL_FULL = { top: SAFE.top + 60, bottom: H - SAFE.bottom - 260 };
export const CALLOUT_Y = { split: SAFE.top + 70, face: 1050, broll: SAFE.top + 40 } as const;
export const BADGE_Y = H - SAFE.bottom - 60; // animatic badge, clear of evidence and captions

// Palette of the genre: near-black, orange glow, yellow highlight, red evidence boxes.
export const C = {
  ink: '#0B0705',
  ember: '#3A1600',
  orange: '#FF7A00',
  amber: '#FFB020',
  yellow: '#FFD60A',
  hl: '#FFC21A',
  red: '#FF2D2D',
  white: '#FFFFFF',
};

export const FONT = {
  sans: 'ShortSans', // public/fonts/sans.ttf: a heavy-capable CJK sans (e.g. Noto Sans SC variable, wght 100–900)
  display: 'ShortDisplay', // public/fonts/display.ttf: an energetic display face (e.g. Smiley Sans); sans is the fallback
};

// Heavy outlined text: paint-order puts the stroke under the fill so glyphs keep their weight.
export const outlined = (stroke: number, color = '#000') => ({
  WebkitTextStroke: `${stroke}px ${color}`,
  paintOrder: 'stroke fill' as const,
});
