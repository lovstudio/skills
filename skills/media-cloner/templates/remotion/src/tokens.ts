import raw from './data/style-tokens.json';

// Style tokens come from the frozen style pack (layout_templates + metrics), then are moved inside
// the target platform's safe area. Every component reads these values; no style lives in the TSX.
export type Tokens = {
  canvas: { width: number; height: number; fps: number };
  safe: { top: number; bottom: number };
  colors: Record<string, string>;
  fonts: { titleFace: string; titleFile: string | null; title: string; body: string; preload: string[] };
  title: { top: number; maxSize: number; widthFrac: number; advanceEm: number; gap: number; stroke: number;
    strokeColor: string; weight: number; lineHeight: number; letterSpacing: number };
  subtitle: { top: number; size: number; maxWidth: number; advanceEm: number; stroke: number; strokeColor: string;
    fill: string; weight: number; lineHeight: number; letterSpacing: number; shadow: string };
  card: { left: number; top: number; headerSize: number; bodySize: number; lineHeight: number;
    headerFill: string; headerStroke: string; bodyFill: string };
  pip: { w: number; h: number; right: number; bottom: number; radius: number; fill: string; avatar: string };
  separator: { bars: { top: string[]; mid: string[]; bottom: string[] } };
};

export const T = raw as unknown as Tokens;

// A token name ("emphasis") or a literal CSS colour ("#FAFA92").
export const color = (name: string) => T.colors[name] ?? name;

// Width units used for fitting: one per CJK character, Latin word, number or space.
export const units = (s: string) => (s.match(/[㐀-鿿“”（）《》]|[A-Za-z]+|\d+(?:\.\d+)?|\s/g) || []).length;
