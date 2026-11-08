import React from 'react';
import { AbsoluteFill, Audio, Freeze, OffthreadVideo, Sequence, staticFile, useCurrentFrame } from 'remotion';
import { CallInWindow, ColorBars, GuestCard, Subtitle, TopTitle, TitleLine } from './overlays';
import { useFonts } from './fonts';

export type RenderPlan = {
  fps: number; width: number; height: number; frames: number;
  video: { from: number; frames: number; src: string; startFrom?: number; freeze?: number }[];
  bars: { from: number; frames: number };
  audio: string;
  title: { lines: TitleLine[]; fromF: number; toF: number };
  card: { header: string; lines: string[]; fromF: number; toF: number } | null;
  callIn: { fromF: number; toF: number } | null;
  subtitles: { fromF: number; toF: number; text: string }[];
};

const Base: React.FC<{ src: string }> = ({ src }) => (
  <OffthreadVideo src={staticFile(src)} muted style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
);

export const Demo: React.FC<{ plan: RenderPlan }> = ({ plan }) => {
  useFonts();
  const f = useCurrentFrame();
  const sub = plan.subtitles.find((c) => f >= c.fromF && f < c.toF);
  return (
    <AbsoluteFill style={{ background: '#000' }}>
      {plan.video.map((v, i) => (
        <Sequence key={i} from={v.from} durationInFrames={v.frames}>
          {v.freeze !== undefined
            ? <Freeze frame={v.freeze}><Base src={v.src} /></Freeze>
            : <OffthreadVideo src={staticFile(v.src)} muted startFrom={v.startFrom ?? 0} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />}
        </Sequence>
      ))}
      <Sequence from={plan.bars.from} durationInFrames={plan.bars.frames}><ColorBars /></Sequence>
      <Audio src={staticFile(plan.audio)} />
      {plan.card && f >= plan.card.fromF && f < plan.card.toF && <GuestCard header={plan.card.header} lines={plan.card.lines} />}
      {f >= plan.title.fromF && f < plan.title.toF && <TopTitle lines={plan.title.lines} />}
      {plan.callIn && f >= plan.callIn.fromF && f < plan.callIn.toF && <CallInWindow />}
      {sub && !(f >= plan.bars.from && f < plan.bars.from + plan.bars.frames) && <Subtitle text={sub.text} />}
    </AbsoluteFill>
  );
};
