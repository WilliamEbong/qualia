import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import type { components } from '../api/schema'
import type { WorkspaceController } from './workspace'
import type { ReviewController } from './review'
import { request } from './client'
import { backendBlockedReason } from './evaluation-state'
import { experimentHistory } from './experiment-state'
import type { ExperimentRecord } from './experiment-state'

export function useExperiments(w: WorkspaceController, review: ReviewController) {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const configured = typeof w.data?.routing?.backend === 'string' ? w.data.routing.backend : 'rules'
  const [backend, setBackend] = useState(configured)
  useEffect(() => setSelectedId(null), [w.slug])
  useEffect(() => setBackend(configured), [w.slug, configured])
  const history = useMemo(() => experimentHistory((w.data?.experiments ?? []) as ExperimentRecord[]), [w.data])
  const selected = history.find(item => item.id === selectedId) ?? history[0]
  const provider = review.availability?.backends.find(item => item.name === backend)
  const blockedReason = backendBlockedReason(w.readOnly, provider, review.availability?.allow_external, 'Tuning is unavailable in this read-only public snapshot.')
  const tune = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    void w.run(async () => {
      if (blockedReason) throw new Error(blockedReason)
      const input: components['schemas']['EvaluateInput'] = { backend, model: String(form.get('model') ?? '').trim() || null }
      const result = await request<components['schemas']['ExperimentResult']>(`projects/${encodeURIComponent(w.slug)}/tune-thresholds`, { method: 'POST', body: JSON.stringify(input) })
      await w.reload(); setSelectedId(result.id)
    })
  }
  return { history, selected, select: setSelectedId, backend, setBackend, blockedReason, tune }
}
export type ExperimentsController = ReturnType<typeof useExperiments>
