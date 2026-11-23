import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import type { components } from '../api/schema'
import type { WorkspaceController } from './workspace'
import type { ReviewController } from './review'
import { request } from './client'
import { eventCodeName } from './entities'
import { backendBlockedReason, benchmarkReason, calibrationRows, formatInterval, formatMetric, metricRows, parseEvaluations, reviewSentence } from './evaluation-state'
import type { BenchmarkStatus, EvaluationRecord } from './evaluation-state'
import { useModelChoice } from './models'

const formatPercent = (value: number | null | undefined) => typeof value === 'number' && Number.isFinite(value) ? `${Math.round(value * 1000) / 10}%` : 'n/a'

// Benchmarks are UTF-8; decode strictly so a bad byte is reported, never silently replaced.
async function utf8(file: File): Promise<string> {
  try { return new TextDecoder('utf-8', { fatal: true }).decode(await file.arrayBuffer()) } catch { throw new Error('The benchmark file is not valid UTF-8. Save it as UTF-8 and try again.') }
}

// Which benchmark splits the open project has, and in-app import (dev and validation only).
export function useBenchmarks(w: WorkspaceController) {
  const [status, setStatus] = useState<BenchmarkStatus | null>(null)
  const url = `projects/${encodeURIComponent(w.slug)}/benchmarks`
  useEffect(() => {
    setStatus(null)
    if (!w.slug || w.readOnly) return
    let current = true
    request<BenchmarkStatus>(url).then(value => { if (current) setStatus(value) }).catch(() => { if (current) setStatus({ dev: null, validation: null }) })
    return () => { current = false }
  }, [w.slug, w.readOnly, url])
  const importBenchmark = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); const target = event.currentTarget; const form = new FormData(target)
    void w.run(async () => {
      const file = form.get('file')
      if (!(file instanceof File) || !file.size) throw new Error('Choose a benchmark JSONL file.')
      const version = Number(form.get('version')) || null
      const input: components['schemas']['BenchmarkImportInput'] = { split: String(form.get('split')) as 'dev' | 'validation', version, content: await utf8(file) }
      setStatus(await request<BenchmarkStatus>(url, { method: 'POST', body: JSON.stringify(input) }))
      target.reset(); w.setNotice(`Imported the ${input.split} benchmark.`)
    })
  }
  return { status, importBenchmark }
}
export type BenchmarksController = ReturnType<typeof useBenchmarks>

export function useEvaluation(w: WorkspaceController, review: ReviewController, benchmarks: BenchmarksController) {
  const [backend, setBackend] = useState('rules')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [sample, setSample] = useState(50)
  const [repeat, setRepeat] = useState<components['schemas']['RepeatabilityResult'] | null>(null)
  const model = useModelChoice(review.availability, 'classification', backend)
  useEffect(() => { setBackend('rules'); setSelectedId(null); setRepeat(null) }, [w.slug])
  const runs = useMemo(() => parseEvaluations((w.data?.evaluation_runs ?? []) as EvaluationRecord[]), [w.data])
  const selected = runs.find(run => run.id === selectedId) ?? runs[0]
  const provider = review.availability?.backends.find(item => item.name === backend)
  // Repeatability samples ordinary project passages, so only validation needs a benchmark.
  const repeatReason = backendBlockedReason(w.readOnly, provider, review.availability?.allow_external, 'Evaluation is unavailable in this read-only public snapshot.')
  const blockedReason = repeatReason || benchmarkReason(benchmarks.status, ['validation'])
  const evaluate = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    void w.run(async () => {
      if (blockedReason) throw new Error(blockedReason)
      const input: components['schemas']['EvaluateInput'] = { backend, model: model.model() ?? null }
      const result = await request<components['schemas']['EvaluationResult']>(`projects/${encodeURIComponent(w.slug)}/evaluate`, { method: 'POST', body: JSON.stringify(input) })
      await w.reload(); setSelectedId(result.id)
    })
  }
  // Same sample twice without stored answers: how often does this model agree with itself?
  const checkRepeatability = () => w.run(async () => {
    if (repeatReason) throw new Error(repeatReason)
    const input: components['schemas']['RepeatabilityInput'] = { backend, model: model.model() ?? null, segments: sample }
    setRepeat(await request<components['schemas']['RepeatabilityResult']>(`projects/${encodeURIComponent(w.slug)}/repeatability`, { method: 'POST', body: JSON.stringify(input) }))
  })
  const metrics = selected?.metrics
  return { runs, selected, select: setSelectedId, backend, setBackend, blockedReason, repeatReason, evaluate, formatMetric, model, sample, setSample, checkRepeatability,
    repeat: repeat && { ...repeat, identicalText: formatPercent(repeat.identical_sets), rows: repeat.per_code.map(row => ({ code: eventCodeName({ code_id: Number(row.code_id), codebook_version_id: repeat.codebook_version_id }, w.data?.codebook_versions ?? []), agreement: formatPercent(row.agreement as number | null), kappa: formatMetric(row.kappa as number | null) })) },
    metricRows: metrics ? metricRows(metrics) : [],
    reviewSentence: metrics ? reviewSentence(metrics, w.data?.routing?.human_review_below) : '',
    calibrationRows: metrics ? calibrationRows(metrics) : [],
    perCode: (metrics?.per_code ?? []).map(row => ({ ...row, name: eventCodeName({ code_id: row.code_id, codebook_version_id: selected!.codebook_version_id }, w.data?.codebook_versions ?? []), precisionText: formatInterval(row.precision, row.precision_ci95), recallText: formatInterval(row.recall, row.recall_ci95), f1Text: formatMetric(row.f1) })),
    hasIntervals: (metrics?.per_code ?? []).some(row => Array.isArray(row.precision_ci95) || Array.isArray(row.recall_ci95)),
    definitions: Object.entries(metrics?.definitions ?? {}),
    alphaBasis: metrics?.alpha_basis === 'human_coders' ? 'Human coder code-set agreement' : metrics?.alpha_basis === 'reference_vs_prediction' ? 'Reference vs. prediction code-set agreement (not human intercoder reliability)' : 'Agreement basis not recorded',
  }
}
export type EvaluationController = ReturnType<typeof useEvaluation>
