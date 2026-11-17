import React from 'react';
import {Composition, type CalculateMetadataFunction} from 'remotion';
// copied in from assets/remotion/LogoSting.tsx by scripts/render_sting.py (not kept in the template)
import {LogoSting, type LogoStingProps} from './LogoSting';

// Input props ({spec, timing, audioSrc?, gain?, intro?}) come from `remotion render --props=props.json`; the timing
// sets the frame rate and the length, so picture and sting.wav share one clock.
const ASPECTS = [
  {id: 'Sting-9x16', width: 1080, height: 1920},
  {id: 'Sting-16x9', width: 1920, height: 1080},
  {id: 'Sting-1x1', width: 1080, height: 1080},
  {id: 'Sting-4x3', width: 1440, height: 1080},
];

const calculateMetadata: CalculateMetadataFunction<LogoStingProps> = ({props}) => {
  if (!props.spec || !props.timing) {
    throw new Error('lov-logo-sting: no spec/timing in the input props; render with --props=props.json (scripts/render_sting.py writes it)');
  }
  return {fps: props.timing.fps, durationInFrames: props.timing.dur};
};

export const Root: React.FC = () => (
  <>
    {ASPECTS.map((a) => (
      <Composition
        key={a.id}
        id={a.id}
        component={LogoSting}
        width={a.width}
        height={a.height}
        fps={30}
        durationInFrames={144}
        defaultProps={{} as LogoStingProps}
        calculateMetadata={calculateMetadata}
      />
    ))}
  </>
);
