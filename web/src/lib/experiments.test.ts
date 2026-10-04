import { describe, expect, it } from 'vitest'
import { experimentHistory } from './experiment-state'
import type { ExperimentRecord } from './experiment-state'

const record = (extra: Partial<ExperimentRecord> = {}): ExperimentRecord => ({ id: 1, slug: 'candidate', agent: 'fake', decision: 'REVERT', reason: 'measured regression', hypothesis: 'Operator claims a large gain', before_json: JSON.stringify({ metrics: { macro_f1: .6, calls: 10 } }), after_json: JSON.stringify({ metrics: { macro_f1: .5, calls: 12 }, confirmation: { metrics: { macro_f1: .49 } } }), changed_files_json: '["config/prompts/classify.txt"]', commit_hash: null, tag: null, created_at: '2026-10-03', ...extra })

describe('recorded experiment evidence', () => {
  it('displays the stored decision and measured values independently of operator claims', () => {
    const entry = experimentHistory([record()])[0]
    expect(entry.decisionText).toBe('REVERT')
    expect(entry.deltaText).toBe('-0.100')
    expect(entry.rows[0]).toEqual({ name: 'Macro F1', before: '0.600', after: '0.500', confirmation: '0.490' })
    expect(entry.files).toEqual(['config/prompts/classify.txt'])
  })
  it('does not fabricate missing measurements, confirmation, files or a decision', () => {
    for (const malformed of ['broken', 'null', '[]', '{}', '{"metrics":[]}']) {
      const entry = experimentHistory([record({ before_json: malformed, after_json: malformed, changed_files_json: '{}', decision: 'operator says KEEP' })])[0]
      expect(entry.measurementsAvailable).toBe(false)
      expect(entry.rows[0].after).toBe('n/a')
      expect(entry.rows[0].confirmation).toBe('n/a')
      expect(entry.deltaText).toBe('n/a')
      expect(entry.files).toBeNull()
      expect(entry.decisionText).toBe('Decision unavailable')
    }
  })
  it('orders immutable attempts newest first and keeps successful commit identity', () => {
    const entries = experimentHistory([record(), record({ id: 2, decision: 'KEEP', tag: 'exp-0002-candidate', commit_hash: 'abc123' })])
    expect(entries.map(item => item.id)).toEqual([2, 1])
    expect(entries[0].decisionText).toBe('KEEP')
    expect(entries[0].tag).toBe('exp-0002-candidate')
  })
})
