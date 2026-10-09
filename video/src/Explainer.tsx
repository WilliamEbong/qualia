import {AbsoluteFill, Series, useCurrentFrame} from 'remotion';
import {lines, provenance, sourceName, tuning} from './data';
import {Appear, codeColor, color, font, Heading, HORIZON, KeyCap, MARGIN, Mono, ramp, Scene} from './theme';

const DUR = {title: 120, premise: 135, coding: 600, evidence: 270, experiments: 420, close: 255};
export const TOTAL_FRAMES = Object.values(DUR).reduce((a, b) => a + b, 0);

const Title: React.FC = () => (
  <Scene dur={DUR.title} dark horizon>
    <Appear at={15} style={{position: 'absolute', left: MARGIN, bottom: 1080 - HORIZON + 110}}>
      <Heading style={{fontSize: 200, color: color.ivory}}>Qualia</Heading>
    </Appear>
    <Appear at={40} style={{position: 'absolute', left: MARGIN, bottom: 1080 - HORIZON + 40}}>
      <Mono style={{fontSize: 36, color: '#F3EFE4CC'}}>Qualitative coding you can audit.</Mono>
    </Appear>
  </Scene>
);

const Premise: React.FC = () => (
  <Scene dur={DUR.premise} horizon>
    <div style={{position: 'absolute', left: MARGIN, bottom: 1080 - HORIZON + 40}}>
      <Appear at={8}><Heading style={{fontSize: 96, color: color.graphite}}>AI can code your interviews.</Heading></Appear>
      <Appear at={60}><Heading style={{fontSize: 96, marginTop: 16}}>Qualia makes it show its work.</Heading></Appear>
    </div>
  </Scene>
);

// One transcript, two beats: you code by hand, then the AI suggests and you decide.
const T = {
  human: {1: 96, 0: 171, 2: 226} as Record<number, number>,
  focus: {1: [60, 150], 0: [150, 200], 2: [200, 270]} as Record<number, [number, number]>,
  suggest: 290,
  accept: 430,
};

const Row: React.FC<{i: number}> = ({i}) => {
  const frame = useCurrentFrame();
  const line = lines[i];
  const tint = codeColor[line.code];
  const humanAt = T.human[i];
  const isSuggestion = humanAt === undefined;
  const shownAt = isSuggestion ? T.suggest : humanAt;
  const accepted = isSuggestion && frame >= T.accept + 6;
  const on = ramp(frame, shownAt, 6);
  const [from, to] = isSuggestion ? [T.suggest, T.accept + 40] : T.focus[i];
  const focused = frame >= from && frame < to;
  return (
    <Appear at={i * 6}>
      <div style={{display: 'flex', gap: 48, alignItems: 'flex-start', marginBottom: 22}}>
        <div style={{flex: 1, paddingLeft: 26, borderLeft: `6px ${isSuggestion && !accepted ? 'dashed' : 'solid'} ${
          on ? tint : 'transparent'}`, outline: focused ? `3px solid ${color.prussian}` : '3px solid transparent',
          outlineOffset: 8}}>
          <Mono style={{fontSize: 22}}>{line.speaker}</Mono>
          <div style={{fontFamily: font.body, fontSize: 34, lineHeight: 1.45, color: color.ink}}>
            <span style={{backgroundColor: `${tint}${Math.round(on * 0x38).toString(16).padStart(2, '0')}`}}>
              {line.text}
            </span>
          </div>
        </div>
        <div style={{width: 520, opacity: on, paddingTop: 30}}>
          <div style={{fontFamily: font.body, fontSize: 30, fontWeight: 500, color: color.ink}}>
            <span style={{display: 'inline-block', width: 18, height: 18, backgroundColor: tint, marginRight: 14}} />
            {line.code}{accepted && <span style={{fontFamily: font.mono, fontWeight: 400, marginLeft: 14}}>m</span>}
          </div>
          <Mono style={{fontSize: 22}}>
            {!isSuggestion ? 'human · codebook v1 (frozen)' : accepted ? 'accepted by you' : 'suggested · model-reported 0.60'}
          </Mono>
          {isSuggestion && !accepted && (
            <Mono style={{fontSize: 22, color: color.uncertain}}>! Below review threshold (0.70)</Mono>
          )}
        </div>
      </div>
    </Appear>
  );
};

const Coding: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <Scene dur={DUR.coding}>
      <div style={{position: 'absolute', left: MARGIN, top: 90, right: MARGIN}}>
        <div style={{position: 'relative', height: 100}}>
          <Appear at={0} out={T.suggest - 12} style={{position: 'absolute'}}><Heading>You code the passages.</Heading></Appear>
          <Appear at={T.suggest} style={{position: 'absolute'}}><Heading>AI suggests. You decide.</Heading></Appear>
        </div>
        <Mono style={{marginTop: 12, marginBottom: 44}}>{sourceName} · AnnoMI demo</Mono>
        {lines.map((_, i) => <Row key={i} i={i} />)}
      </div>
      <div style={{position: 'absolute', right: MARGIN, bottom: 70, display: 'flex', gap: 18, alignItems: 'center'}}>
        {frame < T.suggest ? (
          <><Mono>press</Mono><KeyCap label="1" pressAt={T.human[1] - 6} /><Mono>reflection</Mono>
            <KeyCap label="7" pressAt={frame < 200 ? T.human[0] - 6 : T.human[2] - 6} />
            <Mono>neutral</Mono></>
        ) : (
          <><Mono>press</Mono><KeyCap label="a" pressAt={T.accept} /><Mono>accept</Mono>
            <KeyCap label="r" pressAt={-99} /><Mono>reject</Mono></>
        )}
      </div>
      <Appear at={T.suggest} style={{position: 'absolute', left: MARGIN, bottom: 76}}>
        <Mono style={{fontSize: 20}}>demonstration · synthetic suggestion · no matching validation ECE yet</Mono>
      </Appear>
    </Scene>
  );
};

const Evidence: React.FC = () => {
  const p = provenance;
  const rows: [string, string][] = [
    ['passage', `“${p.passage}”`],
    ['code', `${p.code} · ${p.action}`],
    ['actor', `${p.actorType} · ${p.actor}`],
    ['codebook', `v${p.codebookVersion} · frozen · ${p.codebookHash}`],
    ['pipeline', p.pipeline],
    ['recorded', p.recorded],
  ];
  return (
    <Scene dur={DUR.evidence}>
      <div style={{position: 'absolute', left: MARGIN, top: 110, right: MARGIN}}>
        <Appear at={0}><Heading>Every decision keeps its evidence.</Heading></Appear>
        <Appear at={14} style={{marginTop: 56, backgroundColor: color.cream, borderTop: `1px solid ${color.keyline}`,
          borderBottom: `1px solid ${color.keyline}`, borderLeft: `6px solid ${codeColor.reflection}`, padding: '36px 48px'}}>
          {rows.map(([k, v], i) => (
            <Appear key={k} at={24 + i * 12} style={{display: 'flex', gap: 40, marginBottom: 10}}>
              <Mono style={{width: 200, flexShrink: 0}}>{k}</Mono>
              <Mono style={{color: color.ink}}>{v}</Mono>
            </Appear>
          ))}
        </Appear>
        <Appear at={120} style={{marginTop: 48}}>
          <div style={{fontFamily: font.body, fontSize: 34, lineHeight: 1.45, color: color.graphite, maxWidth: 1400}}>
            Model suggestions also record the backend, model, prompt and model-reported score.
            The history is append-only: nothing is silently changed.
          </div>
        </Appear>
      </div>
    </Scene>
  );
};

const Dot: React.FC<{at: number; x: number; keep: boolean; label: string; note: string}> = ({at, x, keep, label, note}) => {
  const tint = keep ? color.viridian : color.rust;
  return (
    <Appear at={at} style={{position: 'absolute', left: x, top: 260 - 16}}>
      <div style={{width: 32, height: 32, borderRadius: '50%', backgroundColor: tint}} />
      <div style={{marginTop: 18, borderLeft: `6px solid ${tint}`, paddingLeft: 16}}>
        <Mono style={{color: color.ink}}>{label}</Mono>
        <Mono style={{fontSize: 22}}>{note}</Mono>
      </div>
    </Appear>
  );
};

const Experiments: React.FC = () => {
  const frame = useCurrentFrame();
  const cols = ['Before', 'After', 'Fresh confirmation'];
  const cell: React.CSSProperties = {padding: '14px 24px', borderBottom: `1px solid ${color.keyline}`};
  return (
    <Scene dur={DUR.experiments}>
      <div style={{position: 'absolute', left: MARGIN, top: 90}}>
        <Appear at={0}><Heading>Improvements are measured, not claimed.</Heading></Appear>
      </div>
      <Appear at={20} style={{position: 'absolute', left: MARGIN, right: MARGIN, top: 260, height: 1,
        backgroundColor: color.horizon}}><span /></Appear>
      <Dot at={36} x={MARGIN + 120} keep={false} label="REVERT · no gain" note="synthetic live check · macro F1 1.000 → 1.000" />
      <Dot at={72} x={MARGIN + 860} keep label="KEEP · measured gain" note="threshold tuning · AnnoMI demo" />
      <div style={{position: 'absolute', left: MARGIN, right: MARGIN, top: 470}}>
        <table style={{width: '100%', borderCollapse: 'collapse', fontSize: 28, color: color.ink}}>
          <thead>
            <tr style={{borderTop: `2px solid ${color.ink}`, backgroundColor: color.cream}}>
              <th style={{...cell, textAlign: 'left', fontFamily: font.body, fontWeight: 500}}>Validation</th>
              {cols.map((c, i) => (
                <th key={c} style={{...cell, textAlign: 'left', fontFamily: font.body, fontWeight: 500,
                  opacity: ramp(frame, 110 + i * 45)}}>{c}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tuning.rows.map((r) => (
              <tr key={r.metric}>
                <td style={{...cell, fontFamily: font.body, backgroundColor: color.cream}}>{r.metric}</td>
                {r.values.map((v, i) => (
                  <td key={i} style={{...cell, fontFamily: font.mono, opacity: ramp(frame, 110 + i * 45)}}>{v}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        <Appear at={110}><Mono style={{fontSize: 22, marginTop: 14}}>{tuning.caption}</Mono></Appear>
        <Appear at={260} style={{marginTop: 44, borderLeft: `6px solid ${color.viridian}`, paddingLeft: 24}}>
          <Mono style={{color: color.ink, fontSize: 30}}>KEEP · gain on held-out validation data, confirmed by a fresh run</Mono>
          <div style={{fontFamily: font.body, fontSize: 34, color: color.graphite, marginTop: 10}}>
            Qualia’s measured policy decides KEEP or REVERT, never the AI agent.
          </div>
        </Appear>
      </div>
    </Scene>
  );
};

const Close: React.FC = () => {
  const frame = useCurrentFrame();
  const plate = ramp(frame, 110, 15);
  return (
    <AbsoluteFill>
      <Scene dur={DUR.close + 9} horizon>
        <div style={{position: 'absolute', left: MARGIN, bottom: 1080 - HORIZON + 40}}>
          <Appear at={6}><Heading style={{fontSize: 80}}>Runs on your computer.</Heading></Appear>
          <Appear at={36}><Heading style={{fontSize: 80, marginTop: 8}}>External AI stays off until you allow it.</Heading></Appear>
        </div>
        <Appear at={66} style={{position: 'absolute', left: MARGIN, top: HORIZON + 32}}>
          <Mono style={{fontSize: 30}}>Every external call is budgeted and logged.</Mono>
        </Appear>
      </Scene>
      <AbsoluteFill style={{opacity: plate}}>
        <Scene dur={DUR.close + 9} dark horizon>
          <div style={{position: 'absolute', left: MARGIN, bottom: 1080 - HORIZON + 170}}>
            <Heading style={{fontSize: 200, color: color.ivory}}>Qualia</Heading>
          </div>
          <div style={{position: 'absolute', left: MARGIN, bottom: 1080 - HORIZON + 40}}>
            <Mono style={{fontSize: 36, color: '#F3EFE4CC'}}>Qualitative coding you can audit.</Mono>
            <Mono style={{fontSize: 26, color: '#F3EFE4CC', marginTop: 20}}>
              github.com/WilliamEbong/qualia · williamebong.github.io/qualia
            </Mono>
          </div>
        </Scene>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const Explainer: React.FC = () => (
  <Series>
    <Series.Sequence durationInFrames={DUR.title}><Title /></Series.Sequence>
    <Series.Sequence durationInFrames={DUR.premise}><Premise /></Series.Sequence>
    <Series.Sequence durationInFrames={DUR.coding}><Coding /></Series.Sequence>
    <Series.Sequence durationInFrames={DUR.evidence}><Evidence /></Series.Sequence>
    <Series.Sequence durationInFrames={DUR.experiments}><Experiments /></Series.Sequence>
    <Series.Sequence durationInFrames={DUR.close}><Close /></Series.Sequence>
  </Series>
);
