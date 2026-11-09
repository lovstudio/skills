import React from 'react';
import { Composition } from 'remotion';
import plan from './data/render-plan.json';
import cover from './data/cover.json';
import { RenderPlan, StyleClip } from './Clip';
import { CoverSpec, StyleCover } from './Cover';

const p = plan as unknown as RenderPlan;
const c = cover as unknown as CoverSpec;

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="StyleClip" component={StyleClip} durationInFrames={p.frames} fps={p.fps} width={p.width} height={p.height} defaultProps={{ plan: p }} />
    <Composition id="StyleCover" component={StyleCover} durationInFrames={1} fps={30} width={c.width} height={c.height} defaultProps={{ spec: c }} />
  </>
);
