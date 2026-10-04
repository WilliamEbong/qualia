import type { Coding } from './entities'

const reasonLabels: Record<string, string> = { below_threshold: 'Below review threshold', disagreement: 'Backend disagreement', qc_sample: 'Quality-control sample' }
export const eceCaption = 'Validation ECE unavailable — no validation result is available for these suggestions.'

export function reviewReasons(value: string | null): string[] {
  try {
    const reasons: unknown = JSON.parse(value ?? '[]')
    if (Array.isArray(reasons)) {
      const valid = [...new Set(reasons.filter((reason): reason is string => typeof reason === 'string' && reason.length > 0))]
      if (valid.length) return valid.map(reason => reasonLabels[reason] ?? reason)
    }
  } catch { /* Preserve reviewability when a legacy reason is not JSON. */ }
  return ['Human review']
}

export function reasonCaption(value: string | null, threshold: unknown): string {
  // The trigger was recorded at classification time; the threshold shown is today's project setting.
  const current = typeof threshold === 'number' && Number.isFinite(threshold) ? ` (current threshold ${threshold.toFixed(2)})` : ''
  return reviewReasons(value).map(reason => reason === reasonLabels.below_threshold ? reason + current : reason).join(' · ')
}

export function thresholdCaption(routing: unknown, codeId: number): string {
  const thresholds = routing && typeof routing === 'object' ? (routing as { code_thresholds?: unknown }).code_thresholds : undefined
  const value = thresholds && typeof thresholds === 'object' ? (thresholds as Record<string, unknown>)[String(codeId)] : undefined
  return typeof value === 'number' && Number.isFinite(value) ? `AI suggests at score ≥ ${value.toFixed(2)}` : ''
}

const leastCertainFirst = (left: Coding, right: Coding) => (left.score ?? Infinity) - (right.score ?? Infinity)

export function groupSuggestions(suggestions: Coding[]) {
  const groups = new Map<string, Coding[]>()
  for (const suggestion of suggestions) {
    for (const reason of reviewReasons(suggestion.review_trigger)) groups.set(reason, [...(groups.get(reason) ?? []), suggestion])
  }
  return [...groups].map(([reason, items]) => ({ reason, items: items.sort(leastCertainFirst) }))
}

export function modelScore(score: number | null): string {
  return score !== null && Number.isFinite(score) && score >= 0 && score <= 1 ? `model-reported ${score.toFixed(2)}` : 'model-reported score unavailable'
}

export function isAcceptedModel(event: Pick<Coding, 'action' | 'backend'>): boolean {
  return event.action === 'accept' || (event.action === 'assign' && !!event.backend)
}

export function reviewShortcut(key: string): 'accept' | 'reject' | null {
  return key.toLowerCase() === 'a' ? 'accept' : key.toLowerCase() === 'r' ? 'reject' : null
}
