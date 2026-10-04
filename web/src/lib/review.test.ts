import { describe, expect, it } from 'vitest'
import { eceCaption, groupSuggestions, isAcceptedModel, modelScore, reviewReasons, reviewShortcut } from './review-state'
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
