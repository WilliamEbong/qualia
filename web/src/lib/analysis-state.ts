import type { components } from '../api/schema'
import type { Workspace } from './entities'

export type AnalysisReport = components['schemas']['AnalysisReport']
export type AnalysisOptions = components['schemas']['AnalysisOptions']
export type AnalysisFormat = components['schemas']['AnalysisExportRequest']['format']
export type AnalysisResult = { report: AnalysisReport; workspace: Workspace; slug: string }
export function currentAnalysis(result: AnalysisResult | null, slug: string, workspace: Workspace | null, view: string): AnalysisReport | null {
  return view === 'analysis' && result?.slug === slug && result.workspace === workspace ? result.report : null
}
export const defaultAnalysisOptions: Required<AnalysisOptions> = {
  source_id: null, case_id: null, code_ids: [], code_match: 'any', query: '', group_by: null,
  cooccurrence: 'segment', numeric_fields: [], min_word_length: 3, stopwords: [], top_words: 30, excerpt_limit: 100,
}

export function isDefaultAnalysisOptions(value: unknown): boolean {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false
  return Object.entries(value).every(([key, item]) => Object.hasOwn(defaultAnalysisOptions, key)
    && JSON.stringify(item) === JSON.stringify(defaultAnalysisOptions[key as keyof AnalysisOptions]))
}

export function analysisOptions(form: FormData): AnalysisOptions {
  return {
    ...defaultAnalysisOptions,
    source_id: Number(form.get('source_id')) || null, case_id: Number(form.get('case_id')) || null,
    code_ids: form.getAll('code_ids').map(Number), code_match: form.get('code_match') === 'all' ? 'all' : 'any',
    query: String(form.get('query') ?? ''), group_by: String(form.get('group_by') ?? '') || null,
    cooccurrence: form.get('cooccurrence') === 'overlap' ? 'overlap' : 'segment',
    numeric_fields: form.getAll('numeric_fields').map(String), min_word_length: Number(form.get('min_word_length')) || 3,
    stopwords: String(form.get('stopwords') ?? '').split(/[\s,]+/u).filter(Boolean), top_words: Number(form.get('top_words')) || 30,
  }
}

export function analysisCriteria(options: AnalysisOptions): string {
  const o = { ...defaultAnalysisOptions, ...options }
  return `Source ${o.source_id ?? 'all'} · case ${o.case_id ?? 'all'} · codes ${o.code_ids.length ? `${o.code_match}: ${o.code_ids.join(', ')}` : 'all'} · query ${o.query ? JSON.stringify(o.query) : 'none'} · group ${o.group_by ?? 'none'} · co-occurrence ${o.cooccurrence} · numeric ${o.numeric_fields.join(', ') || 'none'} · word length ≥${o.min_word_length}, top ${o.top_words}, stopwords ${o.stopwords.join(', ') || 'none'}`
}

export function analysisExcerpts(data: Workspace, report: AnalysisReport, ids: number[]) {
  const requested = new Set(ids), selected = new Set(report.selected_segment_ids), eventIds = new Set(report.coding_event_ids)
  const sources = new Map(data.sources.map(source => [source.id, source.name]))
  const sourceText = new Map(data.sources.map(source => [source.id, Array.from(source.text)]))
  const events = new Map<number, Workspace['coding_events']>()
  for (const event of data.coding_events) {
    if (!eventIds.has(event.id)) continue
    const existing = events.get(event.segment_id) ?? []
    existing.push(event); events.set(event.segment_id, existing)
  }
  return data.segments.filter(segment => requested.has(segment.id) && selected.has(segment.id)).map(segment => ({
    segment_id: segment.id, source_name: sources.get(segment.source_id) ?? `Source ${segment.source_id}`,
    speaker: segment.speaker, text: (sourceText.get(segment.source_id) ?? []).slice(segment.start, segment.end).join(''),
    events: events.get(segment.id) ?? [],
  }))
}

export function scatterPoints(points: { case_id: number; x: number; y: number }[]) {
  if (!points.length) return { points: [], xMin: 0, xMax: 0, yMin: 0, yMax: 0 }
  const xMin = Math.min(...points.map(point => point.x)), xMax = Math.max(...points.map(point => point.x))
  const yMin = Math.min(...points.map(point => point.y)), yMax = Math.max(...points.map(point => point.y))
  return { xMin, xMax, yMin, yMax, points: points.map(point => ({ ...point,
    cx: xMax === xMin ? 320 : 70 + ((point.x - xMin) / (xMax - xMin)) * 500,
    cy: yMax === yMin ? 190 : 320 - ((point.y - yMin) / (yMax - yMin)) * 260,
  })) }
}

export const analysisNumber = (value: number | null | undefined) => value == null || !Number.isFinite(value) ? 'n/a' : Number.isInteger(value) ? String(value) : value.toPrecision(5)
