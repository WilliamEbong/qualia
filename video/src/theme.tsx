import {loadFont} from '@remotion/fonts';
import {AbsoluteFill, Easing, Img, interpolate, useCurrentFrame} from 'remotion';
import cormorant from '@fontsource/cormorant-garamond/files/cormorant-garamond-latin-400-normal.woff2';
import franklin from '@fontsource-variable/libre-franklin/files/libre-franklin-latin-wght-normal.woff2';
import plexMono from '@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-400-normal.woff2';
// The web app's generated plates, bundled by import so the public folder can hold recordings.
import titleDome from '../../web/public/plates/title_dome.webp';
import paper from '../../web/public/plates/paper.webp';

// Same fonts and values as web/src/styles/tokens.css; loadFont blocks rendering until each is ready.
loadFont({family: 'Cormorant Garamond', url: cormorant, weight: '400'});
loadFont({family: 'Libre Franklin', url: franklin, weight: '100 900'});
loadFont({family: 'IBM Plex Mono', url: plexMono, weight: '400'});

export const font = {
  display: "'Cormorant Garamond', Georgia, serif",
  body: "'Libre Franklin', Arial, sans-serif",
  mono: "'IBM Plex Mono', Consolas, monospace",
};

export const color = {
  ivory: '#F3EFE4', cream: '#E9E1CD', ink: '#1D1C1A', graphite: '#3C3A35', caption: '#635E54',
  keyline: '#1D1C1A4D', horizon: '#1D1C1A59', plateGround: '#1D1C1A',
  prussian: '#236292', rust: '#A2573B', viridian: '#2C9A88', ochre: '#B98A3E', uncertain: '#8A6420',
};

// Code colours follow the fixed index order: reflection is code 1, neutral is code 7.
export const codeColor = {reflection: color.prussian, neutral: color.ochre};

export const HORIZON = 1080 * 0.633;
export const MARGIN = 160;

const ease = Easing.bezier(0.3, 0, 0.7, 1);

// 0 → 1 between `start` and `start + dur` frames, eased and clamped. 9 frames = the 300ms media fade.
export const ramp = (frame: number, start: number, dur = 9) =>
  interpolate(frame, [start, start + dur], [0, 1], {easing: ease, extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

export const Appear: React.FC<{at: number; out?: number; children: React.ReactNode; style?: React.CSSProperties}> = ({
  at, out, children, style,
}) => {
  const frame = useCurrentFrame();
  const r = ramp(frame, at) * (out === undefined ? 1 : 1 - ramp(frame, out));
  return <div style={{opacity: r, transform: `translateY(${(1 - ramp(frame, at)) * 14}px)`, ...style}}>{children}</div>;
};

// Every scene fades out over its last 9 frames so cuts never jump.
export const Scene: React.FC<{dur: number; dark?: boolean; horizon?: boolean; children: React.ReactNode}> = ({
  dur, dark, horizon, children,
}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{backgroundColor: dark ? color.plateGround : color.ivory, opacity: 1 - ramp(frame, dur - 9)}}>
      <Img src={dark ? titleDome : paper}
        style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover'}} />
      {horizon && (
        <div style={{position: 'absolute', left: 0, right: 0, top: HORIZON, height: 1,
          backgroundColor: dark ? '#F3EFE459' : color.horizon}} />
      )}
      {children}
    </AbsoluteFill>
  );
};

export const Heading: React.FC<{children: React.ReactNode; style?: React.CSSProperties}> = ({children, style}) => (
  <h1 style={{fontFamily: font.display, fontWeight: 400, fontSize: 84, lineHeight: 1.04, margin: 0, color: color.ink,
    ...style}}>{children}</h1>
);

export const Mono: React.FC<{children: React.ReactNode; style?: React.CSSProperties}> = ({children, style}) => (
  <div style={{fontFamily: font.mono, fontSize: 26, lineHeight: 1.4, color: color.caption, ...style}}>{children}</div>
);

export const KeyCap: React.FC<{label: string; pressAt: number}> = ({label, pressAt}) => {
  const frame = useCurrentFrame();
  const down = frame >= pressAt && frame < pressAt + 6;
  return (
    <span style={{display: 'inline-block', minWidth: 56, padding: '6px 14px', textAlign: 'center',
      fontFamily: font.mono, fontSize: 30, border: `1px solid ${color.ink}`,
      backgroundColor: down ? color.ink : 'transparent', color: down ? color.ivory : color.ink}}>{label}</span>
  );
};
