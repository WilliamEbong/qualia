import type { components } from '../api/schema'

export type Project = components['schemas']['ProjectSummary']
export type Source = { id: number; name: string; text: string; content_hash: string; version_of: number | null }
export type Segment = { id: number; source_id: number; start: number; end: number; ordinal: number; speaker: string | null }
export type Code = { id: number; parent_id: number | null; name: string; status: 'active' | 'archived'; definition: string; include: string; exclude: string; examples_pos: string; examples_neg: string }
export type Version = { id: number; hash: string; frozen_at: string; snapshot_json: string }
export type Coding = { id: number; segment_id: number; code_id: number; span_start: number; span_end: number; action: string; actor_type: string; actor: string; backend: string | null; model: string | null; model_version?: string | null; cli_version: string | null; codebook_version_id: number; pipeline_version: string; prompt_hash: string; created_at: string; score: number | null; reviewed_by: string | null; rationale: string | null; review_trigger: string | null; suggestion_id: number | null; review_status: string }
export type MemoKind = 'analytic' | 'reflexive' | 'theme' | 'method'
export type Memo = { id: number; title: string; text: string; kind?: MemoKind; segment_id: number | null; code_id: number | null; case_id?: number | null; source_id?: number | null; created_at?: string; author?: string | null }
export type MemoRevision = { id: number; memo_id: number; title: string; text: string; kind: MemoKind; replaced_at: string }
export type Case = { id: number; name: string }
export type Attribute = { id: number; case_id: number | null; source_id: number | null; key: string; value: string }
export type SourceCase = { source_id: number; case_id: number }
export type Proposal = { id: number; batch_id: string; mode: 'draft' | 'refine' | 'evidence'; kind: 'new_code' | 'revise_code'; target_code_id: number | null; payload_json: string; rationale: string; evidence_json: string; actor_type: 'model' | 'rule'; backend: string | null; model: string | null; model_version?: string | null; cli_version: string | null; prompt_hash: string; codebook_version_id: number | null; created_at: string; decision: 'accept' | 'reject' | null; decided_by: string | null; decision_note: string | null; applied_json: string | null; resulting_code_id: number | null; decided_at: string | null }
// code_proposals is optional: older public demo snapshots predate codebook proposals.
export type Workspace = Omit<components['schemas']['Workspace'], 'sources' | 'segments' | 'codes' | 'codebook_versions' | 'coding_events' | 'current_codings' | 'suggestions' | 'memos' | 'cases' | 'attributes' | 'source_cases' | 'code_proposals' | 'memo_revisions' | 'current_coding_ids'> & {
  sources: Source[]; segments: Segment[]; codes: Code[]; codebook_versions: Version[];
  coding_events: Coding[]; current_codings: Coding[]; suggestions: Coding[]; memos: Memo[]; cases: Case[];
  attributes: Attribute[]; source_cases: SourceCase[]; code_proposals?: Proposal[]; memo_revisions?: MemoRevision[];
}
export type Span = { segmentId: number; start: number; end: number }
export type MatrixCell = { code_id: number; case_id: number; count: number }
export type Retrieval = Coding & { source_id: number; segment_text: string; excerpt: string; source_name: string }
export type View = 'home' | 'workspace' | 'codebook' | 'memos' | 'retrieval' | 'matrix' | 'review' | 'evaluation' | 'experiments' | 'analysis'

const codePoints = new WeakMap<Source, string[]>()
export const counted = (count: number, noun: string, plural = `${noun}s`) => `${count} ${count === 1 ? noun : plural}`

export function sourceCodePoints(source: Source): string[] {
  let points = codePoints.get(source)
  if (!points) { points = Array.from(source.text); codePoints.set(source, points) }
  return points
}

/** The API sends current coding as event IDs; static demo snapshots embed the rows themselves. */
export function hydrateWorkspace(value: Workspace & { current_coding_ids?: number[] }): Workspace {
  if (!Array.isArray(value.current_coding_ids) || value.current_codings?.length) return value
  const events = new Map(value.coding_events.map(event => [event.id, event]))
  return { ...value, current_codings: value.current_coding_ids.flatMap(id => events.get(id) ?? []) }
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

// Home's study status: what the project holds, and the single next step that moves it forward.
export function studyStatus(data: Pick<Workspace, 'sources' | 'segments' | 'codes' | 'codebook_versions' | 'current_codings' | 'suggestions'>) {
  const coded = new Set(data.current_codings.map(item => item.segment_id)).size
  const latest = data.codebook_versions[data.codebook_versions.length - 1]
  const pending = data.suggestions.length
  const next: { label: string; view: View; panel?: 'import' } =
    !data.sources.length ? { label: 'Import your first source', view: 'workspace', panel: 'import' }
    : !data.codes.length ? { label: 'Create your first codes', view: 'codebook' }
    : !latest ? { label: 'Freeze the codebook', view: 'codebook' }
    : !coded ? { label: 'Code a passage', view: 'workspace' }
    : pending ? { label: `Review ${counted(pending, 'pending suggestion')}`, view: 'review' }
    : { label: 'Explore the analysis', view: 'analysis' }
  return { sources: data.sources.length, passages: data.segments.length, coded, pending,
    latestVersion: latest ? `cb_v${latest.id} · ${String(latest.frozen_at).slice(0, 10)}` : null, next }
}

// Retrieval: excerpts grouped under their code, in codebook order.
export function groupByCode<T extends { code_id: number }>(items: T[], codeOrder: number[], nameOf: (id: number) => string) {
  const ids = [...new Set(items.map(item => item.code_id))].sort((a, b) => (codeOrder.indexOf(a) + 1 || Infinity) - (codeOrder.indexOf(b) + 1 || Infinity))
  return ids.map(id => ({ codeId: id, name: nameOf(id), items: items.filter(item => item.code_id === id) }))
}

// One caption per memo card: kind, created date, author when recorded, and the last edit.
export function memoMeta(memo: Pick<Memo, 'kind' | 'created_at' | 'author'>, revisions: Array<{ replaced_at?: string }>) {
  const day = (value?: string) => (value ?? '').slice(0, 10)
  const edited = revisions.map(item => item.replaced_at ?? '').sort().at(-1)
  return [`${memo.kind ?? 'analytic'} memo`, day(memo.created_at), memo.author, edited ? `edited ${day(edited)}` : ''].filter(Boolean).join(' · ')
}

// Totals use the cells' definition: distinct currently coded segments whose source is linked to a case.
export function matrixTotals(data: { segments: Array<{ id: number; source_id: number }>; source_cases: Array<{ source_id: number; case_id: number }>; current_codings: Array<{ segment_id: number; code_id: number }> }) {
  const sourceOf = new Map(data.segments.map(segment => [segment.id, segment.source_id]))
  const casesOf = new Map<number, number[]>()
  for (const link of data.source_cases) casesOf.set(link.source_id, [...(casesOf.get(link.source_id) ?? []), link.case_id])
  const byCode = new Map<number, Set<number>>(), byCase = new Map<number, Set<number>>(), all = new Set<number>()
  for (const coding of data.current_codings) {
    const cases = casesOf.get(sourceOf.get(coding.segment_id) ?? -1) ?? []
    if (!cases.length) continue
    all.add(coding.segment_id)
    byCode.set(coding.code_id, (byCode.get(coding.code_id) ?? new Set()).add(coding.segment_id))
    for (const case_ of cases) byCase.set(case_, (byCase.get(case_) ?? new Set()).add(coding.segment_id))
  }
  const sizes = (map: Map<number, Set<number>>) => Object.fromEntries([...map].map(([key, value]) => [key, value.size]))
  return { byCode: sizes(byCode), byCase: sizes(byCase), all: all.size }
}

const CODE_FIELDS = ['parent_id', 'name', 'status', 'definition', 'include', 'exclude', 'examples_pos', 'examples_neg'] as const
const frozenCodesOf = (latest: Version | undefined): Code[] | null => { try { return latest ? JSON.parse(latest.snapshot_json) : null } catch { return null } }

// Draft codes that are new or edited since the latest frozen version.
export function changedCodeIds(codes: Code[], latest: Version | undefined): Set<number> {
  const frozen = frozenCodesOf(latest)
  if (!frozen) return new Set(codes.map(code => code.id))
  const before = new Map(frozen.map(code => [code.id, code]))
  return new Set(codes.filter(code => { const old = before.get(code.id); return !old || CODE_FIELDS.some(field => String(old[field] ?? '') !== String(code[field] ?? '')) }).map(code => code.id))
}

// How many codes differ between the draft and the latest frozen version (added, edited or removed).
export function draftChanges(codes: Code[], latest: Version | undefined): number {
  const frozen = frozenCodesOf(latest)
  if (!frozen) return codes.length
  return changedCodeIds(codes, latest).size + frozen.filter(code => !codes.some(item => item.id === code.id)).length
}

// A suggestion for a code already applied to the passage, from the same frozen version (so the same
// name and definition), sits under that code's first mark instead of repeating it; others stay separate.
export function splitSuggestions(applied: Coding[], suggestions: Coding[]) {
  const key = (item: Coding) => `${item.code_id}:${item.codebook_version_id}`
  const first = new Map<string, number>()
  for (const item of applied) if (!first.has(key(item))) first.set(key(item), item.id)
  return {
    agreeing: (coding: Coding) => first.get(key(coding)) === coding.id ? suggestions.filter(item => key(item) === key(coding)) : [],
    separate: suggestions.filter(item => !first.has(key(item))),
  }
}
