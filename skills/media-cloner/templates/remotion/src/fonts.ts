import { useState } from 'react';
import { continueRender, delayRender, staticFile } from 'remotion';
import { T } from './tokens';

let loaded: Promise<void> | null = null;

const load = () => {
  if (!loaded) {
    const title = T.fonts.titleFile
      ? new FontFace(T.fonts.titleFace, `url(${staticFile(T.fonts.titleFile)})`).load()
          .then((f) => { (document.fonts as unknown as { add: (f: FontFace) => void }).add(f); })
          .catch(() => console.warn(`${T.fonts.titleFile} missing; titles use the fallback family`))
      : Promise.resolve();
    // System fonts named in tokens.fonts.preload must be resolved before the first frame is captured.
    loaded = title.then(() => Promise.all(T.fonts.preload.map((spec) => document.fonts.load(spec)))).then(() => undefined);
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
