import {AbsoluteFill, CalculateMetadataFunction, OffthreadVideo, Series, staticFile, useCurrentFrame} from 'remotion';
import {Appear, color, font, Heading, HORIZON, MARGIN, Mono, ramp, Scene} from '../theme';
import {Card, Step, Timeline, tutorials} from './list';

const FPS = 30;
const INTRO = 120;
const OUTRO = 120;
// The recording plays at 1:1 (1600x900 viewport) so UI text stays sharp; captions sit underneath.
const REC = {left: MARGIN, top: 28, width: 1600, height: 900};
const CAPTION_TOP = REC.top + REC.height + 24;

type Props = {id: string; timeline: Timeline | null};

const frames = (ms: number) => Math.round((ms * FPS) / 1000);
const stepFrames = (s: Step) => (s.card ? frames(s.cardMs ?? 4000) : Math.round((frames(s.endMs) - frames(s.startMs)) / (s.rate ?? 1)));
const bodyFrames = (t: Timeline | null) => (t ? t.steps.reduce((sum, s) => sum + stepFrames(s), 0) : 0);

export const tutorialMetadata: CalculateMetadataFunction<Props> = async ({props, abortSignal}) => {
  const response = await fetch(staticFile(`recordings/${props.id}.json`), {signal: abortSignal});
  const timeline: Timeline | null = response.ok ? await response.json() : null;
  return {durationInFrames: INTRO + bodyFrames(timeline) + OUTRO, props: {...props, timeline}};
};

const onPlate = '#F3EFE4CC';

const Intro: React.FC<{i: number}> = ({i}) => (
  <Scene dur={INTRO} dark horizon>
    <Appear at={8} style={{position: 'absolute', left: MARGIN, bottom: 1080 - HORIZON + 200}}>
      <Mono style={{fontSize: 30, color: onPlate}}>Qualia tutorial {i + 1} of {tutorials.length}</Mono>
    </Appear>
    <Appear at={18} style={{position: 'absolute', left: MARGIN, right: MARGIN, bottom: 1080 - HORIZON + 40}}>
      <Heading style={{fontSize: 120, color: color.ivory}}>{tutorials[i].title}</Heading>
    </Appear>
    <Appear at={36} style={{position: 'absolute', left: MARGIN, top: HORIZON + 32}}>
      <Mono style={{fontSize: 28, color: onPlate}}>User guide {tutorials[i].guide}</Mono>
    </Appear>
  </Scene>
);

const Outro: React.FC<{i: number}> = ({i}) => {
  const next = tutorials[i + 1];
  return (
    <Scene dur={OUTRO} horizon>
      <div style={{position: 'absolute', left: MARGIN, right: MARGIN, bottom: 1080 - HORIZON + 40}}>
        <Appear at={6}><Mono style={{fontSize: 30}}>{next ? `Next · tutorial ${i + 2}` : 'End of the series'}</Mono></Appear>
        <Appear at={14}>
          <Heading style={{fontSize: 104, marginTop: 12}}>{next ? next.title : 'Your work stays on your computer.'}</Heading>
        </Appear>
      </div>
      <Appear at={30} style={{position: 'absolute', left: MARGIN, top: HORIZON + 32}}>
        <Mono style={{fontSize: 28}}>Full steps: docs/USER-GUIDE.md {tutorials[i].guide}</Mono>
      </Appear>
    </Scene>
  );
};

// Steps the browser cannot show (installer, file manager, terminal) appear as a card in the recording frame.
const CardView: React.FC<{card: Card}> = ({card}) => (
  <AbsoluteFill style={{backgroundColor: color.cream, padding: '0 120px', justifyContent: 'center'}}>
    <Heading style={{fontSize: 72}}>{card.title}</Heading>
    {card.lines.map((line) => (
      <p key={line} style={{fontFamily: font.body, fontSize: 34, lineHeight: 1.4, color: color.graphite, margin: '24px 0 0'}}>{line}</p>
    ))}
    {card.command && (
      <div style={{fontFamily: font.mono, fontSize: 25, lineHeight: 1.5, marginTop: 40, padding: '20px 28px', whiteSpace: 'pre',
        border: `1px solid ${color.keyline}`, backgroundColor: color.ivory, color: color.ink}}>{card.command}</div>
    )}
  </AbsoluteFill>
);

const StepView: React.FC<{step: Step; n: number; total: number; video: string; dur: number}> = ({step, n, total, video, dur}) => {
  const frame = useCurrentFrame();
  const z = step.zoom ? ramp(frame, 0, 15) * (1 - ramp(frame, dur - 15, 15)) : 0;
  // Scale the target up to fit (at most 1.6x), centre it, and never show past the recording's edges.
  const target = step.zoom ?? {x: 0, y: 0, width: REC.width, height: REC.height};
  const fit = Math.max(1, Math.min(1.6, (0.9 * REC.width) / target.width, (0.9 * REC.height) / target.height));
  const scale = 1 + (fit - 1) * z;
  const clamp = (v: number, size: number) => Math.min(size - size / (2 * scale), Math.max(size / (2 * scale), v));
  const cx = clamp(REC.width / 2 + (target.x + target.width / 2 - REC.width / 2) * z, REC.width);
  const cy = clamp(REC.height / 2 + (target.y + target.height / 2 - REC.height / 2) * z, REC.height);
  const transform = `translate(${REC.width / 2 - cx * scale}px, ${REC.height / 2 - cy * scale}px) scale(${scale})`;
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', ...REC, overflow: 'hidden', outline: `1px solid ${color.keyline}`, backgroundColor: color.ivory}}>
        {step.card ? <CardView card={step.card} /> : (
          <OffthreadVideo src={staticFile(video)} trimBefore={frames(step.startMs)} playbackRate={step.rate ?? 1}
            style={{width: '100%', height: '100%', transform, transformOrigin: '0 0'}} />
        )}
      </div>
      <Appear at={0} style={{position: 'absolute', left: MARGIN, top: CAPTION_TOP, width: 1060}}>
        <p style={{fontFamily: font.body, fontSize: 32, lineHeight: 1.3, margin: 0, color: color.ink}}>{step.caption}</p>
      </Appear>
      <div style={{position: 'absolute', right: MARGIN, top: CAPTION_TOP + 4, textAlign: 'right'}}>
        <Mono style={{fontSize: 20}}>step {n} of {total}</Mono>
        {step.demo && <Mono style={{fontSize: 20, color: color.uncertain}}>demonstration · deterministic fake backend</Mono>}
        {(step.rate ?? 1) > 1 && <Mono style={{fontSize: 20}}>sped up {step.rate}×</Mono>}
      </div>
    </AbsoluteFill>
  );
};

export const Tutorial: React.FC<Props> = ({id, timeline}) => {
  const i = tutorials.findIndex((t) => t.id === id);
  const steps = timeline?.steps ?? [];
  const body = bodyFrames(timeline);
  return (
    <AbsoluteFill style={{backgroundColor: color.ivory}}>
      <Series>
        <Series.Sequence durationInFrames={INTRO}><Intro i={i} /></Series.Sequence>
        {timeline && body > 0 && (
          <Series.Sequence durationInFrames={body}>
            <Scene dur={body}>
              <Series>
                {steps.map((step, n) => (
                  <Series.Sequence key={n} durationInFrames={stepFrames(step)}>
                    <StepView step={step} n={n + 1} total={steps.length} video={timeline.video} dur={stepFrames(step)} />
                  </Series.Sequence>
                ))}
              </Series>
            </Scene>
          </Series.Sequence>
        )}
        <Series.Sequence durationInFrames={OUTRO}><Outro i={i} /></Series.Sequence>
      </Series>
    </AbsoluteFill>
  );
};
