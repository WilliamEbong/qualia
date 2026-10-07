import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import type { components } from '../api/schema'
import { request } from './client'
import { eventCodeName, isEditingTarget, segmentText } from './entities'
import type { Coding } from './entities'
import type { WorkspaceController } from './workspace'
import { groupSuggestions, isAcceptedModel, modelScore, reasonCaption, reviewReasons, reviewShortcut } from './review-state'
import { calibrationCaption, parseEvaluations } from './evaluation-state'
import type { EvaluationRecord } from './evaluation-state'
import { useModelChoice } from './models'

export function useReview(w: WorkspaceController) {
  const [availability, setAvailability] = useState<components['schemas']['Availability'] | null>(null)
  const [availabilityError, setAvailabilityError] = useState('')
  const [backend, setBackend] = useState('rules')
  const model = useModelChoice(availability, 'classification', backend)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [note, setNote] = useState('')
  const [result, setResult] = useState<components['schemas']['ClassifyResult'] | null>(null)
  useEffect(() => {
    setAvailability(null); setBackend('rules'); setSelectedId(null); setNote(''); setResult(null)
  }, [w.slug])
  // Refetch when routing changes too (e.g. a kept model experiment), so "Task default" stays true.
  const routingKey = JSON.stringify(w.data?.routing ?? null)
  useEffect(() => {
    setAvailabilityError('')
    if (!w.slug) return
    const controller = new AbortController()
    request<components['schemas']['Availability']>(`projects/${encodeURIComponent(w.slug)}/ai/availability`, { signal: controller.signal })
      .then(value => { if (!controller.signal.aborted) setAvailability(value) })
      .catch(reason => { if (!controller.signal.aborted) setAvailabilityError(reason.message) })
    return () => controller.abort()
  }, [w.slug, routingKey])
  const suggestions = w.data?.suggestions ?? []
  const activeSuggestions = suggestions.filter(item => item.segment_id === w.active?.id)
  const groups = useMemo(() => groupSuggestions(suggestions), [suggestions])
  // Without a selection, a/r act on the first card shown (least certain first), not on raw order.
  const candidates = w.view === 'workspace' ? activeSuggestions : groups.flatMap(group => group.items)
  const selected = candidates.find(item => item.id === selectedId) ?? candidates[0]
  const selectedBackend = availability?.backends.find(item => item.name === backend)
  const blockedReason = w.readOnly ? 'AI is unavailable in this read-only public snapshot.' : !selectedBackend ? 'Checking backend availability…' : !selectedBackend.available ? selectedBackend.reason || 'Backend unavailable.' : selectedBackend.external && !availability?.allow_external ? 'External AI is disabled in this project’s routing configuration.' : ''
  const evaluations = useMemo(() => parseEvaluations((w.data?.evaluation_runs ?? []) as EvaluationRecord[]), [w.data])
  const review = (suggestion: Coding, decision: 'accept' | 'reject') => w.run(async () => {
    const input: components['schemas']['ReviewInput'] = { suggestion_id: suggestion.id, decision, actor: w.actor, note: selected?.id === suggestion.id ? note : '' }
    await request<components['schemas']['IdResult']>(`projects/${encodeURIComponent(w.slug)}/review`, { method: 'POST', body: JSON.stringify(input) })
    await w.reload(); setSelectedId(null); setNote('')
  })
  useEffect(() => {
    const handle = (event: KeyboardEvent) => {
      if (w.readOnly || !selected || w.busy || w.panel || !w.actor.trim() || !['workspace', 'review'].includes(w.view) || isEditingTarget(event.target) || event.altKey || event.ctrlKey || event.metaKey || event.repeat) return
      const decision = reviewShortcut(event.key)
      if (decision) { event.preventDefault(); void review(selected, decision) }
    }
    document.addEventListener('keydown', handle)
    return () => document.removeEventListener('keydown', handle)
  }, [selected, w.busy, w.panel, w.actor, w.view, w.slug, note, w.run, w.reload])
  const classify = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    void w.run(async () => {
      if (blockedReason) throw new Error(blockedReason)
      const input: components['schemas']['ClassifyInput'] = { backend, task: 'classification' }
      input.model = model.model()
      if (form.get('scope') === 'source') input.segment_ids = w.segments.map(item => item.id)
      const value = await request<components['schemas']['ClassifyResult']>(`projects/${encodeURIComponent(w.slug)}/classify`, { method: 'POST', body: JSON.stringify(input) })
      setResult(value); await w.reload()
    })
  }
  const excerpt = (item: Coding) => {
    const segment = w.data?.segments.find(segment => segment.id === item.segment_id)
    return segment && w.data ? Array.from(segmentText(w.data, segment)).slice(item.span_start, item.span_end).join('') : ''
  }
  return { availability, availabilityError, backend, setBackend, blockedReason, selected, select: (id: number) => { if (selected?.id !== id) setNote(''); setSelectedId(id) },
    model,
    suggestions, activeSuggestions, groups, note, setNote, result, review, classify, excerpt, modelScore, reviewReasons,
    reasonCaption: (value: string | null) => reasonCaption(value, w.data?.routing?.human_review_below), eceCaption: (item: Coding) => calibrationCaption(item, evaluations), isAcceptedModel,
    codeName: (item: Coding) => eventCodeName(item, w.data?.codebook_versions ?? []),
  }
}
export type ReviewController = ReturnType<typeof useReview>
