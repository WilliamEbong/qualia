import type { Coding } from './entities'

export type EvaluationRecord = { id: number; split: string; backend: string; model: string; codebook_version_id: number; pipeline_version: string; metrics_json: string; created_at: string }
export type MetricCode = { code_id: number; precision: number | null; recall: number | null; f1: number | null; support: number }
export type EvaluationMetrics = {
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

export const metricRows = (metrics: EvaluationMetrics) => [
  ['Macro F1', metrics.macro_f1], ['Micro F1', metrics.micro_f1], ['Exact code-set match', metrics.exact_match],
  ['Partial match (Jaccard)', metrics.partial_match], ['Cohen kappa', metrics.kappa], ['Nominal alpha', metrics.alpha],
  ['Validation ECE', metrics.ece], ['Escalation rate', metrics.escalation_rate], ['Calls per 1,000 segments', metrics.calls_per_1000],
  ['Total latency (ms)', metrics.latency_ms],
].map(([label, value]) => ({ label: String(label), value: formatMetric(value) }))
