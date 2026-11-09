import React from 'react';
import { AbsoluteFill, Audio, Freeze, OffthreadVideo, Sequence, staticFile, useCurrentFrame } from 'remotion';
import { Card, Pip, Separator, Subtitle, TitleBlock, TitleLine } from './overlays';
import { useFonts } from './fonts';
import { color } from './tokens';

type Range = { fromF: number; toF: number };

export type RenderPlan = {
  fps: number; width: number; height: number; frames: number; background?: string;
  video: { from: number; frames: number; src: string; startFrom?: number; freeze?: number }[];
  separators: { fromF: number; frames: number; kind?: string }[];
  audio: string | null;
  titles: (Range & { lines: TitleLine[] })[];
  cards: (Range & { header: string; lines: string[] })[];
  pips: (Range & { avatar?: string })[];
  subtitles: (Range & { text: string })[];
};

const within = (f: number, r: Range) => f >= r.fromF && f < r.toF;
const fill: React.CSSProperties = { width: '100%', height: '100%', objectFit: 'cover' };

export const StyleClip: React.FC<{ plan: RenderPlan }> = ({ plan }) => {
  useFonts();
  const f = useCurrentFrame();
  const inSeparator = plan.separators.some((s) => f >= s.fromF && f < s.fromF + s.frames);
  const sub = plan.subtitles.find((c) => within(f, c));
  const card = plan.cards.find((c) => within(f, c));
  const title = plan.titles.find((t) => within(f, t));
  const pip = plan.pips.find((p) => within(f, p));
  return (
    <AbsoluteFill style={{ background: plan.background ?? color('background') }}>
      {plan.video.filter((v) => v.frames > 0).map((v, i) => (
        <Sequence key={i} from={v.from} durationInFrames={v.frames}>
          {v.freeze !== undefined
            ? <Freeze frame={v.freeze}><OffthreadVideo src={staticFile(v.src)} muted style={fill} /></Freeze>
            : <OffthreadVideo src={staticFile(v.src)} muted startFrom={v.startFrom ?? 0} style={fill} />}
        </Sequence>
      ))}
      {plan.separators.filter((s) => s.frames > 0).map((s, i) => (
        <Sequence key={`s${i}`} from={s.fromF} durationInFrames={s.frames}><Separator kind={s.kind} /></Sequence>
      ))}
      {plan.audio && <Audio src={staticFile(plan.audio)} />}
      {card && <Card header={card.header} lines={card.lines} />}
      {title && <TitleBlock lines={title.lines} />}
      {pip && <Pip avatar={pip.avatar} />}
      {sub && !inSeparator && <Subtitle text={sub.text} />}
    </AbsoluteFill>
  );
};
