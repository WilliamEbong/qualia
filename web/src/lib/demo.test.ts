import { describe, expect, it, vi } from 'vitest'
import { createDemoRequester, demoResponse, parseSnapshot } from './demo'
import type { DemoSnapshot } from './demo'
import type { Workspace } from './entities'
import { defaultAnalysisOptions } from './analysis-state'
import { readFileSync } from 'node:fs'

function snapshot(): DemoSnapshot {
  return { format_version: 1, attribution: { dataset: 'Synthetic test fixture', license: 'Test only', sources: [] }, project: {
    project: { slug: 'fixture', name: 'Synthetic fixture' }, pipeline_version: 'test', routing: {},
    sources: [{ id: 1, name: 'Synthetic', text: 'a😀bc', content_hash: 'test', version_of: null }],
    segments: [{ id: 1, source_id: 1, start: 0, end: 4, ordinal: 0, speaker: null }],
    codes: [{ id: 1, name: 'Code' }], cases: [{ id: 1, name: 'Case' }], source_cases: [{ source_id: 1, case_id: 1 }],
    current_codings: [{ id: 1, segment_id: 1, code_id: 1, span_start: 1, span_end: 2 }, { id: 2, segment_id: 1, code_id: 1, span_start: 0, span_end: 4 }],
    attributes: [], codebook_versions: [], coding_events: [], suggestions: [], memos: [], experiments: [], evaluation_runs: [],
  } as unknown as Workspace }
}

function analysisSnapshot(): DemoSnapshot {
  const source = snapshot()
  source.analysis = {
    format_version: 1, options: structuredClone(defaultAnalysisOptions), pipeline_version: 'test', input_hash: 'a'.repeat(64),
    methods: ['Synthetic fixture: precomputed distinct segment counts'], warnings: [], source_count: 1, segment_count: 1,
    case_count: 1, coded_segment_count: 1, selected_segment_ids: [1], coding_event_ids: [], codebook_version_ids: [], codebook_hashes: {},
    frequencies: [], groups: [], pairs: [], words: [], numeric: [], correlations: [], excerpts: [], excerpt_total: 0, case_rows: [],
  }
  source.analysis_exports = {
    json: { filename: 'qualia-analysis.json', media_type: 'application/json', content: '{"synthetic":true}' },
    csv: { filename: 'qualia-analysis.csv', media_type: 'text/csv', content: 'case_id\n1\n' },
    python: { filename: 'qualia-analysis.py', media_type: 'text/x-python', content: '# Synthetic starter\n' },
    r: { filename: 'qualia-analysis.R', media_type: 'text/plain', content: '# Synthetic starter\n' },
  }
  return source
}

describe('strict read-only static data source', () => {
  it('derives distinct-segment matrix and Unicode excerpts without API access', () => {
    const source = snapshot()
    expect(parseSnapshot(source)).toBe(source)
    expect(demoResponse(source, 'projects/fixture/matrix')).toEqual([{ code_id: 1, case_id: 1, count: 1 }])
    const excerpts = demoResponse(source, 'projects/fixture/retrieval?code_id=1&case_id=1') as { excerpt: string }[]
    expect(excerpts.map(item => item.excerpt)).toEqual(['😀', 'a😀bc'])
    expect(demoResponse(source, 'projects/fixture/ai/availability')).toEqual({ allow_external: false, backends: [] })
  })
  it('refuses every write before loading data and does not fake unsupported routes', async () => {
    const loader = vi.fn(async () => snapshot())
    const request = createDemoRequester(loader)
    for (const method of ['POST', 'PUT', 'PATCH', 'DELETE']) await expect(request('projects/fixture/coding', { method })).rejects.toThrow('read-only')
    expect(loader).not.toHaveBeenCalled()
    await expect(request('projects/fixture/classify')).rejects.toThrow('not available')
    await expect(request('projects/other')).rejects.toThrow('not available')
    expect(loader).toHaveBeenCalledTimes(1)
    expect(() => demoResponse(snapshot(), 'projects/fixture/retrieval?unknown=1')).toThrow('Unsupported')
  })
  it('exports only the loaded public snapshot and rejects protected evaluation entries', () => {
    const source = snapshot()
    const exported = demoResponse(source, 'demo/export') as { content: string }
    expect(JSON.parse(exported.content)).toEqual(source)
    source.project.evaluation_runs = [{ split: 'protected' }]
    expect(() => parseSnapshot(source)).toThrow('invalid')
  })
  it('serves cloned precomputed default analysis and all exports without a network request', async () => {
    const source = analysisSnapshot()
    expect(parseSnapshot(source)).toBe(source)
    const loader = vi.fn(async () => source)
    const request = createDemoRequester(loader)
    const report = await request<NonNullable<DemoSnapshot['analysis']>>('projects/fixture/analysis', { method: 'POST', body: JSON.stringify(defaultAnalysisOptions) })
    expect(report).toEqual(source.analysis)
    report.methods.push('Changed by caller')
    expect(source.analysis?.methods).toHaveLength(1)
    expect(await request('projects/fixture/analysis', { method: 'post', body: '{}' })).toEqual(source.analysis)
    for (const format of ['json', 'csv', 'python', 'r'] as const) {
      const exported = await request<{ content: string }>('projects/fixture/analysis/export', { method: 'POST', body: JSON.stringify({ options: {}, format, expected_input_hash: source.analysis!.input_hash }) })
      expect(exported).toEqual(source.analysis_exports?.[format])
      exported.content = 'changed'
      expect(source.analysis_exports?.[format].content).not.toBe('changed')
    }
    expect(loader).toHaveBeenCalledTimes(1)
  })
  it('rejects unsupported methods, routes and options before loading any snapshot', async () => {
    const loader = vi.fn(async () => analysisSnapshot())
    const request = createDemoRequester(loader)
    for (const method of ['PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']) {
      await expect(request('projects/fixture/analysis', { method, body: '{}' })).rejects.toThrow('read-only')
    }
    for (const path of ['projects/fixture/coding', 'projects/fixture/analysis/unknown', 'projects/fixture/analysis?query=', 'projects/fixture/analysis#fragment']) {
      await expect(request(path, { method: 'POST', body: '{}' })).rejects.toThrow('read-only')
    }
    for (const body of ['{"query":"changed"}', '{"unknown":true}', '[]', 'null', '{"numeric_fields":["age"]}', '{"source_id":1}', '{"top_words":"30"}', '{"__proto__":{}}', '{bad']) {
      await expect(request('projects/fixture/analysis', { method: 'POST', body })).rejects.toThrow()
    }
    for (const body of [{ options: { query: 'changed' }, format: 'csv' }, { options: {}, format: 'html' }, { options: {}, format: 'json', unknown: true }, { options: null, format: 'json' }]) {
      await expect(request('projects/fixture/analysis/export', { method: 'POST', body: JSON.stringify(body) })).rejects.toThrow()
    }
    for (const expected_input_hash of [null, 123, '', 'A'.repeat(64), 'x'.repeat(64), 'a'.repeat(63)]) {
      await expect(request('projects/fixture/analysis/export', { method: 'POST', body: JSON.stringify({ format: 'json', expected_input_hash }) })).rejects.toThrow()
    }
    await expect(request('projects/fixture/analysis', { method: 'POST' })).rejects.toThrow()
    expect(loader).not.toHaveBeenCalled()
  })
  it('reports older snapshots and mismatched project slugs without inventing analysis', async () => {
    const request = createDemoRequester(async () => snapshot())
    await expect(request('projects/fixture/analysis', { method: 'POST', body: '{}' })).rejects.toThrow('unavailable')
    await expect(request('projects/fixture/analysis/export', { method: 'POST', body: '{"options":{},"format":"csv"}' })).rejects.toThrow('unavailable')
    await expect(request('projects/other/analysis', { method: 'POST', body: '{}' })).rejects.toThrow('not available')
    await expect(request('projects/fixture/analysis')).rejects.toThrow('not available')
    const current = createDemoRequester(async () => analysisSnapshot())
    await expect(current('projects/fixture/analysis/export', { method: 'POST', body: JSON.stringify({ options: {}, format: 'json', expected_input_hash: 'b'.repeat(64) }) })).rejects.toThrow('Refresh analysis')
    expect(await current('projects/fixture/analysis/export', { method: 'POST', body: '{"options":{},"format":"json"}' })).toEqual(analysisSnapshot().analysis_exports!.json)
  })
  it('rejects invalid report format, provenance, options and export types', () => {
    const invalid = (edit: (source: DemoSnapshot) => void) => { const source = analysisSnapshot(); edit(source); expect(() => parseSnapshot(source)).toThrow('invalid') }
    invalid(source => { source.analysis!.pipeline_version = 'other' })
    invalid(source => { source.analysis!.input_hash = 'not a digest' })
    invalid(source => { source.analysis!.options.query = 'nondefault' })
    invalid(source => { source.analysis!.selected_segment_ids = [99] })
    invalid(source => { source.analysis!.coding_event_ids = [99] })
    invalid(source => { source.analysis!.codebook_hashes = { '99': 'a'.repeat(64) } })
    invalid(source => { source.analysis!.segment_count = -1 })
    invalid(source => { source.analysis!.format_version = 2 as 1 })
    invalid(source => { source.analysis_exports!.json.media_type = 'text/html' })
    invalid(source => { source.analysis_exports!.json.filename = '../private.json' })
    invalid(source => { delete source.analysis })
  })
  it('accepts the approved generated public snapshot and its precomputed exports', () => {
    const publicSnapshot = parseSnapshot(JSON.parse(readFileSync(new URL('../../../demo/snapshot.json', import.meta.url), 'utf8')))
    expect(publicSnapshot.analysis?.segment_count).toBeGreaterThan(0)
    expect(demoResponse(publicSnapshot, `projects/${publicSnapshot.project.project.slug}/analysis`, 'POST', {})).toEqual(publicSnapshot.analysis)
    expect(Object.keys(publicSnapshot.analysis_exports ?? {})).toEqual(['csv', 'json', 'python', 'r'])
  })
})
