import { Config } from '@remotion/cli/config';

// Optional: reuse an existing Chrome Headless Shell instead of downloading ~170 MB on first render.
if (process.env.REMOTION_BROWSER_EXECUTABLE) {
  Config.setBrowserExecutable(process.env.REMOTION_BROWSER_EXECUTABLE);
}
Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(92);
Config.setConcurrency(6);
Config.setOverwriteOutput(true);
