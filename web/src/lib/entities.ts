import type { components } from '../api/schema'

export type Project = components['schemas']['ProjectSummary']
export type Source = { id: number; name: string; text: string; content_hash: string; version_of: number | null }
export type Segment = { id: number; source_id: number; start: number; end: number; ordinal: number; speaker: string | null }
export type Code = { id: number; parent_id: number | null; name: string; status: 'active' | 'archived'; definition: string; include: string; exclude: string; examples_pos: string; examples_neg: string }
export type Version = { id: number; hash: string; frozen_at: string; snapshot_json: string }
export type Coding = { id: number; segment_id: number; code_id: number; span_start: number; span_end: number; action: string; actor_type: string; actor: string; backend: string | null; model: string | null; cli_version: string | null; codebook_version_id: number; pipeline_version: string; prompt_hash: string; created_at: string; score: number | null; reviewed_by: string | null }
export type Memo = { id: number; title: string; text: string; segment_id: number | null; code_id: number | null }
export type Case = { id: number; name: string }
export type Attribute = { id: number; case_id: number | null; source_id: number | null; key: string; value: string }
export type SourceCase = { source_id: number; case_id: number }
export type Workspace = Omit<components['schemas']['Workspace'], 'sources' | 'segments' | 'codes' | 'codebook_versions' | 'coding_events' | 'current_codings' | 'memos' | 'cases' | 'attributes' | 'source_cases'> & {
  sources: Source[]; segments: Segment[]; codes: Code[]; codebook_versions: Version[];
  coding_events: Coding[]; current_codings: Coding[]; memos: Memo[]; cases: Case[];
  attributes: Attribute[]; source_cases: SourceCase[];
}
export type Span = { segmentId: number; start: number; end: number }
export type MatrixCell = { code_id: number; case_id: number; count: number }
export type Retrieval = Coding & { source_id: number; segment_text: string; excerpt: string; source_name: string }
export type View = 'workspace' | 'codebook' | 'memos' | 'retrieval' | 'matrix'

export function segmentText(data: Workspace, segment: Segment): string {
  const source = data.sources.find(item => item.id === segment.source_id)
  return Array.from(source?.text ?? '').slice(segment.start, segment.end).join('')
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

export const codeStyle = (index: number) => ({ '--code-color': `var(--code-${index % 8 + 1})`, '--code-border': index >= 8 ? 'dashed' : 'solid' })
