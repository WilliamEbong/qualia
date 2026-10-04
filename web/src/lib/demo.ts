import type { Workspace } from './entities'
import { segmentText, uniqueSegmentCount } from './entities'
import type { components } from '../api/schema'
import { defaultAnalysisOptions, isDefaultAnalysisOptions } from './analysis-state'
import type { AnalysisFormat, AnalysisReport } from './analysis-state'

type ExportResult = components['schemas']['ExportResult']
export type DemoSnapshot = { format_version: 1; project: Workspace; attribution: { dataset: string; license: string; sources: string[]; note?: string }; analysis?: AnalysisReport; analysis_exports?: Record<AnalysisFormat, ExportResult> }
const arrays = ['sources', 'segments', 'cases', 'attributes', 'source_cases', 'codes', 'codebook_versions', 'coding_events', 'current_codings', 'suggestions', 'memos', 'experiments', 'evaluation_runs'] as const
const formats = ['json', 'csv', 'python', 'r'] as const
const mediaTypes = { json: 'application/json', csv: 'text/csv', python: 'text/x-python', r: 'text/plain' }
const record = (value: unknown): value is Record<string, unknown> => value !== null && typeof value === 'object' && !Array.isArray(value)
const ids = (value: unknown): value is number[] => Array.isArray(value) && value.every(id => Number.isSafeInteger(id) && id > 0) && new Set(value).size === value.length

function validAnalysis(report: AnalysisReport, data: Workspace): boolean {
  return record(report) && report.format_version === 1 && isDefaultAnalysisOptions(report.options)
    && report.pipeline_version === data.pipeline_version && typeof report.input_hash === 'string' && /^[a-f0-9]{64}$/.test(report.input_hash)
    && ['source_count', 'segment_count', 'case_count', 'coded_segment_count', 'excerpt_total'].every(key => Number.isSafeInteger(report[key as keyof AnalysisReport]) && Number(report[key as keyof AnalysisReport]) >= 0)
    && ['frequencies', 'groups', 'pairs', 'words', 'numeric', 'correlations', 'excerpts', 'case_rows'].every(key => Array.isArray(report[key as keyof AnalysisReport]) && (report[key as keyof AnalysisReport] as unknown[]).every(record))
    && [report.methods, report.warnings].every(values => Array.isArray(values) && values.every(value => typeof value === 'string'))
    && ids(report.selected_segment_ids) && report.selected_segment_ids.every(id => data.segments.some(segment => segment.id === id))
    && report.segment_count === report.selected_segment_ids.length
    && report.source_count <= data.sources.length && report.case_count <= data.cases.length && report.coded_segment_count <= report.segment_count
    && ids(report.coding_event_ids) && report.coding_event_ids.every(id => data.coding_events.some(event => event.id === id))
    && ids(report.codebook_version_ids) && report.codebook_version_ids.every(id => data.codebook_versions.some(version => version.id === id))
    && record(report.codebook_hashes) && Object.keys(report.codebook_hashes).length === report.codebook_version_ids.length
    && report.codebook_version_ids.every(id => report.codebook_hashes[String(id)] === data.codebook_versions.find(version => version.id === id)?.hash)
}

function validExports(value: unknown): boolean {
  return record(value) && Object.keys(value).length === formats.length && formats.every(format => {
    const item = value[format]
    return record(item) && typeof item.filename === 'string' && /^[a-zA-Z0-9_.-]+$/.test(item.filename)
      && item.media_type === mediaTypes[format] && typeof item.content === 'string'
  })
}

function analysisRequest(path: string, method: string, body?: unknown): { exportFormat?: AnalysisFormat; expectedInputHash?: string } | undefined {
  if (method === 'GET') return undefined
  if (method !== 'POST' || !/^projects\/[^/?#]+\/analysis(?:\/export)?$/.test(path)) throw new Error('This public demo is read-only.')
  if (path.endsWith('/export')) {
    if (!record(body) || Object.keys(body).some(key => !['options', 'format', 'expected_input_hash'].includes(key))
      || (body.expected_input_hash !== undefined && (typeof body.expected_input_hash !== 'string' || !/^[a-f0-9]{64}$/.test(body.expected_input_hash)))
      || !formats.includes(body.format as AnalysisFormat) || !isDefaultAnalysisOptions(body.options === undefined ? defaultAnalysisOptions : body.options)) throw new Error('Only default analysis options are available in the read-only demo.')
    return { exportFormat: body.format as AnalysisFormat, expectedInputHash: body.expected_input_hash as string | undefined }
  }
  if (!isDefaultAnalysisOptions(body)) throw new Error('Only default analysis options are available in the read-only demo.')
  return {}
}

export function parseSnapshot(value: unknown): DemoSnapshot {
  const snapshot = value as DemoSnapshot
  if (!snapshot || snapshot.format_version !== 1 || !snapshot.project?.project?.slug || !snapshot.project.project.name
    || !arrays.every(key => Array.isArray(snapshot.project[key])) || !snapshot.project.routing || typeof snapshot.project.pipeline_version !== 'string'
    || typeof snapshot.attribution?.dataset !== 'string' || typeof snapshot.attribution.license !== 'string'
    || !Array.isArray(snapshot.attribution.sources) || !snapshot.attribution.sources.every(source => typeof source === 'string')
    || snapshot.project.evaluation_runs.some(run => run.split !== 'validation')
    || (snapshot.analysis !== undefined && !validAnalysis(snapshot.analysis, snapshot.project))
    || (snapshot.analysis_exports !== undefined && (!snapshot.analysis || !validExports(snapshot.analysis_exports)))) throw new Error('The licensed demo snapshot is missing or invalid.')
  return snapshot
}

export function demoResponse(snapshot: DemoSnapshot, path: string, method = 'GET', body?: unknown): unknown {
  const analysis = analysisRequest(path, method.toUpperCase(), body)
  const [route, query = ''] = path.split('?')
  const parameters = new URLSearchParams(query)
  const data = snapshot.project
  const prefix = `projects/${encodeURIComponent(data.project.slug)}`
  if (analysis) {
    if (route !== `${prefix}/analysis${analysis.exportFormat ? '/export' : ''}`) throw new Error('This project is not available in the read-only demo.')
    const result = analysis.exportFormat ? snapshot.analysis_exports?.[analysis.exportFormat] : snapshot.analysis
    if (!result) throw new Error('Analysis is unavailable in this demo snapshot. Install Qualia to analyze your project.')
    if (analysis.expectedInputHash !== undefined && analysis.expectedInputHash !== snapshot.analysis?.input_hash) throw new Error('Analysis inputs changed. Refresh analysis before exporting.')
    return structuredClone(result)
  }
  if (route === 'projects' && !query) return [data.project]
  if (route === 'demo/attribution' && !query) return snapshot.attribution
  if (route === 'demo/export' && !query) return { filename: 'qualia-public-snapshot.json', media_type: 'application/json', content: JSON.stringify(snapshot) }
  if (route === prefix && !query) return structuredClone(data)
  if (route === `${prefix}/ai/availability` && !query) return { allow_external: false, backends: [] }
  if (route === `${prefix}/matrix` && !query) return data.codes.flatMap(code => data.cases.flatMap(case_ => {
    const sources = new Set(data.source_cases.filter(link => link.case_id === case_.id).map(link => link.source_id))
    const count = uniqueSegmentCount(data.current_codings, code.id, sources, data.segments)
    return count ? [{ code_id: code.id, case_id: case_.id, count }] : []
  }))
  if (route === `${prefix}/retrieval`) {
    if ([...parameters.keys()].some(key => !['code_id', 'case_id'].includes(key))) throw new Error('Unsupported demo retrieval query.')
    const filter = (key: string) => {
      const value = parameters.get(key)
      if (value !== null && !/^[1-9]\d*$/.test(value)) throw new Error('Invalid demo retrieval filter.')
      return value === null ? null : Number(value)
    }
    const codeId = filter('code_id'), caseId = filter('case_id')
    return data.current_codings.flatMap(coding => {
      const segment = data.segments.find(item => item.id === coding.segment_id)
      const source = data.sources.find(item => item.id === segment?.source_id)
      if (!segment || !source || (codeId !== null && coding.code_id !== codeId)
        || (caseId !== null && !data.source_cases.some(link => link.source_id === source.id && link.case_id === caseId))) return []
      const text = segmentText(data, segment)
      return [{ ...coding, source_id: source.id, source_name: source.name, segment_start: segment.start, segment_end: segment.end,
        segment_text: text, excerpt: Array.from(text).slice(coding.span_start, coding.span_end).join('') }]
    })
  }
  throw new Error(`This route is not available in the read-only demo: ${route}`)
}

export function createDemoRequester(load: () => Promise<DemoSnapshot>) {
  let pending: Promise<DemoSnapshot> | undefined
  return async <T,>(path: string, init?: RequestInit): Promise<T> => {
    const method = (init?.method ?? 'GET').toUpperCase()
    let body: unknown
    if (method === 'POST' && /^projects\/[^/?#]+\/analysis(?:\/export)?$/.test(path)) {
      if (typeof init?.body !== 'string') throw new Error('Only JSON default analysis options are available in the read-only demo.')
      try { body = JSON.parse(init.body) } catch { throw new Error('Invalid demo analysis options.') }
    }
    analysisRequest(path, method, body)
    pending ??= load().catch(reason => { pending = undefined; throw reason })
    return demoResponse(await pending, path, method, body) as T
  }
}
