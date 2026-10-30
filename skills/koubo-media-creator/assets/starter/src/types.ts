export type Layout = 'split' | 'face' | 'broll';

export type Caption = { from: number; to: number; text: string; line: string; hl: string[] };

export type Shot = {
  from: number;
  to: number;
  line: string;
  layout: Layout;
  src?: string;
  kind?: 'image' | 'video';
  w?: number;
  h?: number;
  fit?: 'cover' | 'contain';
  boxes?: number[][];
  focus?: number[] | null;
  label?: string | null;
  start?: number;
  callout?: string | null;
  missing?: string; // preview only: evidence not captured yet
};

export type Timeline = {
  fps: number;
  width: number;
  height: number;
  durationInFrames: number;
  speechFrames: number;
  animatic?: boolean;
  // placeholder: an animatic stand-in (a small portrait shown at native size, never stretched)
  presenter: { kind: 'video' | 'image'; src: string; faceY: number; placeholder?: boolean };
  logo?: string | null; // official brand logo (light version for dark footage)
  audio: string;
  watermark: string;
  captions: Caption[];
  shots: Shot[];
  end: { from: number; frames: number; name: string; handle: string; line: string; avatar: string | null; covers: string[] };
  title: string;
};

export type CoverSpec = {
  headline: string[];
  accent: number[]; // indexes of headline lines drawn in yellow
  tag?: string | null;
  cutout?: string | null; // public path of the author's cut-out PNG
  cutoutPx?: number[]; // its pixel size [w, h]; caps the display size so a small photo is never blown up
  cards?: string[]; // public paths of evidence screenshots shown as tilted cards
  bg?: string | null; // optional public path of a background image (blurred and darkened)
  logo?: string | null;
};
