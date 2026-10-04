import { formatMetric } from './evaluation-state'
import type { EvaluationMetrics } from './evaluation-state'

export type ExperimentRecord = { id: number; slug: string; agent: string; decision: string; reason: string; hypothesis: string; before_json: string; after_json: string; changed_files_json: string; commit_hash: string | null; tag: string | null; created_at: string }
type Measurement = { metrics?: EvaluationMetrics; backend?: string; model?: string; codebook_version_id?: number; pipeline_version?: string; created_at?: string; confirmation?: Measurement }

function objectValue(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value)
}
function measurement(value: unknown): Measurement | null {
  return objectValue(value) && objectValue(value.metrics) ? value as Measurement : null
}
function decode(value: string): unknown {
  try { return JSON.parse(value) } catch { return null }
}

export function experimentHistory(records: ExperimentRecord[]) {
  return records.map(record => {
    const before = measurement(decode(record.before_json))
    const after = measurement(decode(record.after_json))
    const confirmation = measurement(after?.confirmation)
    const changed = decode(record.changed_files_json)
    const files = Array.isArray(changed) && changed.every(item => typeof item === 'string') ? changed as string[] : null
    const oldScore = before?.metrics?.macro_f1
    const newScore = after?.metrics?.macro_f1
    const delta = typeof oldScore === 'number' && Number.isFinite(oldScore) && typeof newScore === 'number' && Number.isFinite(newScore) ? newScore - oldScore : null
    return { ...record, before, after, confirmation, files,
      decisionText: record.decision === 'KEEP' || record.decision === 'REVERT' ? record.decision : 'Decision unavailable',
      deltaText: delta === null ? 'n/a' : `${delta > 0 ? '+' : ''}${formatMetric(delta)}`,
      measurementsAvailable: !!before && !!after,
      rows: (['macro_f1', 'micro_f1', 'exact_match', 'partial_match', 'calls', 'calls_per_1000', 'ece'] as const).map(key => ({
        name: { macro_f1: 'Macro F1', micro_f1: 'Micro F1', exact_match: 'Exact code-set match', partial_match: 'Partial match', calls: 'Attempted calls', calls_per_1000: 'Calls per 1,000 segments', ece: 'Validation ECE' }[key],
        before: formatMetric(before?.metrics?.[key], key === 'calls' ? 0 : 3),
        after: formatMetric(after?.metrics?.[key], key === 'calls' ? 0 : 3),
        confirmation: formatMetric(confirmation?.metrics?.[key], key === 'calls' ? 0 : 3),
      })),
    }
  }).sort((left, right) => right.id - left.id)
}
