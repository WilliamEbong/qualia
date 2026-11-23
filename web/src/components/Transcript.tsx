import type { CSSProperties } from 'react'
import { Annotorious } from '@annotorious/react'
import { TextAnnotator } from '@recogito/react-text-annotator'
import { AnnotationSync, annotationStyle } from '../lib/annotations'
import { codeStyle } from '../lib/entities'
import type { WorkspaceController } from '../lib/workspace'
import { Button } from './ui/button'
import { ActorField } from './ActorField'
import type { ReviewController } from '../lib/review'
import { Suggestion } from './Review'

export function Transcript({ w, review }: { w: WorkspaceController; review: ReviewController }) {
  return <section className="transcript-panel" aria-label="Transcript">
    <header className="section-heading transcript-heading"><div><p className="caption">Source {w.source?.id ?? '—'}</p><h2>{w.source?.name ?? 'Your research begins here'}</h2>{w.sources.length > 1 && <label className="source-switch">Switch source<select value={w.source?.id ?? ''} onChange={event => w.selectSource(Number(event.target.value))}>{w.sources.map(source => <option key={source.id} value={source.id}>{source.name}</option>)}</select></label>}</div><Button disabled={w.readOnly} onClick={() => w.setPanel('import')}>Import source</Button></header>
    <p className="caption">{w.readOnly ? 'Read-only snapshot · ↑ / ↓ next or previous passage · inspect saved coding and provenance' : '↑ / ↓ next or previous passage · 1–9 apply a code · select text to code part of a passage · Esc clears the selection'}</p>
    {!w.segments.length && <div className="empty"><h3>No transcript open</h3><p>Select a source on the left, or choose Import source to add a transcript (TXT, Markdown or CSV). Your text stays in this local project.</p></div>}
    <div className="transcript">
      {w.segments.map(segment => <article id={`segment-${segment.id}`} key={`${w.slug}-${segment.id}`} tabIndex={0} aria-label={`Segment ${segment.ordinal + 1}`} className={`segment ${w.active?.id === segment.id ? 'active-segment' : ''}`} onFocus={() => w.activate(segment.id)} onPointerDown={() => w.activate(segment.id)}>
        <div className="segment-heading"><span className="caption">{segment.speaker ? `${segment.speaker} / ` : 'Passage '}{segment.ordinal + 1}</span><span className="caption">segment {segment.id}</span></div>
        <Annotorious><TextAnnotator annotatingEnabled={!w.readOnly} selectionMode="all" style={annotationStyle(w.codes.map(code => code.id))}>
          <p className="segment-text" data-testid={`segment-text-${segment.id}`}>{segment.text}</p>
          <AnnotationSync segmentId={segment.id} text={segment.text} codings={segment.codings} onSpan={w.receiveSpan} />
        </TextAnnotator></Annotorious>
        <div className="segment-codes" role="group" aria-label="Current codes">{segment.codings.map(coding => <span key={coding.id} className={`code-mark ${review.isAcceptedModel(coding) ? 'accepted-model' : 'human'}`} style={codeStyle(w.codeIndex(coding.code_id)) as CSSProperties}>{w.eventCodeName(coding)}{review.isAcceptedModel(coding) && <span className="caption"> · m</span>}{(coding.span_start > 0 || coding.span_end < Array.from(segment.text).length) && <span className="caption"> · characters {coding.span_start}–{coding.span_end}</span>}</span>)}</div>
        <div className="segment-codes" role="group" aria-label="Suggested codes">{segment.suggestions.map(item => <span key={item.id} className="code-mark suggested" style={codeStyle(w.codeIndex(item.code_id)) as CSSProperties}>{review.codeName(item)} <span className="caption">suggested · {review.modelScore(item.score)}</span></span>)}</div>
      </article>)}
    </div>
  </section>
}

export function CodingPanel({ w, review }: { w: WorkspaceController; review: ReviewController }) {
  return <aside className={`coding-panel${w.actor.trim() ? "" : " needs-actor"}`} aria-label="Coding and provenance">
    <h2 className="rail-title">Code this passage</h2>
    <ActorField w={w} label="Human actor" />
    <label>Frozen codebook<select value={w.version?.id ?? ''} onChange={event => w.setVersionId(Number(event.target.value))}><option value="" disabled>No frozen version</option>{w.data?.codebook_versions.map(version => <option key={version.id} value={version.id}>Version {version.id} · {version.frozen_at.slice(0, 16).replace('T', ' ')} UTC</option>)}</select></label>
    {!w.version && <p className="empty-note">Create codes and freeze your codebook before assigning a code.</p>}
    <div className="selection-note"><p className="caption">{w.currentSpan ? `Selected span · characters ${w.currentSpan.start}–${w.currentSpan.end}` : 'Whole segment selected'}</p>{w.currentSpan && <><blockquote>{w.selectionText}</blockquote><Button onClick={w.clearSpan}>Use whole segment</Button></>}</div>
    <div className="code-shortcuts">{w.codingCodes.map((code, index) => <Button key={code.id} style={codeStyle(index) as CSSProperties} className="code-shortcut" disabled={w.readOnly || w.busy || !w.active || !w.actor.trim()} onClick={() => void w.assign(code.id)}><span className="caption">{index < 9 ? index + 1 : '·'}</span>{code.name}</Button>)}</div>
    {!w.readOnly && <details className="quick-code"><summary>New code from this passage</summary><form onSubmit={w.codeInVivo}><fieldset disabled={w.busy || !w.active || !w.actor.trim()}>
      <label>Code name<input name="name" required maxLength={200} placeholder={w.selectionText ? 'Name it, perhaps in the speaker’s words' : 'Name the idea in this passage'} /></label>
      <label>Definition (optional)<textarea name="definition" rows={2} /></label>
      <label className="checkbox"><input type="checkbox" name="example" defaultChecked />Keep the selected text as a positive example</label>
      <p className="caption">Creates a draft code, freezes a new codebook version that includes all current draft edits, and assigns the code to this {w.currentSpan ? 'selection' : 'segment'}.</p>
      <Button type="submit">Create, freeze and assign</Button>
    </fieldset></form></details>}
    <h3>Current assignments</h3>
    {!w.activeCodings.length && <p className="caption">No codes on this passage.</p>}
    {w.activeCodings.map(item => <div key={item.id} className="assignment"><strong>{w.eventCodeName(item)}</strong><p className="caption">characters {item.span_start}–{item.span_end} · coded by {item.actor}</p><blockquote>{w.spanText(item)}</blockquote><Button disabled={w.readOnly || w.busy} onClick={() => void w.remove(item)} aria-label={`Remove assignment of ${w.eventCodeName(item)}`}>Remove assignment</Button></div>)}
    <h3>Pending suggestions</h3>
    {!review.activeSuggestions.length && <p className="caption">No pending suggestions for this passage.</p>}
    {review.activeSuggestions.map(item => <Suggestion key={item.id} item={item} w={w} review={review} />)}
    <h3>Provenance</h3>
    <p className="caption">Decisions are retained, including removals.</p>
    {w.activeEvents.map(item => <details key={item.id} className="provenance"><summary>{item.action} · {w.eventCodeName(item)} · #{item.id}</summary><dl><dt>Actor</dt><dd>{item.actor_type} · {item.actor}</dd><dt>Span</dt><dd>{item.span_start}:{item.span_end}</dd><dt>Backend / model</dt><dd>{item.backend ?? 'manual'} / {item.model ?? '—'}{item.model_version && <> · answered by {item.model_version}</>}</dd><dt>CLI version</dt><dd>{item.cli_version ?? '—'}</dd><dt>Codebook version</dt><dd>{item.codebook_version_id}</dd><dt>Pipeline hash</dt><dd>{item.pipeline_version}</dd><dt>Prompt hash</dt><dd>{item.prompt_hash || '—'}</dd><dt>Model-reported score</dt><dd>{review.modelScore(item.score)}</dd><dt>Rationale</dt><dd>{item.rationale || '—'}</dd><dt>Review reasons</dt><dd>{review.reviewReasons(item.review_trigger).join(' · ')}</dd><dt>Reviewed by</dt><dd>{item.reviewed_by || '—'}</dd><dt>Original suggestion</dt><dd>{item.suggestion_id ?? '—'}</dd><dt>Time</dt><dd>{item.created_at}</dd></dl></details>)}
  </aside>
}
