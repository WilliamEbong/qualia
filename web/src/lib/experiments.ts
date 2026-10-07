import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import type { components } from '../api/schema'
import type { WorkspaceController } from './workspace'
import type { ReviewController } from './review'
import { request } from './client'
import { backendBlockedReason } from './evaluation-state'
import { experimentHistory } from './experiment-state'
import type { ExperimentRecord } from './experiment-state'
import { useModelChoice } from './models'

export function useExperiments(w: WorkspaceController, review: ReviewController) {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const configured = typeof w.data?.routing?.backend === 'string' ? w.data.routing.backend : 'rules'
  const [backend, setBackend] = useState(configured)
  const [candidateBackend, setCandidateBackend] = useState('claude')
  const model = useModelChoice(review.availability, 'classification', backend)
  const candidate = useModelChoice(review.availability, 'classification', candidateBackend)
  useEffect(() => setSelectedId(null), [w.slug])
  useEffect(() => setBackend(configured), [w.slug, configured])
  const history = useMemo(() => experimentHistory((w.data?.experiments ?? []) as ExperimentRecord[]), [w.data])
  const selected = history.find(item => item.id === selectedId) ?? history[0]
  const provider = review.availability?.backends.find(item => item.name === backend)
  const blockedReason = backendBlockedReason(w.readOnly, provider, review.availability?.allow_external, 'Tuning is unavailable in this read-only public snapshot.')
  const tune = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    void w.run(async () => {
      if (blockedReason) throw new Error(blockedReason)
      const input: components['schemas']['EvaluateInput'] = { backend, model: model.model() ?? null }
      const result = await request<components['schemas']['ExperimentResult']>(`projects/${encodeURIComponent(w.slug)}/tune-thresholds`, { method: 'POST', body: JSON.stringify(input) })
      await w.reload(); setSelectedId(result.id)
    })
  }
  const candidateProvider = review.availability?.backends.find(item => item.name === candidateBackend)
  const candidateBlocked = backendBlockedReason(w.readOnly, candidateProvider, review.availability?.allow_external, 'Model experiments are unavailable in this read-only public snapshot.')
  const current = `${configured} / ${typeof w.data?.routing?.model === 'string' ? w.data.routing.model : 'configured model'}`
  // A model switch is measured like any experiment: baseline, candidate and confirmation on validation.
  const tryModel = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    void w.run(async () => {
      if (candidateBlocked) throw new Error(candidateBlocked)
      const chosen = candidate.model() ?? candidate.defaultId
      if (!chosen) throw new Error('Choose a model to try.')
      const input: components['schemas']['ModelExperimentInput'] = { backend: candidateBackend, model: chosen }
      const result = await request<components['schemas']['ExperimentResult']>(`projects/${encodeURIComponent(w.slug)}/experiments/model`, { method: 'POST', body: JSON.stringify(input) })
      await w.reload(); setSelectedId(result.id)
    })
  }
  return { history, selected, select: setSelectedId, backend, setBackend, blockedReason, tune, model,
    candidateBackend, setCandidateBackend, candidate, candidateBlocked, current, tryModel }
}
export type ExperimentsController = ReturnType<typeof useExperiments>
