import { describe, expect, it } from 'vitest'
import { analysisCriteria, analysisExcerpts, analysisNumber, analysisOptions, currentAnalysis, defaultAnalysisOptions, isDefaultAnalysisOptions, scatterPoints } from './analysis-state'
import type { AnalysisReport } from './analysis-state'
import type { Workspace } from './entities'

describe('analysis input and linked evidence', () => {
  it('hides a previous report before it can mix with changed workspace evidence or another view', () => {
    const workspace = { current_codings: [{ id: 1 }], attributes: [] } as unknown as Workspace
    const report = { options: { ...defaultAnalysisOptions, query: 'applied', numeric_fields: ['age'] } } as AnalysisReport
    const result = { report, workspace, slug: 'study' }
    expect(currentAnalysis(result, 'study', workspace, 'analysis')).toBe(report)
    expect(currentAnalysis(result, 'study', { ...workspace, current_codings: [] }, 'analysis')).toBeNull()
    expect(currentAnalysis(result, 'study', { ...workspace, attributes: [] }, 'analysis')).toBeNull()
    expect(currentAnalysis(result, 'other', workspace, 'analysis')).toBeNull()
    expect(currentAnalysis(result, 'study', workspace, 'workspace')).toBeNull()
    expect(currentAnalysis(result, 'study', null, 'analysis')).toBeNull()
    expect(report.options).toMatchObject({ query: 'applied', numeric_fields: ['age'] })
  })
  it('requires explicit numeric fields and preserves literal query semantics', () => {
    const form = new FormData()
    form.set('query', '  literal [x]  '); form.set('case_id', '7'); form.append('code_ids', '3'); form.append('code_ids', '8')
    form.set('code_match', 'all'); form.set('stopwords', 'the, and\nwith')
    const input = analysisOptions(form)
    expect(input.numeric_fields).toEqual([])
    expect(input.query).toBe('  literal [x]  ')
    expect(input).toMatchObject({ case_id: 7, source_id: null, code_ids: [3, 8], code_match: 'all', stopwords: ['the', 'and', 'with'] })
    form.append('numeric_fields', 'age')
    expect(analysisOptions(form).numeric_fields).toEqual(['age'])
    expect(analysisCriteria(input)).toContain('all: 3, 8')
  })
  it('allows only semantically default public options with no unknown fields', () => {
    expect(isDefaultAnalysisOptions({})).toBe(true)
    expect(isDefaultAnalysisOptions({ ...defaultAnalysisOptions })).toBe(true)
    for (const input of [null, [], { source_id: '1' }, { query: ' ' }, { numeric_fields: ['id'] }, { top_words: 31 }, { protected: true }, { code_ids: null }]) expect(isDefaultAnalysisOptions(input)).toBe(false)
  })
  it('drills beyond the embedded excerpt limit and includes only report event IDs', () => {
    const data = { sources: [{ id: 1, name: 'Synthetic', text: 'a😀b' }],
      segments: Array.from({ length: 105 }, (_, index) => ({ id: index + 1, source_id: 1, start: 1, end: 2, speaker: null })),
      coding_events: [{ id: 1, segment_id: 105, action: 'assign' }, { id: 2, segment_id: 105, action: 'suggest' }, { id: 3, segment_id: 105, action: 'remove' }],
    } as unknown as Workspace
    const report = { selected_segment_ids: [104, 105], coding_event_ids: [1], excerpts: [] } as unknown as AnalysisReport
    const evidence = analysisExcerpts(data, report, [1, 105, 105])
    expect(evidence).toHaveLength(1)
    expect(evidence[0]).toMatchObject({ segment_id: 105, text: '😀', source_name: 'Synthetic' })
    expect(evidence[0].events.map(event => event.id)).toEqual([1])
  })
  it('positions constant-field and empty scatter data without NaN and leaves null metrics honest', () => {
    expect(scatterPoints([]).points).toEqual([])
    const result = scatterPoints([{ case_id: 1, x: 5, y: 8 }, { case_id: 2, x: 5, y: 9 }])
    expect(result.points.map(point => point.cx)).toEqual([320, 320])
    expect(result.points.map(point => point.cy)).toEqual([320, 60])
    expect(analysisNumber(null)).toBe('n/a'); expect(analysisNumber(NaN)).toBe('n/a'); expect(analysisNumber(0)).toBe('0')
  })
})
