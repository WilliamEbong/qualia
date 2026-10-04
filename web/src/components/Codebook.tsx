import type { CSSProperties } from 'react'
import type { WorkspaceController } from '../lib/workspace'
import { exampleLines } from '../lib/workspace'
import { thresholdCaption } from '../lib/review-state'
import { Button } from './ui/button'

export function Codebook({ w }: { w: WorkspaceController }) {
  return <section className="content-page codebook-page" aria-label="Codebook">
    <header className="section-heading"><div><p className="caption">Researcher-controlled methodology</p><h2>Codebook</h2></div><Button disabled={w.readOnly || w.busy || !w.codes.length} onClick={() => void w.freeze()}>Freeze codebook</Button></header>
    <p>Draft edits apply to the next frozen version. Existing coding always retains the version used for its decision.</p>
    <div className="two-column"><div>
      {!w.codes.length && <div className="empty"><h3>No codes yet</h3><p>Describe the first idea you want to track, then freeze a version to begin coding.</p></div>}
      {w.codes.map(code => <article key={code.id} className="code-card" style={{ '--depth': code.depth } as CSSProperties}><div className="section-heading"><h3>{code.name}</h3><span className="caption">{code.status}</span></div>{thresholdCaption(w.data?.routing, code.id) && <p className="caption">{thresholdCaption(w.data?.routing, code.id)}</p>}<p className="code-definition">{code.definition || 'No definition supplied.'}</p><dl className="code-fields"><dt>Include</dt><dd>{code.include || '—'}</dd><dt>Exclude</dt><dd>{code.exclude || '—'}</dd><dt>Positive examples</dt><dd className="preserve-lines">{code.positive || '—'}</dd><dt>Negative examples</dt><dd className="preserve-lines">{code.negative || '—'}</dd></dl><Button disabled={w.readOnly} onClick={() => w.setEditCode(code)}>Edit {code.name}</Button></article>)}
      <h3>Frozen versions</h3>{w.data?.codebook_versions.map(version => <details key={version.id} className="version"><summary>cb_v{version.id} · frozen {version.frozen_at}</summary><p className="caption hash">{version.hash}</p><pre>{version.snapshot_json}</pre></details>)}
    </div><form className="editor" key={w.editCode?.id ?? 'new'} onSubmit={w.saveCode}><fieldset disabled={w.readOnly}>
      <div className="section-heading"><h3>{w.editCode ? `Edit ${w.editCode.name}` : 'Create code'}</h3>{w.editCode && <Button onClick={() => w.setEditCode(null)}>New code</Button>}</div>
      <label>Name<input name="name" required maxLength={200} defaultValue={w.editCode?.name ?? ''} /></label><label>Parent code<select name="parent_id" defaultValue={w.editCode?.parent_id ?? ''}><option value="">No parent</option>{w.codes.map(code => <option key={code.id} value={code.id} disabled={code.id === w.editCode?.id}>{code.name}</option>)}</select></label>
      <label>Definition<textarea name="definition" rows={3} defaultValue={w.editCode?.definition ?? ''} /></label><label>Include<textarea name="include" rows={2} defaultValue={w.editCode?.include ?? ''} /></label><label>Exclude<textarea name="exclude" rows={2} defaultValue={w.editCode?.exclude ?? ''} /></label><label>Positive examples, one per line<textarea name="examples_pos" rows={2} defaultValue={exampleLines(w.editCode?.examples_pos ?? '[]')} /></label><label>Negative examples, one per line<textarea name="examples_neg" rows={2} defaultValue={exampleLines(w.editCode?.examples_neg ?? '[]')} /></label>
      <label>Status<select name="status" defaultValue={w.editCode?.status ?? 'active'}><option value="active">Active</option><option value="archived">Archived</option></select></label><p className="caption">Archiving retains historical references.</p><Button type="submit" className="primary" disabled={w.readOnly || w.busy}>Save draft code</Button>
    </fieldset></form></div>
  </section>
}
