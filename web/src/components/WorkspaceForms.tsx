import type { WorkspaceController } from '../lib/workspace'
import { Button } from './ui/button'

export function WorkspaceForms({ w }: { w: WorkspaceController }) {
  if (!w.panel) return null
  return <section className="operation-panel" aria-label={`${w.panel} options`}>
    <header className="section-heading"><h2>{w.panel === 'import' ? 'Import source material' : w.panel === 'case' ? 'Case details' : 'Export research'}</h2><Button onClick={() => w.setPanel(null)}>Close</Button></header>
    {w.panel === 'import' && <form onSubmit={w.importSource}><fieldset disabled={w.readOnly}>
      <div className="form-grid"><label>File<input type="file" name="file" accept=".txt,.md,.csv,text/plain,text/markdown,text/csv" /></label><label>Source name<input name="name" placeholder="Uses the filename if left blank" maxLength={255} /></label><label>File format<select name="format" defaultValue="txt"><option value="txt">Plain text</option><option value="md">Markdown</option><option value="csv">CSV with column mapping</option></select></label><label>Source version<select name="version_of" defaultValue=""><option value="">New source</option>{w.data?.sources.map(item => <option key={item.id} value={item.id}>New version of {item.name}</option>)}</select></label></div>
      <label>Or paste source text<textarea name="content" rows={5} placeholder="Choose a file above, or paste text here." /></label>
      <details><summary>CSV column mapping</summary><p className="caption">One row per text record. Column names are case-sensitive; attribute names are comma-separated.</p><div className="form-grid"><label>Text column<input name="text_column" defaultValue="text" /></label><label>Case column<input name="case_column" defaultValue="case" /></label><label>Speaker column<input name="speaker_column" defaultValue="speaker" /></label><label>Attribute columns<input name="attribute_columns" placeholder="region, role" /></label></div></details>
      <p className="caption">Identical source content is imported once. Changed content creates an immutable new source.</p><Button type="submit" className="primary" disabled={w.readOnly || w.busy}>Import into project</Button>
    </fieldset></form>}
    {w.panel === 'case' && <form key={w.editCase?.id ?? 'new'} onSubmit={w.saveCase}><fieldset disabled={w.readOnly}>
      <label>Case name<input name="name" required defaultValue={w.editCase?.name ?? ''} maxLength={200} /></label>
      <fieldset><legend>Add linked sources</legend><p className="caption">Existing links remain attached. This form adds links; removing links is not currently supported.</p>{w.data?.sources.map(item => <label className="checkbox" key={item.id}><input type="checkbox" name="source_ids" value={item.id} defaultChecked={w.caseSources.includes(item.id)} disabled={w.caseSources.includes(item.id)} />{item.name}</label>)}</fieldset>
      <label>Attributes, one name=value per line<textarea name="attributes" defaultValue={w.caseAttributes} rows={4} placeholder="region=north" /></label><p className="caption">Submitted values update their named attributes. Omitted attributes remain; use name= with an empty value to mark a value missing.</p><Button type="submit" className="primary" disabled={w.readOnly || w.busy}>Save case</Button>
    </fieldset></form>}
    {w.panel === 'export' && w.readOnly && <form onSubmit={w.exportData}><p>Download this licensed public snapshot, including its public excerpts and attribution. No API is contacted.</p><Button type="submit">Download public snapshot JSON</Button></form>}{w.panel === 'export' && !w.readOnly && <form onSubmit={w.exportData}><fieldset disabled={w.readOnly}>
      <label>Format<select name="format" defaultValue="json"><option value="json">JSON</option><option value="csv">CSV</option></select></label><label className="checkbox"><input type="checkbox" name="include_text" />Include source text and excerpts</label><label className="checkbox"><input type="checkbox" name="bundle" />Reproducibility bundle</label><p>Text is excluded by default. Provenance, codebook versions and decision history accompany the export. Protected benchmark data is excluded.</p><Button className="primary" type="submit" disabled={w.readOnly || w.busy}>Download export</Button>
    </fieldset></form>}
  </section>
}
