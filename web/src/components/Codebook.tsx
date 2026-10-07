import { Fragment } from 'react'
import type { CSSProperties } from 'react'
import type { WorkspaceController } from '../lib/workspace'
import { exampleLines } from '../lib/workspace'
import { descendantIds } from '../lib/entities'
import { thresholdCaption } from '../lib/review-state'
import type { ProposalsController } from '../lib/proposals'
import type { ProposalView } from '../lib/proposals-state'
import { ModelPicker } from './ModelPicker'
import { Button } from './ui/button'

function ProposalCard({ w, p, item }: { w: WorkspaceController; p: ProposalsController; item: ProposalView }) {
  const passages = (item.evidence.segment_ids ?? []).slice(0, 3)
  return <article className="suggestion proposal" aria-label={`Proposal ${item.id}`}>
    <h4>{item.title}</h4><p className="caption">{item.origin} · proposal #{item.id}</p>
    <dl className="code-fields">{item.changes.map(change => <Fragment key={change.field}><dt>{change.label}</dt><dd className="preserve-lines">{change.before ? <><span className="caption">Current</span>{'\n'}{change.before}{'\n'}<span className="caption">Proposed</span>{'\n'}{change.after || '—'}</> : change.after || '—'}</dd></Fragment>)}</dl>
    {!item.changes.length && <p className="caption">No field differs from the current draft.</p>}
    <p>{item.rationale}</p>{item.evidence.focus && <p className="caption">Focus: {item.evidence.focus}</p>}
    {passages.length > 0 && <details><summary>Supporting passages ({item.evidence.segment_ids?.length})</summary>{passages.map(id => <div key={id}><blockquote>{p.excerpt(id)}</blockquote><Button onClick={() => w.openSegment(id)}>Open segment {id}</Button></div>)}</details>}
    <details className="provenance"><summary>Proposal provenance</summary><dl><dt>Mode</dt><dd>{item.mode}</dd><dt>Actor</dt><dd>{item.actor_type}</dd>{item.actor_type === 'model' && <><dt>Backend / model</dt><dd>{item.backend} / {item.model}{item.model_version && <> · answered by {item.model_version}</>}</dd><dt>CLI version</dt><dd>{item.cli_version}</dd><dt>Prompt hash</dt><dd>{item.prompt_hash}</dd></>}<dt>Based on codebook</dt><dd>{item.codebook_version_id ? `cb_v${item.codebook_version_id}` : 'No frozen version yet'}</dd><dt>Batch</dt><dd>{item.batch_id}</dd><dt>Created</dt><dd>{item.created_at}</dd></dl></details>
    <div className="actions"><Button disabled={w.busy || !w.actor.trim()} onClick={() => p.startAccept(item)}>Review and accept</Button><Button disabled={w.busy || !w.actor.trim()} onClick={() => void p.reject(item)}>Reject</Button></div>
  </article>
}

function Proposals({ w, p }: { w: WorkspaceController; p: ProposalsController }) {
  return <section className="proposals" aria-label="Codebook proposals">
    <div className="section-heading"><h3>Proposals</h3><span className="caption">{p.pending.length} awaiting decision</span></div>
    <p className="caption">Proposals never change the codebook by themselves. Accepting copies the values you confirm into the draft; freezing stays your decision. AI proposals can split ideas too finely, miss implicit meaning and blur boundaries. They are not themes.</p>
    {w.readOnly ? <div className="empty"><h3>Proposals need the local app</h3><p>This public demo is read-only. In your own project, Qualia can draft codes from passages, refine codes from your review decisions, or find evidence in your reviews offline.</p></div> : <>
      <details className="proposal-request"><summary>Ask for proposals</summary>
        <Button disabled={w.busy} onClick={() => void p.findEvidence()}>Find evidence in my reviews</Button>
        <p className="caption">Offline, no AI: codes with repeatedly rejected suggestions, unused codes, and codes that nearly always appear together.</p>
        <form className="editor" onSubmit={p.ask}><fieldset disabled={w.busy}>
          <label>Proposal type<select value={p.mode} onChange={event => p.setMode(event.target.value as 'draft' | 'refine')}><option value="draft">Draft new codes from passages</option><option value="refine">Refine codes from review evidence</option></select></label>
          <label>Backend<select value={p.backend} onChange={event => p.setBackend(event.target.value)}>{p.backends.length ? p.backends.map(item => <option key={item.name} value={item.name}>{item.name} · {item.external ? 'external' : 'offline demonstration'}{item.available ? '' : ' · unavailable'}</option>) : <option value="">Checking availability…</option>}</select></label>
          <ModelPicker id="proposal-model" m={p.model} disabled={w.readOnly || w.busy} />
          {p.mode === 'draft' ? <>
            <label>Source<select value={p.sourceId ?? ''} onChange={event => p.setSourceId(Number(event.target.value) || null)}>{w.data?.sources.map(source => <option key={source.id} value={source.id}>{source.name}</option>)}</select></label>
            <label>Passages to send (1–20)<input type="number" min={1} max={20} value={p.count} onChange={event => p.setCount(Number(event.target.value))} /></label>
            <p className="caption">Sends the first {p.draftIds.length} segments of this source and your current code names, so proposals avoid duplicates.</p>
            <label>Focus (optional)<textarea rows={2} maxLength={500} value={p.focus} onChange={event => p.setFocus(event.target.value)} placeholder="For example: experiences of waiting for care" /></label>
          </> : <fieldset className="choices"><legend>Codes to refine (up to two)</legend>{w.codes.filter(code => code.status === 'active').map(code => <label key={code.id} className="checkbox"><input type="checkbox" checked={p.codeIds.includes(code.id)} onChange={() => p.toggleCode(code.id)} />{code.name}</label>)}<p className="caption">Sends each code with up to four coded and four rejected passages and your review notes.</p></fieldset>}
          {p.blockedReason && <p className="caption">{p.blockedReason}</p>}
          <Button type="submit" disabled={w.busy || !!p.blockedReason}>Ask for proposals</Button>
        </fieldset></form>
      </details>
      {p.result && <div role="status" className="run-result"><h3>Proposals {p.result.status}</h3><p>{p.result.proposal_ids.length} new proposals</p><p className="caption">{p.result.backend} / {p.result.model} · batch {p.result.batch_id}</p>{p.result.errors.map((error, index) => <p key={index} className="error">{error}</p>)}</div>}
      <label>Reviewer<input value={w.actor} onChange={event => w.setActor(event.target.value)} maxLength={200} /></label>
      <label>Decision note (optional)<textarea rows={2} value={p.note} onChange={event => p.setNote(event.target.value)} /></label>
      {!p.pending.length && <p className="caption">No proposals are waiting.</p>}
      {p.pending.map(item => <ProposalCard key={item.id} w={w} p={p} item={item} />)}
    </>}
    {p.decided.length > 0 && <details className="version"><summary>Decided proposals ({p.decided.length})</summary>{p.decided.map(item => <p key={item.id} className="caption">#{item.id} · {item.title} · {item.decision === 'accept' ? 'accepted' : 'rejected'} by {item.decided_by}{item.decision_note ? ` · “${item.decision_note}”` : ''}</p>)}</details>}
  </section>
}

export function Codebook({ w, proposals: p }: { w: WorkspaceController; proposals: ProposalsController }) {
  const editing = p.editorCode ?? w.editCode
  const blocked = editing?.id ? descendantIds(editing.id, w.codes) : new Set<number>()
  return <section className="content-page codebook-page" aria-label="Codebook">
    <header className="section-heading"><div><p className="caption">Researcher-controlled methodology</p><h2>Codebook</h2></div><Button disabled={w.readOnly || w.busy || !w.codes.some(code => code.status === 'active')} onClick={() => void w.freeze()}>Freeze codebook</Button></header>
    <p>Draft edits apply to the next frozen version. Existing coding always retains the version used for its decision.</p>
    <div className="two-column"><div>
      <Proposals w={w} p={p} />
      {!w.codes.length && <div className="empty"><h3>No codes yet</h3><p>Describe the first idea you want to track, or ask for draft proposals above, then freeze a version to begin coding.</p></div>}
      {w.codes.map(code => <article key={code.id} className="code-card" style={{ '--depth': code.depth } as CSSProperties}><div className="section-heading"><h3>{code.name}</h3><span className="caption">{code.status}</span></div>{p.originCaption(code.id) && <p className="caption">{p.originCaption(code.id)}</p>}{thresholdCaption(w.data?.routing, code.id) && <p className="caption">{thresholdCaption(w.data?.routing, code.id)}</p>}<p className="code-definition">{code.definition || 'No definition supplied.'}</p><dl className="code-fields"><dt>Include</dt><dd>{code.include || '—'}</dd><dt>Exclude</dt><dd className="preserve-lines">{code.exclude || '—'}</dd><dt>Positive examples</dt><dd className="preserve-lines">{code.positive || '—'}</dd><dt>Negative examples</dt><dd className="preserve-lines">{code.negative || '—'}</dd></dl><Button disabled={w.readOnly} onClick={() => { p.cancelAccept(); w.startEditCode(code) }}>Edit {code.name}</Button></article>)}
      <h3>Frozen versions</h3>{w.data?.codebook_versions.map(version => <details key={version.id} className="version"><summary>cb_v{version.id} · frozen {version.frozen_at}</summary><p className="caption hash">{version.hash}</p><pre>{version.snapshot_json}</pre></details>)}
    </div><form id="code-editor" className="editor" key={p.accepting ? `proposal-${p.accepting.id}` : `${w.editCode?.id ?? 'new'}-${w.formNonce}`} onSubmit={p.accepting ? p.saveAccepted : w.saveCode}><fieldset disabled={w.readOnly}>
      <div className="section-heading"><h3>{p.accepting ? `Accept proposal #${p.accepting.id}` : w.editCode ? `Edit ${w.editCode.name}` : 'Create code'}</h3>{p.accepting ? <Button onClick={p.cancelAccept}>Cancel</Button> : w.editCode && <Button onClick={() => w.startEditCode(null)}>New code</Button>}</div>
      {p.accepting && <p className="caption">{p.accepting.title}. Edit anything before accepting; saving records your decision as {w.actor || 'the reviewer'} and changes only the draft codebook.</p>}
      <label>Name<input name="name" required maxLength={200} defaultValue={editing?.name ?? ''} /></label><label>Parent code<select name="parent_id" defaultValue={editing?.parent_id ?? ''}><option value="">No parent</option>{w.codes.map(code => <option key={code.id} value={code.id} disabled={blocked.has(code.id)}>{code.name}</option>)}</select></label>
      <label>Definition<textarea name="definition" rows={3} defaultValue={editing?.definition ?? ''} /></label><label>Include<textarea name="include" rows={2} defaultValue={editing?.include ?? ''} /></label><label>Exclude<textarea name="exclude" rows={2} defaultValue={editing?.exclude ?? ''} /></label><label>Positive examples, one per line<textarea name="examples_pos" rows={2} defaultValue={exampleLines(editing?.examples_pos ?? '[]')} /></label><label>Negative examples, one per line<textarea name="examples_neg" rows={2} defaultValue={exampleLines(editing?.examples_neg ?? '[]')} /></label>
      <label>Status<select name="status" defaultValue={editing?.status ?? 'active'}><option value="active">Active</option><option value="archived">Archived</option></select></label><p className="caption">Archiving retains historical references.</p><Button type="submit" className="primary" disabled={w.readOnly || w.busy || (!!p.accepting && !w.actor.trim())}>{p.accepting ? 'Accept into draft codebook' : 'Save draft code'}</Button>
    </fieldset></form></div>
  </section>
}
