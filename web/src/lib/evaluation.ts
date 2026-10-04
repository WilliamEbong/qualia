import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import type { components } from '../api/schema'
import type { WorkspaceController } from './workspace'
import type { ReviewController } from './review'
import { request } from './client'
import { eventCodeName } from './entities'
import { formatMetric, metricRows, parseEvaluations } from './evaluation-state'
import type { EvaluationRecord } from './evaluation-state'

export function useEvaluation(w: WorkspaceController, review: ReviewController) {
  const [backend, setBackend] = useState('rules')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  useEffect(() => { setBackend('rules'); setSelectedId(null) }, [w.slug])
  const runs = useMemo(() => parseEvaluations((w.data?.evaluation_runs ?? []) as EvaluationRecord[]), [w.data])
  const selected = runs.find(run => run.id === selectedId) ?? runs[0]
  const provider = review.availability?.backends.find(item => item.name === backend)
  const blockedReason = w.readOnly ? 'Evaluation is unavailable in this read-only public snapshot.' : !provider ? 'Checking backend availability…' : !provider.available ? provider.reason || 'Backend unavailable.'
    : provider.external && !review.availability?.allow_external ? 'External AI is disabled for this project.' : ''
  const evaluate = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    void w.run(async () => {
      if (blockedReason) throw new Error(blockedReason)
      const input: components['schemas']['EvaluateInput'] = { backend, model: String(form.get('model') ?? '').trim() || null }
      const result = await request<components['schemas']['EvaluationResult']>(`projects/${encodeURIComponent(w.slug)}/evaluate`, { method: 'POST', body: JSON.stringify(input) })
      await w.reload(); setSelectedId(result.id)
    })
  }
  const metrics = selected?.metrics
  return { runs, selected, select: setSelectedId, backend, setBackend, blockedReason, evaluate, formatMetric,
    metricRows: metrics ? metricRows(metrics) : [],
    perCode: (metrics?.per_code ?? []).map(row => ({ ...row, name: eventCodeName({ code_id: row.code_id, codebook_version_id: selected!.codebook_version_id }, w.data?.codebook_versions ?? []), precisionText: formatMetric(row.precision), recallText: formatMetric(row.recall), f1Text: formatMetric(row.f1) })),
    definitions: Object.entries(metrics?.definitions ?? {}),
    alphaBasis: metrics?.alpha_basis === 'human_coders' ? 'Human coder code-set agreement' : metrics?.alpha_basis === 'reference_vs_prediction' ? 'Reference vs. prediction code-set agreement (not human intercoder reliability)' : 'Agreement basis not recorded',
  }
}
export type EvaluationController = ReturnType<typeof useEvaluation>
