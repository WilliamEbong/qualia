import {Config} from '@remotion/cli/config';

// public/ holds the tutorial recordings (gitignored); plates are imported from web/public in theme.tsx.
Config.setPublicDir('public');
Config.setMuted(true);
Config.setCodec('h264');
