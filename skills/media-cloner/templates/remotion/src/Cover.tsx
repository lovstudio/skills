import React from 'react';
import { AbsoluteFill, Img, OffthreadVideo, staticFile } from 'remotion';
import { Pip, TitleBlock, TitleLine } from './overlays';
import { useFonts } from './fonts';
import { T, color } from './tokens';

// A cover is one frame (video, image or plain background) with the title block enlarged at centerY.
export type CoverSpec = { width: number; height: number; src?: string; frame?: number; image?: string; background?: string;
  lines: TitleLine[]; centerY: number; size: number; pip?: boolean };

export const StyleCover: React.FC<{ spec: CoverSpec }> = ({ spec }) => {
  useFonts();
  const fill: React.CSSProperties = { width: '100%', height: '100%', objectFit: 'cover' };
  return (
    <AbsoluteFill style={{ background: spec.background ?? color('background') }}>
      {spec.src && <OffthreadVideo src={staticFile(spec.src)} muted startFrom={spec.frame ?? 0} style={fill} />}
      {spec.image && <Img src={staticFile(spec.image)} style={fill} />}
      <TitleBlock lines={spec.lines} top={Math.round(spec.centerY * spec.height - spec.size * 1.15)} maxSize={spec.size} width={spec.width} />
      {spec.pip && <Pip top={spec.height - 60 - T.pip.h} />}
    </AbsoluteFill>
  );
};
