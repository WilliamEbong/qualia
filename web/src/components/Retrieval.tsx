import type { CSSProperties } from 'react'
import type { WorkspaceController } from '../lib/workspace'
import { Button } from './ui/button'

export function Retrieval({ w }: { w: WorkspaceController }) {
  return <section className="content-page" aria-label="Retrieved excerpts"><header className="section-heading"><div><p className="caption">Evidence across sources</p><h2>Retrieval</h2></div><span className="caption">{w.retrievalSegmentCount} distinct segments · {w.retrieval.length} coded excerpts</span></header>
    <div className="filters"><label>Code<select value={w.retrievalCode ?? ''} onChange={event => w.setRetrievalCode(Number(event.target.value) || null)}><option value="">All codes</option>{w.codes.map(code => <option key={code.id} value={code.id}>{code.name}</option>)}</select></label><label>Case<select value={w.retrievalCase ?? ''} onChange={event => w.setRetrievalCase(Number(event.target.value) || null)}><option value="">All cases</option>{w.data?.cases.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label></div>
    {w.queryLoading ? <p role="status">Loading excerpts…</p> : !w.retrieval.length ? <div className="empty"><h3>No matching coded segments</h3><p>Assign a code to a transcript, or change the filters.</p></div> : w.retrieval.map((item, index) => <article className="retrieval-card" key={`${item.segment_id}-${index}`}><p className="caption">{item.source_name ?? `Source ${item.source_id ?? '—'}`} · segment {item.segment_id}</p><p><strong>{w.eventCodeName(item)}</strong> <span className="caption">· codebook version {item.codebook_version_id}</span></p><blockquote>{item.excerpt}</blockquote><Button onClick={() => w.openSegment(item.segment_id)}>Open in transcript</Button></article>)}
  </section>
}

export function Matrix({ w }: { w: WorkspaceController }) {
  const matrix = w.matrixView
  return <section className="content-page" aria-label="Code by case matrix"><header className="section-heading"><div><p className="caption">Compare cases</p><h2>Code-by-case matrix</h2></div></header><p>Each cell counts distinct currently coded segments. A segment linked to multiple cases counts in each case. Select a cell to inspect its excerpts.</p>
    {w.queryLoading && <p role="status">Loading matrix…</p>}
    {!w.codes.length || !w.data?.cases.length ? <div className="empty"><h3>Your matrix needs codes and cases</h3><p>Create a case linked to a source and code a segment to see counts here.</p></div> : <div className="table-scroll" tabIndex={0} aria-label="Scrollable matrix"><table><thead>{matrix.table.getHeaderGroups().map(group => <tr key={group.id}>{group.headers.map(header => <th key={header.id} scope="col"><matrix.table.FlexRender header={header} /></th>)}</tr>)}</thead><tbody>{matrix.rows.map(row => <tr key={row.id}>{row.cells.map(cell => cell.isCode ? <th key={cell.id} scope="row"><matrix.table.FlexRender cell={cell.cell} /></th> : <td key={cell.id}><button className="matrix-cell" style={cell.style as CSSProperties} onClick={cell.select} aria-label={cell.label}><matrix.table.FlexRender cell={cell.cell} /></button></td>)}</tr>)}</tbody></table></div>}
  </section>
}
