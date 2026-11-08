import React from 'react';
import { Composition } from 'remotion';
import plan from './data/render-plan.json';
import cover from './data/cover.json';
import { Demo, RenderPlan } from './Demo';
import { Cover, CoverSpec } from './Cover';

// render-plan.json comes from scripts/build_render_plan.py; cover.json is edited by hand.
const p = plan as unknown as RenderPlan;
const c = cover as unknown as CoverSpec;

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="XiaonuanClip" component={Demo} durationInFrames={p.frames} fps={p.fps} width={p.width} height={p.height} defaultProps={{ plan: p }} />
    <Composition id="XiaonuanCover34" component={Cover} durationInFrames={1} fps={30} width={1080} height={1440} defaultProps={{ spec: c }} />
  </>
);
