import React from 'react';
import { Composition } from 'remotion';
import timeline from '../public/data/timeline.json';
import cover from '../public/data/cover.json';
import { Short } from './Short';
import { Cover } from './Cover';
import type { CoverSpec, Timeline } from './types';

const tl = timeline as unknown as Timeline;
const cs = cover as unknown as CoverSpec;

// Vertical film plus one cover visual in the two slots the platforms ask for.
export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="Short" component={Short} durationInFrames={Math.max(1, tl.durationInFrames)} fps={tl.fps || 30}
      width={1080} height={1920} defaultProps={{ tl }} />
    <Composition id="Cover34" component={Cover} durationInFrames={1} fps={30} width={1080} height={1440}
      defaultProps={{ spec: cs, ratio: '34' as const }} />
    <Composition id="Cover169" component={Cover} durationInFrames={1} fps={30} width={1920} height={1080}
      defaultProps={{ spec: cs, ratio: '169' as const }} />
  </>
);
