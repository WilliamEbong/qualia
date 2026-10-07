import { describe, expect, it } from 'vitest'
import { descendantIds, exampleList } from './entities'
import type { Code, Proposal, Segment } from './entities'
import { acceptedProposals, draftSegmentIds, originCaption, proposalView } from './proposals-state'

const code = (id: number, values: Partial<Code> = {}) => ({ id, parent_id: null, name: `Code ${id}`, status: 'active', definition: '', include: '', exclude: '', examples_pos: '[]', examples_neg: '[]', ...values }) as Code
const proposal = (values: Partial<Proposal>) => ({ id: 1, batch_id: 'b', mode: 'draft', kind: 'new_code', target_code_id: null, payload_json: '{}', rationale: '', evidence_json: '{}', actor_type: 'model', backend: 'claude', model: 'haiku', cli_version: '2', prompt_hash: 'h', codebook_version_id: null, created_at: '', decision: null, decided_by: null, decision_note: null, applied_json: null, resulting_code_id: null, decided_at: null, ...values }) as Proposal

describe('codebook proposals', () => {
  it('shows only the fields a revision changes, with current and proposed values', () => {
    const current = code(3, { name: 'Support', examples_neg: '["old"]' })
    const view = proposalView(proposal({ kind: 'revise_code', target_code_id: 3, actor_type: 'rule', mode: 'evidence', backend: null, model: null,
      payload_json: JSON.stringify({ name: 'Support', parent_id: null, status: 'active', definition: '', include: '', exclude: '', examples_pos: [], examples_neg: ['old', 'new'] }),
      evidence_json: JSON.stringify({ signal: 'rejections' }) }), [current])
    expect(view.title).toBe('Revise “Support”')
    expect(view.origin).toBe('evidence from rejected AI suggestions · offline')
    expect(view.changes).toEqual([{ field: 'examples_neg', label: 'Negative examples', before: 'old', after: 'old\nnew' }])
  })
  it('lists a new code’s filled fields and labels model provenance', () => {
    const view = proposalView(proposal({ payload_json: JSON.stringify({ name: 'Waiting', definition: 'Delay.', examples_pos: ['I waited'], status: 'active', parent_id: null }) }), [])
    expect(view.title).toBe('New code “Waiting”')
    expect(view.origin).toBe('model-proposed · claude / haiku · draft')
    expect(view.changes.map(change => change.field)).toEqual(['name', 'definition', 'examples_pos'])
  })
  it('derives code origin from the latest accepted proposal only', () => {
    const items = [proposal({ id: 1, decision: 'reject', resulting_code_id: null }), proposal({ id: 2, decision: 'accept', resulting_code_id: 9, decided_by: 'ana' }),
      proposal({ id: 3, kind: 'revise_code', actor_type: 'rule', decision: 'accept', resulting_code_id: 9, decided_by: 'ben' })]
    const origins = acceptedProposals(items)
    expect([...origins.keys()]).toEqual([9])
    expect(originCaption(origins.get(9))).toBe('revised from evidence-based proposal #3 · accepted by ben')
    expect(originCaption(undefined)).toBe('')
  })
  it('sends the first passages of one source in reading order, at most twenty', () => {
    const segments = [3, 1, 2].map(ordinal => ({ id: ordinal * 10, source_id: 1, ordinal })) as Segment[]
    expect(draftSegmentIds([...segments, { id: 99, source_id: 2, ordinal: 0 } as Segment], 1, 2)).toEqual([10, 20])
    expect(draftSegmentIds(segments, 1, 50)).toHaveLength(3)
  })
})

describe('codebook editor helpers', () => {
  it('reads examples from API JSON text and demo arrays alike', () => {
    expect(exampleList('["a","b"]')).toEqual(['a', 'b'])
    expect(exampleList(['c'])).toEqual(['c'])
    expect(exampleList('not json')).toEqual([])
  })
  it('blocks a code and all its descendants as parent choices', () => {
    const codes = [code(1), code(2, { parent_id: 1 }), code(3, { parent_id: 2 }), code(4)]
    expect([...descendantIds(1, codes)].sort()).toEqual([1, 2, 3])
  })
})

describe('workspace payload', () => {
  it('rebuilds current coding from event IDs and keeps embedded demo rows', async () => {
    const { hydrateWorkspace } = await import('./entities')
    const events = [{ id: 1, segment_id: 1 }, { id: 2, segment_id: 2 }]
    const api = hydrateWorkspace({ coding_events: events, current_codings: [], current_coding_ids: [2, 9] } as never)
    expect(api.current_codings).toEqual([events[1]])
    const demo = hydrateWorkspace({ coding_events: events, current_codings: [events[0]] } as never)
    expect(demo.current_codings).toEqual([events[0]])
  })
})
