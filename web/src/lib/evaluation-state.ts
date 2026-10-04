import type { Coding } from './entities'

export type EvaluationRecord = { id: number; split: string; backend: string; model: string; codebook_version_id: number; pipeline_version: string; metrics_json: string; created_at: string }
export type Interval = [number, number]
export type MetricCode = { code_id: number; precision: number | null; recall: number | null; f1: number | null; support: number; precision_ci95?: Interval | null; recall_ci95?: Interval | null }
export type CalibrationBin = { lower: number; upper: number; count: number; mean_confidence: number | null; accuracy: number | null }
export type EvaluationMetrics = {
  review_share?: number | null; review_cutoff?: number | null; calibration_bins?: CalibrationBin[];
  per_code?: MetricCode[]; macro_f1?: number | null; micro_f1?: number | null; exact_match?: number | null; partial_match?: number | null;
  kappa?: number | null; alpha?: number | null; ece?: number | null; escalation_rate?: number | null; calls_per_1000?: number | null;
  latency_ms?: number; segment_count?: number; scored_prediction_count?: number; calls?: number; escalated_segments?: number;
  alpha_basis?: string; definitions?: Record<string, string>; identity?: { prompt_hash?: string; benchmark_hash?: string; cli_versions?: string[]; run_id?: string };
}
export type Evaluation = EvaluationRecord & { metrics: EvaluationMetrics | null }

export function parseEvaluations(records: EvaluationRecord[]): Evaluation[] {
  return records.filter(record => record.split === 'validation').map(record => {
    try {
      const value: unknown = JSON.parse(record.metrics_json)
      return { ...record, metrics: value && typeof value === 'object' && !Array.isArray(value) ? value as EvaluationMetrics : null }
    } catch { return { ...record, metrics: null } }
  }).sort((left, right) => right.id - left.id)
}

export function formatMetric(value: unknown, digits = 3): string {
  return typeof value === 'number' && Number.isFinite(value) ? value.toFixed(digits) : 'n/a'
}

export function matchingCalibration(event: Coding, runs: Evaluation[]): Evaluation | undefined {
  return runs.find(run => run.split === 'validation' && run.backend === event.backend && run.model === event.model
    && run.codebook_version_id === event.codebook_version_id && run.pipeline_version === event.pipeline_version
    && !!event.prompt_hash && run.metrics?.identity?.prompt_hash === event.prompt_hash
    && typeof run.metrics.ece === 'number' && Number.isFinite(run.metrics.ece) && run.metrics.ece >= 0 && run.metrics.ece <= 1
    && typeof run.metrics.scored_prediction_count === 'number' && run.metrics.scored_prediction_count > 0)
}

export function calibrationCaption(event: Coding, runs: Evaluation[]): string {
  const match = matchingCalibration(event, runs)
  return match ? `Validation ECE ${formatMetric(match.metrics?.ece)} · ${match.metrics?.scored_prediction_count} scored code assignments · evaluation #${match.id} · ${match.created_at}`
    : 'Validation ECE unavailable — no scored validation result matches this suggestion’s backend, model, frozen codebook, pipeline and prompt.'
}

export type BackendStatus = { name: string; available: boolean; external: boolean; reason?: string }

export function backendBlockedReason(readOnly: boolean, provider: BackendStatus | undefined, allowExternal: boolean | undefined, readOnlyText: string): string {
  return readOnly ? readOnlyText : !provider ? 'Checking backend availability…' : !provider.available ? provider.reason || 'Backend unavailable.'
    : provider.external && !allowExternal ? 'External AI is disabled for this project.' : ''
}

const finite = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value)

export function formatInterval(value: unknown, interval: unknown): string {
  const point = formatMetric(value)
  const valid = Array.isArray(interval) && interval.length === 2 && interval.every(finite)
  return point !== 'n/a' && valid ? `${point} (${interval[0].toFixed(2)}–${interval[1].toFixed(2)})` : point
}

// Bands are reading aids only; they never change a decision. Landis & Koch (1977); Krippendorff (2004).
export function reliabilityWord(metric: 'kappa' | 'alpha', value: unknown): string {
  if (!finite(value)) return ''
  if (metric === 'alpha') return value >= .8 ? 'reliable' : value >= .667 ? 'tentative' : 'insufficient'
  return value < 0 ? 'poor' : value <= .2 ? 'slight' : value <= .4 ? 'fair' : value <= .6 ? 'moderate' : value <= .8 ? 'substantial' : 'almost perfect'
}

const withBand = (metric: 'kappa' | 'alpha', value: unknown) => finite(value) ? `${formatMetric(value)} · ${reliabilityWord(metric, value)}` : formatMetric(value)

export const metricRows = (metrics: EvaluationMetrics) => [
  { label: 'Macro F1', value: formatMetric(metrics.macro_f1), help: 'Average F1 across every code, so rare codes count as much as common ones.' },
  { label: 'Micro F1', value: formatMetric(metrics.micro_f1), help: 'F1 over all code decisions pooled together, so common codes weigh more.' },
  { label: 'Exact code-set match', value: formatMetric(metrics.exact_match), help: 'Share of segments where the AI chose exactly the reference codes.' },
  { label: 'Partial match (Jaccard)', value: formatMetric(metrics.partial_match), help: 'Average overlap between AI and reference codes per segment; 1 means identical.' },
  { label: 'Cohen kappa', value: withBand('kappa', metrics.kappa), help: 'Agreement beyond chance; 1 is perfect, 0 is chance. Words follow Landis & Koch (1977).' },
  { label: 'Nominal alpha', value: withBand('alpha', metrics.alpha), help: 'Krippendorff’s agreement beyond chance: 0.800 or more is reliable, 0.667 or more supports tentative conclusions.' },
  { label: 'Validation ECE', value: formatMetric(metrics.ece), help: 'Average gap between model-reported scores and how often those suggestions were right; 0 means they match.' },
  { label: 'Escalation rate', value: formatMetric(metrics.escalation_rate), help: 'Share of segments sent on to the stronger backend.' },
  { label: 'Calls per 1,000 segments', value: formatMetric(metrics.calls_per_1000), help: 'Backend calls per 1,000 segments, a cost and speed indicator.' },
  { label: 'Total latency (ms)', value: formatMetric(metrics.latency_ms), help: 'Total time the evaluation took.' },
]

export function reviewSentence(metrics: EvaluationMetrics, threshold: unknown): string {
  const share = metrics.review_share, cutoff = metrics.review_cutoff
  if (!finite(share)) return ''
  const current = finite(threshold) ? ` Current review threshold: ${threshold.toFixed(2)}.` : ''
  if (!finite(cutoff)) return `No score cutoff reached 90% precision on this validation set, so every AI suggestion needs review.${current}`
  if (share === 0) return `All scored suggestions together already reach 90% precision on this validation set.${current}`
  return `Reviewing suggestions with a model-reported score below ${cutoff.toFixed(2)} (${Math.round(share * 100)}% of them) leaves the rest at 90% precision or better on this validation set.${current}`
}

export function calibrationRows(metrics: EvaluationMetrics) {
  return (Array.isArray(metrics.calibration_bins) ? metrics.calibration_bins : [])
    .filter(bin => finite(bin?.lower) && finite(bin.upper) && finite(bin.count) && bin.count > 0 && finite(bin.accuracy))
    .map(bin => ({ band: `${bin.lower.toFixed(1)}–${bin.upper.toFixed(1)}`, count: bin.count, meanScore: formatMetric(bin.mean_confidence, 2), correct: `${Math.round(bin.accuracy! * 100)}%` }))
}
