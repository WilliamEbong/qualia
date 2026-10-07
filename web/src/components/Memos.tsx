import type { WorkspaceController } from '../lib/workspace'
import { Button } from './ui/button'

const kinds = { analytic: 'Analytic', reflexive: 'Reflexive', theme: 'Theme', method: 'Method' }

export function Memos({ w }: { w: WorkspaceController }) {
  const memo = w.editMemo
  return <section className="content-page memos-page" aria-label="Memos"><header className="section-heading"><div><p className="caption">Field notes</p><h2>Memos</h2></div><Button disabled={w.readOnly} onClick={() => w.setEditMemo(null)}>New memo</Button></header><div className="two-column"><div>
    <label>Show<select value={w.memoKind} onChange={event => w.setMemoKind(event.target.value as typeof w.memoKind)}><option value="">All memo kinds</option>{Object.entries(kinds).map(([value, label]) => <option key={value} value={value}>{label} memos</option>)}</select></label>
    <p className="caption">Analytic: interpretations and questions. Reflexive: how your background and assumptions shape what you notice. Theme: a pattern you are building, usually linked to a parent code. Method: decisions about sampling, coding and analysis.</p>
    {!w.memos.length && <div className="empty"><h3>Keep your interpretation beside the evidence</h3><p>Write a memo and optionally link it to a segment, code, case or source.</p></div>}
    {w.memos.map(item => { const history = w.memoRevisions(item.id); return <article key={item.id} className="memo-card"><div className="section-heading"><h3>{item.title}</h3><span className="caption">{kinds[item.kind ?? 'analytic'].toLowerCase()} memo</span></div><p className="preserve-lines">{item.text}</p>
      <div className="actions">{item.segment_id !== null && <Button onClick={() => w.openSegment(item.segment_id!)}>Segment {item.segment_id}</Button>}{item.code_id !== null && <span className="caption">Code: {w.codeName(item.code_id)}</span>}{item.case_id != null && <span className="caption">Case: {w.caseName(item.case_id)}</span>}{item.source_id != null && <span className="caption">Source: {w.sourceName(item.source_id)}</span>}<Button disabled={w.readOnly} onClick={() => w.setEditMemo(item)}>Edit memo</Button></div>
      {history.length > 0 && <details className="provenance"><summary>Earlier versions ({history.length})</summary>{history.map(version => <div key={version.id}><p className="caption">Replaced {version.replaced_at} · {kinds[version.kind].toLowerCase()} · {version.title}</p><p className="preserve-lines">{version.text}</p></div>)}</details>}
    </article> })}
  </div><form className="editor" key={`${memo?.id ?? 'new'}-${w.formNonce}`} onSubmit={w.saveMemo}><fieldset disabled={w.readOnly}><h3>{memo ? 'Edit memo' : 'Write memo'}</h3>
    <label>Title<input name="title" required maxLength={200} defaultValue={memo?.title ?? ''} /></label>
    <label>Kind<select name="kind" defaultValue={memo?.kind ?? 'analytic'}>{Object.entries(kinds).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
    <label>Memo<textarea name="text" rows={10} defaultValue={memo?.text ?? ''} /></label>
    <label>Linked segment<select name="segment_id" defaultValue={memo?.segment_id ?? ''}><option value="">No linked segment</option>{w.data?.segments.map(segment => <option key={segment.id} value={segment.id}>{w.sourceName(segment.source_id)} · segment {segment.ordinal + 1} (#{segment.id})</option>)}</select></label>
    <label>Linked code<select name="code_id" defaultValue={memo?.code_id ?? ''}><option value="">No linked code</option>{w.codes.map(code => <option key={code.id} value={code.id}>{code.name}</option>)}</select></label>
    <label>Linked case<select name="case_id" defaultValue={memo?.case_id ?? ''}><option value="">No linked case</option>{w.data?.cases.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
    <label>Linked source<select name="source_id" defaultValue={memo?.source_id ?? ''}><option value="">No linked source</option>{w.data?.sources.map(source => <option key={source.id} value={source.id}>{source.name}</option>)}</select></label>
    <p className="caption">Editing keeps the previous version under “Earlier versions”.</p>
    <Button type="submit" className="primary" disabled={w.readOnly || w.busy}>Save memo</Button></fieldset></form></div></section>
}
