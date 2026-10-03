import { describe, expect, it } from 'vitest'
import { eventCodeName, orderedCodes, shortcut, uniqueSegmentCount } from './entities'
import { annotationSpan, codingAnnotation } from './annotation-offsets'
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
