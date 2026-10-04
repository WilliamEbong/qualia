import { describe, expect, it } from 'vitest'
import { eceCaption, groupSuggestions, isAcceptedModel, modelScore, reasonCaption, reviewReasons, reviewShortcut, thresholdCaption } from './review-state'
import type { Coding } from './entities'

describe('review trust semantics', () => {
  it('groups every applicable trigger and keeps unflagged suggestions reviewable', () => {
    const items = [{ id: 1, review_trigger: '["below_threshold","qc_sample","qc_sample"]' }, { id: 2, review_trigger: '[]' }] as Coding[]
    expect(groupSuggestions(items).map(group => [group.reason, group.items.map(item => item.id)])).toEqual([
      ['Below review threshold', [1]], ['Quality-control sample', [1]], ['Human review', [2]],
    ])
    expect(reviewReasons('["disagreement"]')).toEqual(['Backend disagreement'])
    expect(reviewReasons('broken')).toEqual(['Human review'])
  })
  it('explains why an item waits and shows the least certain first', () => {
    expect(reasonCaption('["below_threshold","qc_sample"]', .7)).toBe('Below review threshold (current threshold 0.70) · Quality-control sample')
    expect(reasonCaption('["disagreement"]', .7)).toBe('Backend disagreement')
    expect(reasonCaption('["below_threshold"]', undefined)).toBe('Below review threshold')
    const items = [{ id: 1, score: .6, review_trigger: '["below_threshold"]' }, { id: 2, score: null, review_trigger: '["below_threshold"]' }, { id: 3, score: .3, review_trigger: '["below_threshold"]' }] as Coding[]
    expect(groupSuggestions(items)[0].items.map(item => item.id)).toEqual([3, 1, 2])
  })
  it('captions explicit per-code thresholds only', () => {
    expect(thresholdCaption({ code_thresholds: { '4': .6 } }, 4)).toBe('AI suggests at score ≥ 0.60')
    expect(thresholdCaption({ code_thresholds: { '4': .6 } }, 5)).toBe('')
    expect(thresholdCaption({}, 4)).toBe('')
    expect(thresholdCaption(undefined, 4)).toBe('')
  })
  it('does not turn a missing score or validation result into accuracy', () => {
    expect(modelScore(0.826)).toBe('model-reported 0.83')
    expect(modelScore(null)).toBe('model-reported score unavailable')
    expect(modelScore(Number.NaN)).toBe('model-reported score unavailable')
    expect(eceCaption).toContain('ECE unavailable')
  })
  it('retains model identity after human acceptance without marking rejections as accepted', () => {
    expect(isAcceptedModel({ action: 'accept', backend: 'fake' })).toBe(true)
    expect(isAcceptedModel({ action: 'assign', backend: null })).toBe(false)
    expect(isAcceptedModel({ action: 'reject', backend: 'fake' })).toBe(false)
    expect(reviewShortcut('a')).toBe('accept')
    expect(reviewShortcut('r')).toBe('reject')
    expect(reviewShortcut('Enter')).toBeNull()
  })
})
