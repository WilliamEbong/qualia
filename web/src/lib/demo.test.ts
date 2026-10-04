import { describe, expect, it, vi } from 'vitest'
import { createDemoRequester, demoResponse, parseSnapshot } from './demo'
import type { DemoSnapshot } from './demo'
import type { Workspace } from './entities'

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
})
