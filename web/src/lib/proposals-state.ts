import type { Code, Proposal, Segment } from './entities'
import { exampleList } from './entities'

export type ProposalValues = { name: string; parent_id: number | null; status: 'active' | 'archived'; definition: string; include: string; exclude: string; examples_pos: string[]; examples_neg: string[] }
export type ProposalEvidence = { signal?: 'rejections' | 'unused' | 'overlap'; segment_ids?: number[]; excerpts?: string[]; notes?: string[]; focus?: string; jaccard?: number; coded_segments?: number }
export type ProposalChange = { field: keyof ProposalValues; label: string; before: string; after: string }
export type ProposalView = Proposal & { values: ProposalValues; evidence: ProposalEvidence; changes: ProposalChange[]; title: string; origin: string }

const labels: Record<keyof ProposalValues, string> = { name: 'Name', parent_id: 'Parent code', status: 'Status', definition: 'Definition', include: 'Include', exclude: 'Exclude', examples_pos: 'Positive examples', examples_neg: 'Negative examples' }
const signals = { rejections: 'rejected AI suggestions', unused: 'an unused code', overlap: 'overlapping codes' }

function parse<T>(value: string | null, fallback: T): T {
  try { return value ? JSON.parse(value) as T : fallback } catch { return fallback }
}

export function codeValues(code: Code): ProposalValues {
  return { name: code.name, parent_id: code.parent_id, status: code.status, definition: code.definition, include: code.include, exclude: code.exclude, examples_pos: exampleList(code.examples_pos), examples_neg: exampleList(code.examples_neg) }
}

export function proposalView(proposal: Proposal, codes: Code[]): ProposalView {
  const values: ProposalValues = { name: '', parent_id: null, status: 'active', definition: '', include: '', exclude: '', examples_pos: [], examples_neg: [], ...parse<Partial<ProposalValues>>(proposal.payload_json, {}) }
  const target = codes.find(code => code.id === proposal.target_code_id)
  const before = target ? codeValues(target) : null
  const show = (field: keyof ProposalValues, value: ProposalValues[keyof ProposalValues]) => field === 'parent_id'
    ? value === null ? 'No parent' : codes.find(code => code.id === value)?.name ?? `Code ${value}`
    : Array.isArray(value) ? value.join('\n') : String(value ?? '')
  const fields = Object.keys(labels) as (keyof ProposalValues)[]
  const changes = fields.filter(field => before ? show(field, before[field]) !== show(field, values[field])
    : !['parent_id', 'status'].includes(field) && show(field, values[field]) !== '')
    .map(field => ({ field, label: labels[field], before: before ? show(field, before[field]) : '', after: show(field, values[field]) }))
  const evidence = parse<ProposalEvidence>(proposal.evidence_json, {})
  return { ...proposal, values, evidence, changes,
    title: proposal.kind === 'new_code' ? `New code “${values.name}”` : `Revise “${target?.name ?? `code ${proposal.target_code_id}`}”`,
    origin: proposal.actor_type === 'rule' ? `evidence from ${signals[evidence.signal ?? 'rejections']} · offline` : `model-proposed · ${proposal.backend} / ${proposal.model} · ${proposal.mode}` }
}

/** The latest accepted proposal that created or revised each code. */
export function acceptedProposals(proposals: Proposal[]): Map<number, Proposal> {
  const result = new Map<number, Proposal>()
  for (const proposal of proposals) if (proposal.decision === 'accept' && proposal.resulting_code_id !== null) result.set(proposal.resulting_code_id, proposal)
  return result
}

export function originCaption(proposal: Proposal | undefined): string {
  if (!proposal) return ''
  const who = proposal.actor_type === 'model' ? `model-proposed (${proposal.backend})` : 'evidence-based'
  return `${proposal.kind === 'new_code' ? 'created from' : 'revised from'} ${who} proposal #${proposal.id} · accepted by ${proposal.decided_by}`
}

/** The first `count` segments of a source in reading order: the passages sent for drafting. */
export function draftSegmentIds(segments: Segment[], sourceId: number | null, count: number): number[] {
  return segments.filter(segment => segment.source_id === sourceId).sort((a, b) => a.ordinal - b.ordinal).slice(0, Math.max(0, Math.min(20, count))).map(segment => segment.id)
}
