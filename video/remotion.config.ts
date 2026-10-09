import {Config} from '@remotion/cli/config';

// Reuse the web app's generated plates instead of copying binaries.
Config.setPublicDir('../web/public');
Config.setMuted(true);
Config.setCodec('h264');
