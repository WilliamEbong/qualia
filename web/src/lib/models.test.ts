import { expect, test } from 'vitest'
import type { components } from '../api/schema'
import { defaultModel, modelLabel, modelOptions, requestModel } from './models'

const availability: components['schemas']['Availability'] = {
  allow_external: true,
  backends: [
    { name: 'claude', available: true, external: true, reason: '', models: [
      { id: 'haiku', label: 'Haiku', description: 'Quick classification.' },
      { id: 'opus', label: 'Opus', description: 'Detailed proposals.' },
    ] },
    { name: 'codex', available: false, external: true, reason: 'Unavailable', models: [{ id: 'luna', label: 'Luna', description: 'Fast.' }] },
    { name: 'rules', available: true, external: false, reason: '' },
  ],
  defaults: { classification: { claude: 'haiku', codex: 'luna' }, escalation: { claude: 'opus' }, proposal: { claude: 'opus' } },
}

test('options preserve backend catalogue order and metadata, including unavailable backends', () => {
  expect(modelOptions(availability, 'claude')).toEqual(availability.backends[0].models)
  expect(modelOptions(availability, 'codex')).toEqual(availability.backends[1].models)
  expect(modelOptions(availability, 'rules')).toEqual([])
  expect(modelOptions(availability, 'missing')).toEqual([])
  expect(modelOptions(null, 'claude')).toEqual([])
})

test('defaults are specific to the task and backend', () => {
  expect(defaultModel(availability, 'classification', 'claude')).toBe('haiku')
  expect(defaultModel(availability, 'classification', 'codex')).toBe('luna')
  expect(defaultModel(availability, 'escalation', 'claude')).toBe('opus')
  expect(defaultModel(availability, 'proposal', 'claude')).toBe('opus')
  expect(defaultModel(availability, 'proposal', 'codex')).toBeUndefined()
  expect(defaultModel({ allow_external: false, backends: [] }, 'classification', 'rules')).toBeUndefined()
  expect(defaultModel(null, 'classification', 'claude')).toBeUndefined()
})

test('labels use the catalogue, with exact ID and unavailable-default fallbacks', () => {
  expect(modelLabel(availability, 'claude', 'haiku')).toBe('Haiku')
  expect(modelLabel(availability, 'claude', 'claude-opus-5-5')).toBe('claude-opus-5-5')
  expect(modelLabel(null, 'claude', undefined)).toBe('Configured model')
})

test('default omits the request model and a catalogue choice passes through', () => {
  expect(requestModel('', 'ignored invalid text')).toBeUndefined()
  expect(requestModel('haiku', 'ignored invalid text')).toBe('haiku')
})

test.each(['claude-opus-5-5', 'provider/model_v1.2:latest', 'a', '9', 'a'.repeat(120)])('custom model accepts and trims %s', model => {
  expect(requestModel('__custom', ` \t${model}\n `)).toBe(model)
})

test.each(['', '   ', '-model', '_model', '/model', 'model name', 'model\nname', 'model@host', 'mödél', 'a'.repeat(121)])('custom model rejects invalid ID %j', model => {
  expect(() => requestModel('__custom', model)).toThrow(new Error('Enter a model ID using letters, digits, dot, dash, underscore, colon or slash.'))
})
