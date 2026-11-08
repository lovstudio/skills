import { useState } from 'react';
import { continueRender, delayRender, staticFile } from 'remotion';
import { FONT } from './style';

let loaded: Promise<void> | null = null;
const load = () => {
  if (!loaded) {
    const title = new FontFace(FONT.titleFace, `url(${staticFile('fonts/title.ttf')})`);
    loaded = title.load()
      .then((f) => { (document.fonts as unknown as { add: (f: FontFace) => void }).add(f); })
      .catch(() => console.warn('public/fonts/title.ttf missing; using the system fallback for titles'))
      // Songti SC is a macOS system font; make sure both weights are resolved before the first frame.
      .then(() => Promise.all([document.fonts.load('700 50px "Songti SC"'), document.fonts.load('400 38px "Songti SC"')]))
      .then(() => undefined);
  }
  return loaded;
};

export const useFonts = () => {
  const [handle] = useState(() => delayRender('fonts'));
  useState(() => {
    load().then(() => continueRender(handle)).catch((e) => { console.error(e); continueRender(handle); });
    return null;
  });
};
