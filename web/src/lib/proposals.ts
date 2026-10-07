import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import type { components } from '../api/schema'
import { request } from './client'
import type { Code } from './entities'
import { segmentText } from './entities'
import { acceptedProposals, draftSegmentIds, originCaption, proposalView } from './proposals-state'
import type { ProposalView } from './proposals-state'
import { codeFormValues, focusCodeEditor } from './workspace'
import type { WorkspaceController } from './workspace'
import { useModelChoice } from './models'

type Availability = components['schemas']['Availability']
type ProposalRun = components['schemas']['ProposalRun']
const proposers = ['claude', 'codex', 'fake']

export function useProposals(w: WorkspaceController, availability: Availability | null) {
  const [mode, setMode] = useState<'draft' | 'refine'>('draft')
  const [backend, setBackend] = useState('')
  const model = useModelChoice(availability, 'proposal', backend)
  const [sourceId, setSourceId] = useState<number | null>(null)
  const [count, setCount] = useState(10)
  const [codeIds, setCodeIds] = useState<number[]>([])
  const [focus, setFocus] = useState('')
  const [note, setNote] = useState('')
  const [accepting, setAccepting] = useState<ProposalView | null>(null)
  const [result, setResult] = useState<ProposalRun | null>(null)
  useEffect(() => { setAccepting(null); setResult(null); setCodeIds([]); setSourceId(null); setFocus(''); setNote('') }, [w.slug])

  const backends = availability?.backends.filter(item => proposers.includes(item.name)) ?? []
  // Prefer a subscription CLI the project allows; the offline fake backend is a demonstration fallback.
  useEffect(() => { if (!backend && backends.length) setBackend((backends.find(item => item.available && item.name !== 'fake' && (!item.external || availability?.allow_external)) ?? backends.find(item => item.name === 'fake'))?.name ?? '') }, [availability])
  const selectedBackend = backends.find(item => item.name === backend)
  const blockedReason = !selectedBackend ? 'Checking backend availability…' : !selectedBackend.available ? selectedBackend.reason || 'Backend unavailable.' : selectedBackend.external && !availability?.allow_external ? 'External AI is disabled in this project’s routing configuration.' : ''

  const codes = w.data?.codes ?? []
  const views = useMemo(() => (w.data?.code_proposals ?? []).map(item => proposalView(item, codes)), [w.data])
  const pending = views.filter(item => !item.decision).reverse()
  const decided = views.filter(item => item.decision).reverse()
  const origins = useMemo(() => acceptedProposals(w.data?.code_proposals ?? []), [w.data])
  const draftSource = sourceId ?? w.data?.sources[0]?.id ?? null
  const draftIds = draftSegmentIds(w.data?.segments ?? [], draftSource, count)

  const post = <T,>(route: string, body?: unknown) => request<T>(`projects/${encodeURIComponent(w.slug)}/codebook/proposals/${route}`, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) })
  const finish = async (run: ProposalRun) => {
    setResult(run); await w.reload()
    const count = run.proposal_ids.length
    if (run.status === 'completed') w.setNotice(count ? `${count} new ${count === 1 ? 'proposal is' : 'proposals are'} waiting for your decision.` : 'No new proposals: nothing in the current evidence meets a signal.')
  }
  const findEvidence = () => w.run(async () => { await finish(await post<ProposalRun>('evidence')) })
  const ask = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    void w.run(async () => {
      if (blockedReason) throw new Error(blockedReason)
      if (mode === 'draft' && !draftIds.length) throw new Error('Choose a source with segments to draft from.')
      if (mode === 'refine' && !codeIds.length) throw new Error('Choose one or two codes to refine.')
      const input: components['schemas']['ProposalInput'] = { mode, backend, model: model.model(), focus, segment_ids: mode === 'draft' ? draftIds : [], code_ids: mode === 'refine' ? codeIds : [] }
      await finish(await post<ProposalRun>('ai', input))
    })
  }
  const toggleCode = (id: number) => setCodeIds(value => value.includes(id) ? value.filter(item => item !== id) : [...value, id].slice(-2))
  const decide = (proposal: ProposalView, decision: 'accept' | 'reject', values?: components['schemas']['ProposalValues']) => post<components['schemas']['ProposalDecisionResult']>(`${proposal.id}/decision`, { decision, actor: w.actor, note, values })
  const reject = (proposal: ProposalView) => w.run(async () => {
    await decide(proposal, 'reject'); setNote(''); await w.reload(); w.setNotice('Proposal rejected; the decision and your note are kept.')
  })
  const startAccept = (proposal: ProposalView) => { w.setEditCode(null); setAccepting(proposal); focusCodeEditor() }
  const saveAccepted = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    if (!accepting) return
    void w.run(async () => {
      await decide(accepting, 'accept', codeFormValues(form)); setAccepting(null); setNote(''); await w.reload()
      w.setNotice('Proposal accepted into the draft codebook. Freeze a new version to code with it.')
    })
  }
  // Defaults for the shared code editor while a proposal is being reviewed.
  const editorCode: Code | null = accepting ? { id: accepting.target_code_id ?? 0, ...accepting.values, examples_pos: JSON.stringify(accepting.values.examples_pos), examples_neg: JSON.stringify(accepting.values.examples_neg) } : null

  return { mode, setMode, backend, setBackend, backends, blockedReason, sourceId: draftSource, setSourceId, count, setCount, draftIds, codeIds, toggleCode, focus, setFocus, note, setNote,
    model,
    pending, decided, result, findEvidence, ask, reject, accepting, startAccept, cancelAccept: () => setAccepting(null), saveAccepted, editorCode,
    originCaption: (codeId: number) => originCaption(origins.get(codeId)),
    excerpt: (segmentId: number) => { const segment = w.data?.segments.find(item => item.id === segmentId); return segment && w.data ? segmentText(w.data, segment) : '' },
  }
}
export type ProposalsController = ReturnType<typeof useProposals>
