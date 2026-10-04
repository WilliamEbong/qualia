import type { Workspace } from './entities'
import { segmentText, uniqueSegmentCount } from './entities'

export type DemoSnapshot = { format_version: 1; project: Workspace; attribution: { dataset: string; license: string; sources: string[]; note?: string } }
const arrays = ['sources', 'segments', 'cases', 'attributes', 'source_cases', 'codes', 'codebook_versions', 'coding_events', 'current_codings', 'suggestions', 'memos', 'experiments', 'evaluation_runs'] as const

export function parseSnapshot(value: unknown): DemoSnapshot {
  const snapshot = value as DemoSnapshot
  if (!snapshot || snapshot.format_version !== 1 || !snapshot.project?.project?.slug || !snapshot.project.project.name
    || !arrays.every(key => Array.isArray(snapshot.project[key])) || !snapshot.project.routing || typeof snapshot.project.pipeline_version !== 'string'
    || typeof snapshot.attribution?.dataset !== 'string' || typeof snapshot.attribution.license !== 'string'
    || !Array.isArray(snapshot.attribution.sources) || !snapshot.attribution.sources.every(source => typeof source === 'string')
    || snapshot.project.evaluation_runs.some(run => run.split !== 'validation')) throw new Error('The licensed demo snapshot is missing or invalid.')
  return snapshot
}

export function demoResponse(snapshot: DemoSnapshot, path: string, method = 'GET'): unknown {
  if (method.toUpperCase() !== 'GET') throw new Error('This public demo is read-only. Install Qualia to work with your own project.')
  const [route, query = ''] = path.split('?')
  const parameters = new URLSearchParams(query)
  const data = snapshot.project
  const prefix = `projects/${encodeURIComponent(data.project.slug)}`
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
    if (init?.method && init.method.toUpperCase() !== 'GET') throw new Error('This public demo is read-only.')
    pending ??= load().catch(reason => { pending = undefined; throw reason })
    return demoResponse(await pending, path, init?.method) as T
  }
}
