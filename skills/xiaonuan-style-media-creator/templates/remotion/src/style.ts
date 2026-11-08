// Layout constants for the 晓暖 call-in clip look, measured from 10 training samples
// (style-pack/xiaonuan-v0.1/style-profile.json → layout_templates.live_callin_9x16) and then
// moved inside the platform safe area (top 160 px, bottom 260 px) — an intentional deviation.
export const W = 1080;
export const H = 1920;
export const SAFE = { top: 160, bottom: 260 };

export const COLOR = {
  yellow: '#FAFA92',   // most common emphasis fill
  yellowHot: '#F6E714',
  red: '#DB0006',
  white: '#FCFCFB',
  stroke: '#0A0602',
  subFill: '#F5F3F1',
  subStroke: '#0D0807',
  cardHeader: '#FFE33A',
  window: '#3A3F47',
};

export const FONT = {
  titleFace: 'XNTitle',                               // public/fonts/title.ttf, e.g. Smiley Sans Oblique (OFL)
  title: '"XNTitle", "PingFang SC", "Heiti SC", sans-serif', // fallback when title.ttf is absent
  serif: '"Songti SC", "STSong", "Noto Serif SC", serif', // ≈ bold Song-style subtitles
};

export const TITLE = { top: SAFE.top + 10, maxSize: 100, widthFrac: 0.92, gap: 6, stroke: 16 };
export const SUB = { top: Math.round(0.766 * H), size: 50, maxWidth: 780, stroke: 7 };
export const CARD = { left: 54, top: SAFE.top + 10, headerSize: 52, bodySize: 38, lineHeight: 1.28 };
const winW = Math.round(0.174 * W);
const winH = Math.round(0.148 * H);
export const WINDOW = { w: winW, h: winH, left: W - 24 - winW, top: H - SAFE.bottom - winH, radius: 18 };

export const units = (s: string) => (s.match(/[㐀-鿿“”（）]|[A-Za-z]+|\d+(?:\.\d+)?|\s/g) || []).length;
