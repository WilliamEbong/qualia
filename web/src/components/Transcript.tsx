import type { CSSProperties } from 'react'
import { Annotorious } from '@annotorious/react'
import { TextAnnotator } from '@recogito/react-text-annotator'
import { AnnotationSync, annotationStyle } from '../lib/annotations'
import { codeStyle } from '../lib/entities'
import type { WorkspaceController } from '../lib/workspace'
import { Button } from './ui/button'

export function Transcript({ w }: { w: WorkspaceController }) {
  return <section className="transcript-panel" aria-label="Transcript">
    <header className="section-heading"><div><p className="caption">Source {w.source?.id ?? '—'}</p><h2>{w.source?.name ?? 'Your research begins here'}</h2></div><Button onClick={() => w.setPanel('import')}>Import transcript</Button></header>
    <p className="caption">↑ / ↓ move between segments · 1–9 assign a code · select text for a span · Esc clears the span</p>
    {!w.segments.length && <div className="empty"><h3>No transcript selected</h3><p>Import a TXT, Markdown, or mapped CSV file. Your text stays in this local project.</p></div>}
    <div className="transcript">
      {w.segments.map(segment => <article id={`segment-${segment.id}`} key={`${w.slug}-${segment.id}`} tabIndex={0} aria-label={`Segment ${segment.ordinal + 1}`} className={`segment ${w.active?.id === segment.id ? 'active-segment' : ''}`} onFocus={() => w.activate(segment.id)} onPointerDown={() => w.activate(segment.id)}>
        <div className="segment-heading"><span className="caption">{segment.speaker || 'Speaker'} / {segment.ordinal + 1}</span><span className="caption">segment {segment.id}</span></div>
        <Annotorious><TextAnnotator selectionMode="all" style={annotationStyle(w.codes.map(code => code.id))}>
          <p className="segment-text" data-testid={`segment-text-${segment.id}`}>{segment.text}</p>
          <AnnotationSync segmentId={segment.id} text={segment.text} codings={segment.codings} onSpan={w.receiveSpan} />
        </TextAnnotator></Annotorious>
        <div className="segment-codes" aria-label="Current codes">{segment.codings.map(coding => <span key={coding.id} className={`code-mark ${coding.actor_type === 'model' ? 'accepted-model' : 'human'}`} style={codeStyle(w.codeIndex(coding.code_id)) as CSSProperties}>{w.eventCodeName(coding)}{coding.actor_type === 'model' && <span className="caption"> · m</span>}<span className="caption"> [{coding.span_start}:{coding.span_end}]</span></span>)}</div>
      </article>)}
    </div>
  </section>
}

export function CodingPanel({ w }: { w: WorkspaceController }) {
  return <aside className="coding-panel" aria-label="Coding and provenance">
    <h2>Code this passage</h2>
    <label>Human actor<input value={w.actor} onChange={event => w.setActor(event.target.value)} maxLength={200} /></label>
    <label>Frozen codebook<select value={w.version?.id ?? ''} onChange={event => w.setVersionId(Number(event.target.value))}><option value="" disabled>No frozen version</option>{w.data?.codebook_versions.map(version => <option key={version.id} value={version.id}>Version {version.id} · {version.frozen_at}</option>)}</select></label>
    {!w.version && <p className="empty-note">Create codes and freeze your codebook before assigning a code.</p>}
    <div className="selection-note"><p className="caption">{w.currentSpan ? `Selected span ${w.currentSpan.start}:${w.currentSpan.end}` : 'Whole segment selected'}</p>{w.currentSpan && <><blockquote>{w.selectionText}</blockquote><Button onClick={w.clearSpan}>Use whole segment</Button></>}</div>
    <div className="code-shortcuts">{w.codingCodes.map((code, index) => <Button key={code.id} style={codeStyle(index) as CSSProperties} className="code-shortcut" disabled={w.busy || !w.active || !w.actor.trim()} onClick={() => void w.assign(code.id)}><span className="caption">{index < 9 ? index + 1 : '·'}</span>{code.name}</Button>)}</div>
    <h3>Current assignments</h3>
    {!w.activeCodings.length && <p className="caption">No codes on this segment.</p>}
    {w.activeCodings.map(item => <div key={item.id} className="assignment"><strong>{w.eventCodeName(item)}</strong><p className="caption">{item.span_start}:{item.span_end} · {item.actor}</p><blockquote>{w.spanText(item)}</blockquote><Button disabled={w.busy} onClick={() => void w.remove(item)}>Remove assignment</Button></div>)}
    <h3>Provenance</h3>
    <p className="caption">Decisions are retained, including removals.</p>
    {w.activeEvents.map(item => <details key={item.id} className="provenance"><summary>{item.action} · {w.eventCodeName(item)} · #{item.id}</summary><dl><dt>Actor</dt><dd>{item.actor_type} · {item.actor}</dd><dt>Span</dt><dd>{item.span_start}:{item.span_end}</dd><dt>Backend / model</dt><dd>{item.backend ?? 'manual'} / {item.model ?? '—'}</dd><dt>CLI version</dt><dd>{item.cli_version ?? '—'}</dd><dt>Codebook version</dt><dd>{item.codebook_version_id}</dd><dt>Pipeline hash</dt><dd>{item.pipeline_version}</dd><dt>Prompt hash</dt><dd>{item.prompt_hash || '—'}</dd><dt>Time</dt><dd>{item.created_at}</dd></dl></details>)}
  </aside>
}
