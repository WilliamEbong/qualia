import { describe, expect, it } from 'vitest'
import type { Coding } from './entities'
import { backendBlockedReason, calibrationCaption, calibrationRows, formatInterval, formatMetric, matchingCalibration, metricRows, parseEvaluations, reliabilityWord, reviewSentence } from './evaluation-state'
import type { EvaluationRecord } from './evaluation-state'
import { nextTheme, resolveTheme } from './theme'

const event = { backend: 'fake', model: 'fake-v1', codebook_version_id: 4, pipeline_version: 'pipeline', prompt_hash: 'prompt' } as Coding
const record = (extra: Partial<EvaluationRecord> = {}): EvaluationRecord => ({ id: 1, split: 'validation', backend: 'fake', model: 'fake-v1', codebook_version_id: 4, pipeline_version: 'pipeline', created_at: '2026-10-03', metrics_json: JSON.stringify({ ece: .125, scored_prediction_count: 8, identity: { prompt_hash: 'prompt' } }), ...extra })

describe('validation result identity and honest metric rendering', () => {
  it('uses only a matching scored validation result, not the latest global result', () => {
    const runs = parseEvaluations([record(), record({ id: 2, model: 'other' }), record({ id: 3, split: 'protected' })])
    expect(runs.map(run => run.id)).toEqual([2, 1])
    expect(matchingCalibration(event, runs)?.id).toBe(1)
    expect(calibrationCaption(event, runs)).toContain('Validation ECE 0.125 · 8 scored code assignments')
    for (const field of ['backend', 'model', 'pipeline_version', 'prompt_hash'] as const) {
      expect(matchingCalibration({ ...event, [field]: 'changed' }, runs)).toBeUndefined()
    }
    expect(matchingCalibration({ ...event, codebook_version_id: 5 }, runs)).toBeUndefined()
  })
  it('keeps missing, corrupt, unscored and undefined results unavailable', () => {
    for (const metrics_json of ['broken', 'null', '[]', '{}', '{"ece":0,"scored_prediction_count":0,"identity":{"prompt_hash":"prompt"}}']) {
      expect(calibrationCaption(event, parseEvaluations([record({ metrics_json })]))).toContain('ECE unavailable')
    }
    expect(formatMetric(null)).toBe('n/a')
    expect(formatMetric(undefined)).toBe('n/a')
    expect(formatMetric(Number.NaN)).toBe('n/a')
    expect(formatMetric(0)).toBe('0.000')
  })
})

describe('uncertainty shown in plain language', () => {
  it('formats Wilson ranges and falls back to the bare value for older runs', () => {
    expect(formatInterval(.5, [.0945, .9055])).toBe('0.500 (0.09–0.91)')
    expect(formatInterval(.5, undefined)).toBe('0.500')
    expect(formatInterval(.5, null)).toBe('0.500')
    expect(formatInterval(null, [.1, .2])).toBe('n/a')
    expect(formatInterval(.5, ['x', 1])).toBe('0.500')
  })
  it('labels agreement with cited bands and never invents a word for missing values', () => {
    expect(reliabilityWord('alpha', .81)).toBe('reliable')
    expect(reliabilityWord('alpha', .7)).toBe('tentative')
    expect(reliabilityWord('alpha', .5)).toBe('insufficient')
    expect(reliabilityWord('kappa', -.1)).toBe('poor')
    expect(reliabilityWord('kappa', .15)).toBe('slight')
    expect(reliabilityWord('kappa', .55)).toBe('moderate')
    expect(reliabilityWord('kappa', .9)).toBe('almost perfect')
    expect(reliabilityWord('kappa', null)).toBe('')
    const rows = metricRows({ kappa: .7, alpha: null, macro_f1: .5 })
    expect(rows.find(row => row.label === 'Cohen kappa')?.value).toBe('0.700 · substantial')
    expect(rows.find(row => row.label === 'Nominal alpha')?.value).toBe('n/a')
    expect(rows.every(row => row.help.length > 20)).toBe(true)
  })
  it('turns the review figures into one sentence with the current threshold', () => {
    expect(reviewSentence({ review_share: .35, review_cutoff: .64 }, .7)).toBe('Reviewing suggestions with a model-reported score below 0.64 (35% of them) leaves the rest at 90% precision or better on this validation set. Current review threshold: 0.70.')
    expect(reviewSentence({ review_share: 1, review_cutoff: null }, undefined)).toBe('No score cutoff reached 90% precision on this validation set, so every AI suggestion needs review.')
    expect(reviewSentence({ review_share: 0, review_cutoff: .1 }, .7)).toContain('already reach 90% precision')
    expect(reviewSentence({}, .7)).toBe('')
  })
  it('lists only populated calibration bands', () => {
    const bins = [{ lower: .7, upper: .8, count: 12, mean_confidence: .74, accuracy: .71 }, { lower: .8, upper: .9, count: 0, mean_confidence: null, accuracy: null }]
    expect(calibrationRows({ calibration_bins: bins })).toEqual([{ band: '0.7–0.8', count: 12, meanScore: '0.74', correct: '71%' }])
    expect(calibrationRows({})).toEqual([])
  })
})

describe('backend readiness explanations', () => {
  it('explains exactly why a run cannot start', () => {
    const local = { name: 'rules', available: true, external: false, reason: '' }
    const remote = { name: 'jev', available: true, external: true, reason: '' }
    expect(backendBlockedReason(true, local, true, 'Read-only.')).toBe('Read-only.')
    expect(backendBlockedReason(false, undefined, true, 'Read-only.')).toBe('Checking backend availability…')
    expect(backendBlockedReason(false, { ...local, available: false, reason: 'Not installed.' }, true, '')).toBe('Not installed.')
    expect(backendBlockedReason(false, remote, false, '')).toBe('External AI is disabled for this project.')
    expect(backendBlockedReason(false, remote, true, '')).toBe('')
    expect(backendBlockedReason(false, local, false, '')).toBe('')
  })
})

describe('remembered theme preference', () => {
  it('defaults to light and validates stored values before applying a theme', () => {
    expect(resolveTheme(null)).toBe('light')
    expect(resolveTheme('invalid')).toBe('light')
    expect(resolveTheme('dark')).toBe('dark')
    expect(resolveTheme(null, true)).toBe('dark')
    expect(resolveTheme('light', true)).toBe('light')
    expect(nextTheme(nextTheme('light'))).toBe('light')
  })
})
