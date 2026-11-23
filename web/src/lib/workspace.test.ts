import { describe, expect, it } from 'vitest'
import { codeStyle, eventCodeName, orderedCodes, shortcut, splitSuggestions, uniqueSegmentCount } from './entities'
import { annotationSpan, codingAnnotation, highlightStyle } from './annotation-offsets'
import type { Code, Coding, Segment, Version } from './entities'

const coding = (id: number, segment: number, code: number, start = 0, end = 1) => ({ id, segment_id: segment, code_id: code, span_start: start, span_end: end }) as Coding

describe('saved annotation boundary', () => {
  it('restores overlapping spans without moving emoji or combining marks', () => {
    const text = 'a😀e\u0301b'
    const first = codingAnnotation(coding(1, 8, 3, 1, 4), text)
    const second = codingAnnotation(coding(2, 8, 4, 2, 5), text)
    expect(first.target.selector[0]).toEqual({ start: 1, end: 5, quote: '😀e\u0301' })
    expect(second.target.selector[0]).toEqual({ start: 3, end: 6, quote: 'e\u0301b' })
    expect(annotationSpan(JSON.parse(JSON.stringify(first)), 8, text)).toEqual({ segmentId: 8, start: 1, end: 4 })
    expect(annotationSpan(JSON.parse(JSON.stringify(second)), 8, text)).toEqual({ segmentId: 8, start: 2, end: 5 })
  })
  it('rejects out-of-source selectors instead of producing invalid API offsets', () => {
    const annotation = codingAnnotation(coding(1, 8, 3), 'abc')
    annotation.target.selector[0].end = 50
    expect(annotationSpan(annotation, 8, 'abc')).toBeNull()
  })
})

describe('workspace controls and counts', () => {
  it('keeps the fixed code palette order and distinguishes repeated colors by hatch', () => {
    expect(Array.from({ length: 8 }, (_, index) => codeStyle(index)['--code-color'])).toEqual([
      'var(--code-1)', 'var(--code-2)', 'var(--code-3)', 'var(--code-4)',
      'var(--code-5)', 'var(--code-6)', 'var(--code-7)', 'var(--code-8)',
    ])
    expect(codeStyle(7)['--code-pattern']).toBe('none')
    expect(codeStyle(8)['--code-color']).toBe('var(--code-1)')
    expect(codeStyle(8)['--code-pattern']).toBe('var(--code-hatch)')
    expect(codeStyle(8)['--code-border']).toBe('solid')
  })
  it('keeps each decision label tied to its frozen version after a rename', () => {
    const versions = [
      { id: 1, snapshot_json: JSON.stringify([{ id: 7, name: 'Original label' }]) },
      { id: 2, snapshot_json: JSON.stringify([{ id: 7, name: 'Renamed label' }]) },
    ] as Version[]
    expect(eventCodeName({ code_id: 7, codebook_version_id: 1 }, versions)).toBe('Original label')
    expect(eventCodeName({ code_id: 7, codebook_version_id: 2 }, versions)).toBe('Renamed label')
    expect(eventCodeName({ code_id: 7, codebook_version_id: 3 }, versions)).toBe('Code 7 (version 3)')
    expect(eventCodeName({ code_id: 8, codebook_version_id: 1 }, versions)).toBe('Code 8 (version 1)')
  })
  it('bounds navigation at each end and maps only one-digit code shortcuts', () => {
    expect(shortcut('ArrowUp', 0, 5)).toEqual({ index: 0 })
    expect(shortcut('ArrowDown', 4, 5)).toEqual({ index: 4 })
    expect(shortcut('9', 0, 5)).toEqual({ codeIndex: 8 })
    expect(shortcut('0', 0, 5)).toEqual({})
    expect(shortcut('12', 0, 5)).toEqual({})
  })
  it('counts a segment once despite multiple spans and respects case sources', () => {
    const segments = [{ id: 1, source_id: 10 }, { id: 2, source_id: 20 }, { id: 3, source_id: 10 }] as Segment[]
    const events = [coding(1, 1, 7), coding(2, 1, 7, 1, 3), coding(3, 2, 7), coding(4, 3, 8)]
    expect(uniqueSegmentCount(events, 7, new Set([10]), segments)).toBe(1)
    expect(uniqueSegmentCount(events, 7, new Set([10, 20]), segments)).toBe(2)
  })
  it('displays parents before children while retaining archived records', () => {
    const codes = [{ id: 2, parent_id: 1 }, { id: 3, parent_id: null, status: 'archived' }, { id: 1, parent_id: null }] as Code[]
    expect(orderedCodes(codes).map(code => code.id)).toEqual([3, 1, 2])
  })
})

describe('in-vivo example', () => {
  it('counts characters, not UTF-16 units, and keeps only a requested nonblank quote', async () => {
    const { inVivoExample } = await import('./workspace')
    const emoji = '😀'.repeat(500)
    expect(inVivoExample(emoji, true)).toEqual([emoji])
    expect(inVivoExample(emoji + 'a', true)).toEqual([])
    expect(inVivoExample('Waiting.', false)).toEqual([])
    expect(inVivoExample('', true)).toEqual([])
  })
})

describe('counted', () => {
  it('uses the singular only for exactly one', async () => {
    const { counted } = await import('./entities')
    expect([0, 1, 2].map(count => counted(count, 'segment'))).toEqual(['0 segments', '1 segment', '2 segments'])
    expect(counted(1, 'cache hit')).toBe('1 cache hit')
    expect(counted(3, 'pending suggestion')).toBe('3 pending suggestions')
  })
})

describe('study status and next step', () => {
  it('counts the study and picks one next step in order', async () => {
    const { studyStatus } = await import('./entities')
    const base = { sources: [], segments: [], codes: [], codebook_versions: [], current_codings: [], suggestions: [] }
    const step = (extra: object) => studyStatus({ ...base, ...extra } as never).next
    expect(step({})).toEqual({ label: 'Import your first source', view: 'workspace', panel: 'import' })
    const sources = [{ id: 1 }], segments = [{ id: 1 }, { id: 2 }]
    expect(step({ sources, segments }).label).toBe('Create your first codes')
    expect(step({ sources, segments, codes: [{ id: 1 }] }).label).toBe('Freeze the codebook')
    const frozen = { codebook_versions: [{ id: 1, frozen_at: '2026-11-23T17:02:40Z' }] }
    expect(step({ sources, segments, codes: [{ id: 1 }], ...frozen }).label).toBe('Code a passage')
    const coded = { current_codings: [{ segment_id: 1 }, { segment_id: 1 }] }
    expect(step({ sources, segments, codes: [{ id: 1 }], ...frozen, ...coded, suggestions: [{}, {}] }))
      .toEqual({ label: 'Review 2 pending suggestions', view: 'review' })
    const done = studyStatus({ ...base, sources, segments, codes: [{ id: 1 }], ...frozen, ...coded } as never)
    expect(done.next.label).toBe('Explore the analysis')
    expect([done.sources, done.passages, done.coded, done.pending, done.latestVersion]).toEqual([1, 2, 1, 0, 'cb_v1 · 2026-11-23'])
  })
})

describe('matrix totals and retrieval grouping', () => {
  it('totals count distinct segments, so a segment in two cases counts once overall', async () => {
    const { matrixTotals } = await import('./entities')
    const data = { segments: [{ id: 1, source_id: 10 }, { id: 2, source_id: 20 }, { id: 3, source_id: 30 }],
      source_cases: [{ source_id: 10, case_id: 100 }, { source_id: 10, case_id: 200 }, { source_id: 20, case_id: 200 }],
      current_codings: [{ segment_id: 1, code_id: 5 }, { segment_id: 1, code_id: 6 }, { segment_id: 2, code_id: 5 }, { segment_id: 3, code_id: 5 }] }
    const totals = matrixTotals(data as never)
    // Segment 3's source has no case, so it is outside the matrix, as in the cells.
    expect(totals.byCode).toEqual({ 5: 2, 6: 1 })
    expect(totals.byCase).toEqual({ 100: 1, 200: 2 })
    expect(totals.all).toBe(2)
  })
  it('groups excerpts under their code in codebook order', async () => {
    const { groupByCode } = await import('./entities')
    const items: Array<{ code_id: number; segment_id: number }> = [{ code_id: 2, segment_id: 1 }, { code_id: 1, segment_id: 2 }, { code_id: 2, segment_id: 3 }]
    const groups = groupByCode(items, [1, 2], id => `Code ${id}`)
    expect(groups.map(group => [group.name, group.items.map(item => item.segment_id)])).toEqual([['Code 1', [2]], ['Code 2', [1, 3]]])
  })
})

describe('memo metadata line', () => {
  it('shows kind, date, author when known and the last edit date', async () => {
    const { memoMeta } = await import('./entities')
    expect(memoMeta({ kind: 'reflexive', created_at: '2026-11-23T17:02:40.774Z', author: 'AK' } as never, [])).toBe('reflexive memo · 2026-11-23 · AK')
    expect(memoMeta({ created_at: '2026-11-20T09:00:00Z' } as never, [{ replaced_at: '2026-11-21T10:00:00Z' }, { replaced_at: '2026-11-22T10:00:00Z' }] as never)).toBe('analytic memo · 2026-11-20 · edited 2026-11-22')
  })
})

describe('draft changes since the latest frozen codebook', () => {
  it('counts added, edited and removed codes', async () => {
    const { draftChanges } = await import('./entities')
    const code = (id: number, extra = {}) => ({ id, parent_id: null, name: `C${id}`, status: 'active', definition: '', include: '', exclude: '', examples_pos: '[]', examples_neg: '[]', ...extra })
    const frozen = { id: 1, hash: 'h', frozen_at: '2026-11-23', snapshot_json: JSON.stringify([code(1), code(2), code(3)]) }
    expect(draftChanges([code(1), code(2), code(3)] as never, frozen)).toBe(0)
    expect(draftChanges([code(1, { definition: 'new' }), code(2), code(4)] as never, frozen)).toBe(3)
    expect(draftChanges([code(1)] as never, undefined)).toBe(1)
  })
})

describe('codes changed since the latest frozen version', () => {
  it('lists the ids that are new or edited', async () => {
    const { changedCodeIds } = await import('./entities')
    const code = (id: number, extra = {}) => ({ id, parent_id: null, name: `C${id}`, status: 'active', definition: '', include: '', exclude: '', examples_pos: '[]', examples_neg: '[]', ...extra })
    const frozen = { id: 1, hash: 'h', frozen_at: '2026-11-23', snapshot_json: JSON.stringify([code(1), code(2)]) }
    expect([...changedCodeIds([code(1, { name: 'Renamed' }), code(2), code(3)] as never, frozen)]).toEqual([1, 3])
  })
})

describe('coded-text highlight', () => {
  it('underlines in the code colour over a light tint, so it never reads as a text selection', () => {
    expect(highlightStyle('#236292')).toEqual({ fill: '#236292', fillOpacity: 0.1, underlineColor: '#236292', underlineThickness: 2, underlineOffset: 2, underlineStyle: 'solid' })
  })
})

describe('suggestions beside applied codes', () => {
  it('nests a suggestion under the code it agrees with and keeps the rest separate', () => {
    const applied = [{ id: 1, code_id: 7 }, { id: 2, code_id: 7 }] as Coding[]
    const suggestions = [{ id: 10, code_id: 7 }, { id: 11, code_id: 8 }] as Coding[]
    const { agreeing, separate } = splitSuggestions(applied, suggestions)
    expect(agreeing(applied[0]).map(item => item.id)).toEqual([10])
    expect(agreeing(applied[1])).toEqual([]) // shown once, under the first mark for that code
    expect(separate.map(item => item.id)).toEqual([11])
  })
  it('keeps a suggestion from another frozen version separate, since the code may have been renamed', () => {
    const applied = [{ id: 1, code_id: 7, codebook_version_id: 1 }] as Coding[]
    const suggestions = [{ id: 10, code_id: 7, codebook_version_id: 2 }] as Coding[]
    const { agreeing, separate } = splitSuggestions(applied, suggestions)
    expect(agreeing(applied[0])).toEqual([])
    expect(separate.map(item => item.id)).toEqual([10])
  })
})
