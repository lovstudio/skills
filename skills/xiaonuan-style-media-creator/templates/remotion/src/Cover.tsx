import React from 'react';
import { AbsoluteFill, OffthreadVideo, staticFile } from 'remotion';
import { CallInWindow, TopTitle, TitleLine } from './overlays';
import { useFonts } from './fonts';

// 3:4 cover: one live frame, the same two title lines enlarged at chest height (~60%), call-in window kept.
export type CoverSpec = { src: string; frame: number; lines: TitleLine[]; centerY: number; size: number };

export const Cover: React.FC<{ spec: CoverSpec }> = ({ spec }) => {
  useFonts();
  return (
    <AbsoluteFill style={{ background: '#000' }}>
      <OffthreadVideo src={staticFile(spec.src)} muted startFrom={spec.frame} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
      <TopTitle lines={spec.lines} top={Math.round(spec.centerY * 1440 - spec.size * 1.15)} maxSize={spec.size} />
      <CallInWindow top={1440 - 60 - Math.round(0.148 * 1920)} />
    </AbsoluteFill>
  );
};
