import { describe, expect, it } from 'vitest'
import type { Coding } from './entities'
import { calibrationCaption, formatMetric, matchingCalibration, parseEvaluations } from './evaluation-state'
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
