import type { components } from '../api/schema'

export type Project = components['schemas']['ProjectSummary']
export type Source = { id: number; name: string; text: string; content_hash: string; version_of: number | null }
export type Segment = { id: number; source_id: number; start: number; end: number; ordinal: number; speaker: string | null }
export type Code = { id: number; parent_id: number | null; name: string; status: 'active' | 'archived'; definition: string; include: string; exclude: string; examples_pos: string; examples_neg: string }
export type Version = { id: number; hash: string; frozen_at: string; snapshot_json: string }
export type Coding = { id: number; segment_id: number; code_id: number; span_start: number; span_end: number; action: string; actor_type: string; actor: string; backend: string | null; model: string | null; cli_version: string | null; codebook_version_id: number; pipeline_version: string; prompt_hash: string; created_at: string; score: number | null; reviewed_by: string | null; rationale: string | null; review_trigger: string | null; suggestion_id: number | null; review_status: string }
export type Memo = { id: number; title: string; text: string; segment_id: number | null; code_id: number | null }
export type Case = { id: number; name: string }
export type Attribute = { id: number; case_id: number | null; source_id: number | null; key: string; value: string }
export type SourceCase = { source_id: number; case_id: number }
export type Proposal = { id: number; batch_id: string; mode: 'draft' | 'refine' | 'evidence'; kind: 'new_code' | 'revise_code'; target_code_id: number | null; payload_json: string; rationale: string; evidence_json: string; actor_type: 'model' | 'rule'; backend: string | null; model: string | null; cli_version: string | null; prompt_hash: string; codebook_version_id: number | null; created_at: string; decision: 'accept' | 'reject' | null; decided_by: string | null; decision_note: string | null; applied_json: string | null; resulting_code_id: number | null; decided_at: string | null }
// code_proposals is optional: older public demo snapshots predate codebook proposals.
export type Workspace = Omit<components['schemas']['Workspace'], 'sources' | 'segments' | 'codes' | 'codebook_versions' | 'coding_events' | 'current_codings' | 'suggestions' | 'memos' | 'cases' | 'attributes' | 'source_cases' | 'code_proposals'> & {
  sources: Source[]; segments: Segment[]; codes: Code[]; codebook_versions: Version[];
  coding_events: Coding[]; current_codings: Coding[]; suggestions: Coding[]; memos: Memo[]; cases: Case[];
  attributes: Attribute[]; source_cases: SourceCase[]; code_proposals?: Proposal[];
}
export type Span = { segmentId: number; start: number; end: number }
export type MatrixCell = { code_id: number; case_id: number; count: number }
export type Retrieval = Coding & { source_id: number; segment_text: string; excerpt: string; source_name: string }
export type View = 'home' | 'workspace' | 'codebook' | 'memos' | 'retrieval' | 'matrix' | 'review' | 'evaluation' | 'experiments' | 'analysis'

const codePoints = new WeakMap<Source, string[]>()
export function sourceCodePoints(source: Source): string[] {
  let points = codePoints.get(source)
  if (!points) { points = Array.from(source.text); codePoints.set(source, points) }
  return points
}

export function segmentText(data: Workspace, segment: Segment): string {
  const source = data.sources.find(item => item.id === segment.source_id)
  return source ? sourceCodePoints(source).slice(segment.start, segment.end).join('') : ''
}

// Examples arrive as JSON text from the API and as arrays in the public demo snapshot.
export function exampleList(value: unknown): string[] {
  if (Array.isArray(value)) return value.map(String)
  if (typeof value !== 'string') return []
  try { const parsed: unknown = JSON.parse(value); return Array.isArray(parsed) ? parsed.map(String) : [] } catch { return [] }
}

export function descendantIds(codeId: number, codes: Code[]): Set<number> {
  const found = new Set<number>([codeId])
  for (let grew = true; grew;) {
    grew = false
    for (const code of codes) if (code.parent_id !== null && found.has(code.parent_id) && !found.has(code.id)) { found.add(code.id); grew = true }
  }
  return found
}

export function codeDepth(code: Code, codes: Code[]): number {
  const visited = new Set<number>([code.id])
  let parent = code.parent_id
  let depth = 0
  while (parent !== null && !visited.has(parent)) {
    visited.add(parent)
    depth++
    parent = codes.find(item => item.id === parent)?.parent_id ?? null
  }
  return depth
}

export function orderedCodes(codes: Code[]): Code[] {
  const result: Code[] = []
  const seen = new Set<number>()
  function visit(parent: number | null) {
    for (const code of codes.filter(item => item.parent_id === parent)) {
      if (seen.has(code.id)) continue
      seen.add(code.id); result.push(code); visit(code.id)
    }
  }
  visit(null)
  return [...result, ...codes.filter(item => !seen.has(item.id))]
}

export function frozenCodes(version: Version | undefined): Code[] {
  if (!version) return []
  try { const parsed: unknown = JSON.parse(version.snapshot_json); return Array.isArray(parsed) ? parsed as Code[] : [] } catch { return [] }
}

export function eventCodeName(event: Pick<Coding, 'code_id' | 'codebook_version_id'>, versions: Version[]): string {
  const version = versions.find(item => item.id === event.codebook_version_id)
  return frozenCodes(version).find(code => code.id === event.code_id)?.name ?? `Code ${event.code_id} (version ${event.codebook_version_id})`
}

export function isEditingTarget(target: EventTarget | null): boolean {
  return target instanceof HTMLElement && !!target.closest('input,textarea,select,[contenteditable="true"],[role="textbox"]')
}

export function shortcut(key: string, index: number, length: number): { index?: number; codeIndex?: number } {
  if (key === 'ArrowDown') return { index: Math.min(length - 1, index + 1) }
  if (key === 'ArrowUp') return { index: Math.max(0, index - 1) }
  if (/^[1-9]$/.test(key)) return { codeIndex: Number(key) - 1 }
  return {}
}

export function uniqueSegmentCount(codings: Coding[], codeId: number, sourceIds: Set<number>, segments: Segment[]): number {
  const valid = new Set(segments.filter(segment => sourceIds.has(segment.source_id)).map(segment => segment.id))
  return new Set(codings.filter(item => item.code_id === codeId && valid.has(item.segment_id)).map(item => item.segment_id)).size
}

export const codeStyle = (index: number) => ({ '--code-color': `var(--code-${index % 8 + 1})`, '--code-border': 'solid', '--code-pattern': index >= 8 ? 'var(--code-hatch)' : 'none' })
