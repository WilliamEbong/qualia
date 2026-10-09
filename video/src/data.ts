import snapshot from '../../demo/snapshot.json';

// Everything shown from the demo is read from the public AnnoMI snapshot, never typed in by hand.
const {project} = snapshot;
const SOURCE_ID = 100; // AnnoMI transcript 125
const source = project.sources.find((s) => s.id === SOURCE_ID)!;
const codeName = new Map(project.codes.map((c) => [c.id, c.name]));
const coding = new Map(project.current_codings.map((c) => [c.segment_id, c]));
const event = new Map(project.coding_events.map((e) => [e.segment_id, e]));

export const sourceName = source.name;

export const lines = project.segments
  .filter((s) => s.source_id === SOURCE_ID)
  .sort((a, b) => a.ordinal - b.ordinal)
  .slice(0, 4)
  .map((s) => ({
    id: s.id,
    speaker: s.speaker as string,
    text: source.text.slice(s.start, s.end),
    code: codeName.get(coding.get(s.id)!.code_id) as 'reflection' | 'neutral',
  }));

// Provenance of the first therapist line, exactly as recorded.
const first = lines.find((l) => l.speaker === 'therapist')!;
const ev = event.get(first.id)!;
const version = project.codebook_versions.find((v) => v.id === ev.codebook_version_id)!;

export const provenance = {
  passage: first.text,
  code: first.code,
  action: ev.action,
  actorType: ev.actor_type,
  actor: ev.actor.split(' (')[0],
  codebookVersion: version.id,
  codebookHash: version.hash.slice(0, 8),
  pipeline: ev.pipeline_version.slice(0, 8),
  recorded: ev.created_at.slice(0, 19).replace('T', ' ') + ' UTC',
};

// Published, measured experiment results (README "Tune the AI without touching your methodology").
export const tuning = {
  rows: [
    {metric: 'Macro F1 (higher is better)', values: ['0.523', '0.567', '0.572']},
    {metric: 'Exact code-set match', values: ['0.365', '0.405', '0.399']},
    {metric: 'Calibration error (lower is better)', values: ['0.050', '0.038', '0.036']},
  ],
  caption: 'Threshold tuning, no AI agent involved · AnnoMI demo · Jev · 1,258 validation segments',
};
