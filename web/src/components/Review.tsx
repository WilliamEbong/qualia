import type { CSSProperties } from 'react'
import type { Coding } from '../lib/entities'
import { codeStyle } from '../lib/entities'
import type { WorkspaceController } from '../lib/workspace'
import type { ReviewController } from '../lib/review'
import { Button } from './ui/button'

export function Suggestion({ item, w, review }: { item: Coding; w: WorkspaceController; review: ReviewController }) {
  return <article className={`suggestion ${review.selected?.id === item.id ? 'selected-suggestion' : ''}`} style={codeStyle(w.codeIndex(item.code_id)) as CSSProperties} aria-label={`Suggestion ${item.id}`} onFocus={() => review.select(item.id)}>
    <Button className="suggestion-select" aria-pressed={review.selected?.id === item.id} onClick={() => review.select(item.id)}>{review.codeName(item)}</Button>
    <p className="caption">suggested · {review.modelScore(item.score)}</p><p className="caption">{review.eceCaption(item)}</p>
    <p className="caption">{review.reviewReasons(item.review_trigger).join(' · ')} · segment {item.segment_id}</p>
    <blockquote>{review.excerpt(item)}</blockquote><p>{item.rationale || 'No rationale supplied.'}</p>
    <details><summary>Suggestion provenance</summary><dl><dt>Backend / model</dt><dd>{item.backend} / {item.model}</dd><dt>CLI version</dt><dd>{item.cli_version}</dd><dt>Actor</dt><dd>{item.actor_type} · {item.actor}</dd><dt>Frozen codebook</dt><dd>{item.codebook_version_id}</dd><dt>Span</dt><dd>{item.span_start}:{item.span_end}</dd><dt>Pipeline hash</dt><dd>{item.pipeline_version}</dd><dt>Prompt hash</dt><dd>{item.prompt_hash}</dd><dt>Created</dt><dd>{item.created_at}</dd></dl></details>
    <div className="actions"><Button disabled={w.readOnly || w.busy || !w.actor.trim()} onClick={() => void review.review(item, 'accept')}>Accept <span className="caption">a</span></Button><Button disabled={w.readOnly || w.busy || !w.actor.trim()} onClick={() => void review.review(item, 'reject')}>Reject <span className="caption">r</span></Button><Button onClick={() => w.openSegment(item.segment_id)}>Open segment</Button></div>
  </article>
}

export function ReviewQueue({ w, review }: { w: WorkspaceController; review: ReviewController }) {
  return <section className="content-page" aria-label="Suggestion review queue"><header className="section-heading"><div><p className="caption">Human decisions, retained evidence</p><h2>Review suggestions</h2></div><span className="caption">{review.suggestions.length} pending suggestions</span></header>
    <div className="two-column"><div><form className="editor" onSubmit={review.classify}><fieldset disabled={w.readOnly}><h3>Run classification</h3><p>Classification proposes codes from the latest frozen codebook. Review each suggestion before it becomes an assignment.</p>
      <label>Backend<select value={review.backend} onChange={event => review.setBackend(event.target.value)} disabled={w.readOnly || w.busy}>{review.availability?.backends.map(item => <option key={item.name} value={item.name}>{item.name} · {item.external ? 'external' : 'offline'}{!item.available ? ' · unavailable' : ''}</option>) ?? <option value="rules">Checking availability…</option>}</select></label>
      <label>Model override (optional)<input name="model" placeholder="Use configured model" disabled={w.readOnly || w.busy} /></label><label>Scope<select name="scope" defaultValue="project"><option value="project">All project segments</option><option value="source" disabled={!w.segments.length}>Current source</option></select></label>
      {review.blockedReason && <p className="caption">{review.blockedReason}</p>}{review.availabilityError && <p role="alert">Availability unavailable: {review.availabilityError}</p>}
      <Button type="submit" disabled={w.readOnly || w.busy || !!review.blockedReason || !w.data?.codebook_versions.length || !w.data.segments.length}>Run classification</Button>
      {!w.data?.codebook_versions.length && <p className="caption">Freeze a codebook before classification.</p>}
      <details><summary>Backend availability and privacy</summary><p className="caption">External AI: {review.availability?.allow_external ? 'allowed by project policy' : 'disabled by project policy'}. Change project routing configuration explicitly to allow external processing.</p>{review.availability?.backends.map(item => <p key={item.name}><strong>{item.name}</strong> · {item.available ? 'available' : 'unavailable'} · {item.reason || (item.external ? 'External processing' : 'Runs locally without network')}</p>)}</details>
    </fieldset></form>{review.result && <div role="status" className="run-result"><h3>Classification {review.result.status}</h3><p>{review.result.suggestion_ids.length} suggestions · {review.result.segments} segments · {review.result.calls} calls · {review.result.cache_hits} cache hits</p><p className="caption">{review.result.backend} / {review.result.model} · run {review.result.run_id}</p>{review.result.errors.map((error, index) => <p role="alert" key={index}>{error}</p>)}</div>}
    <label>Reviewer<input disabled={w.readOnly} value={w.actor} onChange={event => w.setActor(event.target.value)} maxLength={200} /></label><label>Review note (optional)<textarea disabled={w.readOnly} value={review.note} onChange={event => review.setNote(event.target.value)} rows={3} /></label><p className="caption">Select a suggestion, then press a to accept or r to reject. Typing in a field never reviews a suggestion. Suggestions with several reasons appear in each relevant group.</p></div>
    <div>{!review.suggestions.length && <div className="empty"><h3>No pending suggestions</h3><p>Run local rules classification to propose codes, or continue coding manually.</p></div>}{review.groups.map(group => <section key={group.reason} aria-label={group.reason}><h3>{group.reason} <span className="caption">{group.items.length}</span></h3>{group.items.map(item => <Suggestion key={item.id} item={item} w={w} review={review} />)}</section>)}</div></div>
  </section>
}
