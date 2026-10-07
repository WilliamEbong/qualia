import { useEffect, useState } from 'react'
import type { components } from '../api/schema'

type Availability = components['schemas']['Availability'] | null | undefined
type Task = 'classification' | 'escalation' | 'proposal'

export function modelOptions(availability: Availability, backend: string): components['schemas']['ModelChoice'][] {
  return availability?.backends.find(item => item.name === backend)?.models ?? []
}

export function defaultModel(availability: Availability, task: Task, backend: string): string | undefined {
  return availability?.defaults?.[task]?.[backend]
}

export function modelLabel(availability: Availability, backend: string, model: string | undefined): string {
  return modelOptions(availability, backend).find(item => item.id === model)?.label ?? model ?? 'Configured model'
}

export function requestModel(choice: string, customText: string): string | undefined {
  if (choice === '') return undefined
  if (choice !== '__custom') return choice
  const model = customText.trim()
  if (!/^[A-Za-z0-9][A-Za-z0-9_.:\/-]{0,119}$/.test(model)) {
    throw new Error('Enter a model ID using letters, digits, dot, dash, underscore, colon or slash.')
  }
  return model
}

/** Model selection state for one form: '' is the task default, '__custom' an exact ID. */
export function useModelChoice(availability: Availability, task: Task, backend: string) {
  const [choice, setChoice] = useState('')
  const [custom, setCustom] = useState('')
  useEffect(() => { setChoice(''); setCustom('') }, [backend])
  const models = modelOptions(availability, backend)
  const taskDefault = defaultModel(availability, task, backend)
  return {
    models, choice, setChoice, custom, setCustom,
    defaultId: taskDefault,
    defaultLabel: modelLabel(availability, backend, taskDefault),
    description: models.find(item => item.id === (choice || taskDefault))?.description ?? '',
    model: () => requestModel(choice, custom),
  }
}
export type ModelChoiceController = ReturnType<typeof useModelChoice>
