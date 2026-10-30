import { useState } from 'react';
import { continueRender, delayRender, staticFile } from 'remotion';
import { FONT } from './layout';

let loaded: Promise<void> | null = null;

const load = () => {
  if (!loaded) {
    const faces = [
      new FontFace(FONT.sans, `url(${staticFile('fonts/sans.ttf')})`, { weight: '100 900' }),
      new FontFace(FONT.display, `url(${staticFile('fonts/display.ttf')})`),
    ];
    loaded = Promise.all(
      faces.map((f) => f.load().then((ff) => { (document.fonts as unknown as { add: (f: FontFace) => void }).add(ff); })),
    ).then(() => undefined);
  }
  return loaded;
};

// Block rendering until both fonts are ready, otherwise the first frames fall back to system fonts.
export const useFonts = () => {
  const [handle] = useState(() => delayRender('fonts'));
  useState(() => {
    load().then(() => continueRender(handle)).catch((e) => { console.error(e); continueRender(handle); });
    return null;
  });
};
