import {useMemo} from 'react';
import {AbsoluteFill, CalculateMetadataFunction, Easing, OffthreadVideo, Series, staticFile, useCurrentFrame} from 'remotion';
import {Appear, color, font, Heading, HORIZON, MARGIN, Mono, ramp, Scene} from '../theme';
import {Action, Card, Event, Step, Timeline, tutorials} from './list';

// Editorial screencast: the app sits in a keylined stage on paper; the camera frames each action up close;
// a top line names tutorial, chapter and step over a progress rule; the caption names the action as it happens.
const FPS = 30;
const INTRO = 150;
const OUTRO = 120;
const CHAPTER = 60;
const STAGE = {left: 64, top: 60, width: 1792, height: 1008};
// Height of the caption panel inside the stage; close-ups keep their target above it.
const PANEL = 160;
const GLIDE = 700;
const MAX_ZOOM = 2;

type Props = {id: string; timeline: Timeline | null};
type View = Timeline['view'];
type Cam = {t: number; z: number; cx: number; cy: number};
type Key = Cam & {from: Cam};
type Part = {kind: 'chapter'; n: number; title: string; first: number; last: number} | {kind: 'step'; n: number; step: Step};

const frames = (ms: number) => Math.round((ms * FPS) / 1000);
const stepFrames = (s: Step) => (s.card ? frames(s.cardMs ?? 4000) : Math.round((frames(s.endMs) - frames(s.startMs)) / (s.rate ?? 1)));
const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));
// The house easing (doc 04); no springs.
const glide = Easing.bezier(0.3, 0, 0.7, 1);

// Steps in order, with a chapter card before every chapter after the first.
const partsOf = (id: string, timeline: Timeline | null): Part[] => {
  const chapters = tutorials.find((t) => t.id === id)?.chapters ?? [];
  const steps = timeline?.steps ?? [];
  return steps.flatMap((step, i): Part[] => {
    const c = chapters.findIndex(([first]) => first === i + 1);
    const card: Part[] = c > 0 ? [{kind: 'chapter', n: c + 1, title: chapters[c][1], first: i + 1,
      last: (chapters[c + 1]?.[0] ?? steps.length + 1) - 1}] : [];
    return [...card, {kind: 'step', n: i + 1, step}];
  });
};
const partFrames = (p: Part) => (p.kind === 'chapter' ? CHAPTER : stepFrames(p.step));

export const tutorialMetadata: CalculateMetadataFunction<Props> = async ({props, abortSignal}) => {
  const response = await fetch(staticFile(`recordings/${props.id}.json`), {signal: abortSignal});
  const timeline: Timeline | null = response.ok ? await response.json() : null;
  const body = partsOf(props.id, timeline).reduce((sum, p) => sum + partFrames(p), 0);
  return {durationInFrames: INTRO + body + OUTRO, props: {...props, timeline}};
};

// Keep the frame inside the recorded page.
const inside = (c: Cam, view: View): Cam => {
  const hw = view.width / (2 * c.z);
  const hh = view.height / (2 * c.z);
  return {...c, cx: clamp(c.cx, hw, view.width - hw), cy: clamp(c.cy, hh, view.height - hh)};
};
const between = (a: Cam, b: Cam, p: number): Cam => ({
  t: b.t, z: a.z * Math.pow(b.z / a.z, p), cx: a.cx + (b.cx - a.cx) * p, cy: a.cy + (b.cy - a.cy) * p,
});

// The camera frames each action up close and holds still while the next action is already in view.
const cameraKeys = (events: Event[], view: View): Key[] => {
  const scale = STAGE.width / view.width;
  const wide: Cam = {t: 0, z: 1, cx: view.width / 2, cy: view.height / 2};
  const keys: Key[] = [{...wide, from: wide}];
  for (const e of events) {
    if (!e.box) continue;
    const b = e.box;
    const z = clamp(Math.min((0.7 * view.width) / (b.width + 40), (0.6 * view.height) / (b.height + 40)), 1, MAX_ZOOM);
    const shot = inside({t: e.t, z, cx: b.x + b.width / 2, cy: b.y + b.height / 2 + PANEL / (2 * scale * z)}, view);
    const cur = keys[keys.length - 1];
    const hw = view.width / (2 * cur.z);
    const hh = view.height / (2 * cur.z);
    const seen = b.x >= cur.cx - hw + 12 && b.x + b.width <= cur.cx + hw - 12 && b.y >= cur.cy - hh + 12
      && b.y + b.height <= cur.cy + hh - PANEL / (scale * cur.z) - 12;
    if (seen && Math.abs(Math.log(shot.z / cur.z)) < 0.3) continue;
    const from = between(cur.from, cur, glide(clamp((e.t - cur.t) / GLIDE, 0, 1)));
    keys.push({...shot, from});
  }
  return keys;
};

const cameraAt = (keys: Key[], t: number): Cam => {
  let k = 0;
  while (k + 1 < keys.length && keys[k + 1].t <= t) k++;
  return between(keys[k].from, keys[k], glide(clamp((t - keys[k].t) / GLIDE, 0, 1)));
};

const onPlate = '#F3EFE4CC';

const Intro: React.FC<{i: number}> = ({i}) => {
  const t = tutorials[i];
  return (
    <Scene dur={INTRO} dark horizon>
      <div style={{position: 'absolute', left: MARGIN, right: MARGIN, bottom: 1080 - HORIZON + 40}}>
        <Appear at={8}><Mono style={{fontSize: 30, color: onPlate}}>Qualia tutorial {i + 1} of {tutorials.length} · User guide {t.guide}</Mono></Appear>
        <Appear at={18}><Heading style={{fontSize: 120, color: color.ivory, marginTop: 18}}>{t.title}</Heading></Appear>
      </div>
      <div style={{position: 'absolute', left: MARGIN, right: MARGIN, top: HORIZON + 32, display: 'grid',
        gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', columnGap: 64, rowGap: 14}}>
        {t.chapters.map(([, title], n) => (
          <Appear key={title} at={36 + n * 6}><Mono style={{fontSize: 28, color: onPlate}}>{n + 1} · {title}</Mono></Appear>
        ))}
      </div>
    </Scene>
  );
};

const ChapterCard: React.FC<{i: number; part: Extract<Part, {kind: 'chapter'}>}> = ({i, part}) => (
  <Scene dur={CHAPTER} horizon>
    <div style={{position: 'absolute', left: MARGIN, right: MARGIN, bottom: 1080 - HORIZON + 40}}>
      <Appear at={0}><Mono style={{fontSize: 30}}>Part {part.n} of {tutorials[i].chapters.length}</Mono></Appear>
      <Appear at={6}><Heading style={{fontSize: 104, marginTop: 14}}>{part.title}</Heading></Appear>
    </div>
    <Appear at={12} style={{position: 'absolute', left: MARGIN, top: HORIZON + 32}}>
      <Mono style={{fontSize: 28}}>{part.first === part.last ? `Step ${part.first}` : `Steps ${part.first}–${part.last}`}</Mono>
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
          <Heading style={{fontSize: 104, marginTop: 12}}>{next ? next.title : 'Your projects stay on your computer.'}</Heading>
        </Appear>
        {!next && <Appear at={22}><Mono style={{fontSize: 30, marginTop: 16}}>External AI stays off until you allow it for a project.</Mono></Appear>}
      </div>
      <Appear at={30} style={{position: 'absolute', left: MARGIN, top: HORIZON + 32}}>
        <Mono style={{fontSize: 28}}>Full steps: docs/USER-GUIDE.md {tutorials[i].guide}</Mono>
      </Appear>
    </Scene>
  );
};

// Steps the browser cannot show (installer, file manager) appear as a card; terminal output as a terminal.
const CardView: React.FC<{card: Card}> = ({card}) => (
  <AbsoluteFill style={{padding: `0 96px ${PANEL}px`, justifyContent: 'center', backgroundColor: color.cream}}>
    <Heading style={{fontSize: 80}}>{card.title}</Heading>
    {card.lines.map((line) => (
      <p key={line} style={{fontFamily: font.body, fontSize: 38, lineHeight: 1.4, color: color.graphite, margin: '22px 0 0'}}>{line}</p>
    ))}
    {card.command && (
      <div style={{fontFamily: font.mono, fontSize: 28, lineHeight: 1.5, marginTop: 40, padding: '24px 32px', whiteSpace: 'pre',
        border: `1px solid ${color.keyline}`, backgroundColor: card.terminal ? color.plateGround : color.ivory,
        color: card.terminal ? color.ivory : color.ink}}>{card.command}</div>
    )}
  </AbsoluteFill>
);

const ActionText: React.FC<{action: Action}> = ({action}) => (
  <>
    {action.verb}
    {action.value && <> “{action.value}”</>}
    {action.target && <>{action.value ? ' in ' : ' '}<strong style={{fontWeight: 600}}>{action.target}</strong></>}
  </>
);

const StepView: React.FC<{i: number; step: Step; n: number; total: number; timeline: Timeline; keys: Key[]}> = ({
  i, step, n, total, timeline, keys,
}) => {
  const frame = useCurrentFrame();
  const rate = step.rate ?? 1;
  const t = step.startMs + (frame * 1000 * rate) / FPS;
  const cam = cameraAt(keys, t);
  const k = (STAGE.width / timeline.view.width) * cam.z;
  const at = (x: number, y: number) => ({x: STAGE.width / 2 + (x - cam.cx) * k, y: STAGE.height / 2 + (y - cam.cy) * k});
  // The action shown is the latest one in this step; it changes as the pointer starts to move.
  const mine = timeline.events.filter((e) => e.action && e.t >= step.startMs && e.t <= t);
  const current = mine[mine.length - 1];
  const since = (e: Event) => frame - Math.round(((e.t - step.startMs) * FPS) / 1000 / rate);
  const ring = !step.card && current?.box && current.action?.verb !== 'Press' ? current.box : null;
  const corner = ring && at(ring.x, ring.y);
  const keysDown = mine.filter((e) => e.action?.verb === 'Press' && since(e) < 45);
  const chapter = [...tutorials[i].chapters].reverse().find(([first]) => first <= n)?.[1];
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', left: STAGE.left, right: STAGE.left, top: 14, display: 'flex', justifyContent: 'space-between'}}>
        <Mono style={{fontSize: 20}}>Tutorial {i + 1} · {tutorials[i].title}{chapter ? ` · ${chapter}` : ''}</Mono>
        <Mono style={{fontSize: 20}}>step {n} of {total}</Mono>
      </div>
      <div style={{position: 'absolute', left: STAGE.left, width: STAGE.width, top: 46, height: 1, backgroundColor: color.keyline}} />
      <div style={{position: 'absolute', left: STAGE.left, width: (STAGE.width * n) / total, top: 45, height: 3, backgroundColor: color.ochre}} />
      <div style={{position: 'absolute', ...STAGE, overflow: 'hidden', outline: `1px solid ${color.keyline}`, backgroundColor: color.ivory}}>
        {step.card ? <CardView card={step.card} /> : (
          <OffthreadVideo src={staticFile(timeline.video)} trimBefore={frames(step.startMs)} playbackRate={rate}
            style={{position: 'absolute', left: 0, top: 0, width: STAGE.width, height: STAGE.height, transformOrigin: '0 0',
              transform: `translate(${STAGE.width / 2 - cam.cx * k}px, ${STAGE.height / 2 - cam.cy * k}px) scale(${cam.z})`}} />
        )}
        {ring && corner && current && (
          <div style={{position: 'absolute', left: corner.x - 10, top: corner.y - 10, width: ring.width * k + 20, height: ring.height * k + 20,
            border: `4px solid ${color.ochre}`, boxSizing: 'border-box', opacity: ramp(since(current), 4, 6)}} />
        )}
        {keysDown.length > 0 && (
          <div style={{position: 'absolute', right: 40, bottom: PANEL + 8, display: 'flex', gap: 12}}>
            {keysDown.map((e) => {
              const down = since(e) < 8;
              return (
                <span key={e.t} style={{fontFamily: font.mono, fontSize: 34, padding: '8px 22px', border: `1px solid ${color.ink}`,
                  backgroundColor: down ? color.ink : color.ivory, color: down ? color.ivory : color.ink,
                  opacity: 1 - ramp(since(e), 36, 9)}}>{e.action?.target}</span>
              );
            })}
          </div>
        )}
        <div style={{position: 'absolute', left: 32, right: 32, bottom: 28, minHeight: PANEL - 60, display: 'flex', alignItems: 'center',
          gap: 40, padding: '18px 32px', backgroundColor: '#F3EFE4F2', border: `1px solid ${color.keyline}`}}>
          <div style={{flex: 1}}>
            {!step.card && (
              <div style={{fontFamily: font.body, fontSize: 38, lineHeight: 1.25, color: color.ink, minHeight: 48}}>
                {current?.action && <ActionText action={current.action} />}
              </div>
            )}
            <Appear at={0}>
              <p style={{fontFamily: font.body, fontSize: step.card ? 34 : 27, lineHeight: 1.3, margin: step.card ? 0 : '6px 0 0',
                color: step.card ? color.ink : color.graphite}}>{step.caption}</p>
            </Appear>
          </div>
          {(step.demo || rate > 1) && (
            <div style={{textAlign: 'right'}}>
              {step.demo && <Mono style={{fontSize: 20, color: color.uncertain}}>demonstration · fake backend</Mono>}
              {rate > 1 && <Mono style={{fontSize: 20}}>sped up {rate}×</Mono>}
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const Tutorial: React.FC<Props> = ({id, timeline}) => {
  const i = tutorials.findIndex((t) => t.id === id);
  const parts = useMemo(() => partsOf(id, timeline), [id, timeline]);
  const body = parts.reduce((sum, p) => sum + partFrames(p), 0);
  const keys = useMemo(() => (timeline ? cameraKeys(timeline.events, timeline.view) : []), [timeline]);
  const total = timeline?.steps.length ?? 0;
  return (
    <AbsoluteFill style={{backgroundColor: color.ivory}}>
      <Series>
        <Series.Sequence durationInFrames={INTRO}><Intro i={i} /></Series.Sequence>
        {timeline && body > 0 && (
          <Series.Sequence durationInFrames={body}>
            <Scene dur={body}>
              <Series>
                {parts.map((p) => (
                  <Series.Sequence key={`${p.kind}-${p.n}`} durationInFrames={partFrames(p)}>
                    {p.kind === 'chapter' ? <ChapterCard i={i} part={p} />
                      : <StepView i={i} step={p.step} n={p.n} total={total} timeline={timeline} keys={keys} />}
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
