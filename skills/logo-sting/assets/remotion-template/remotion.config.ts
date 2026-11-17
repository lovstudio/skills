import {Config} from '@remotion/cli/config';

// Frames as JPEG 92 (as the reference film's master); codec, CRF, audio and colour flags come from render_sting.py.
Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(92);
Config.setDelayRenderTimeoutInMilliseconds(120000);
// The work dir is throwaway and node_modules may be a link to another install: keep webpack's cache out of it.
Config.setCachingEnabled(false);
