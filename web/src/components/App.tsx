import { useAnalysis } from '../lib/analysis'
import { Analysis } from './Analysis'
import { useWorkspace } from '../lib/workspace'
import { useReview } from '../lib/review'
import { useProposals } from '../lib/proposals'
import { ReviewQueue } from './Review'
import type { View } from '../lib/entities'
import { useBenchmarks, useEvaluation } from '../lib/evaluation'
import { useTheme } from '../lib/theme'
import { Evaluation } from './Evaluation'
import { useExperiments } from '../lib/experiments'
import { Experiments } from './Experiments'
import { Landing } from './Landing'
import { Transcript, CodingPanel } from './Transcript'
import { Codebook } from './Codebook'
import { Memos } from './Memos'
import { Retrieval, Matrix } from './Retrieval'
import { WorkspaceForms } from './WorkspaceForms'
import { Button } from './ui/button'

export function App() {
  const w = useWorkspace()
  const review = useReview(w)
  const proposals = useProposals(w, review.availability)
  const benchmarks = useBenchmarks(w)
  const evaluation = useEvaluation(w, review, benchmarks)
  const theme = useTheme()
  const experiments = useExperiments(w, review, benchmarks)
  const analysis = useAnalysis(w)
  const create = !w.readOnly && <details className="project-create"><summary>New project</summary><form onSubmit={w.createProject}><label>Project identifier<input name="name" required pattern="[a-z0-9]+(-[a-z0-9]+)*" placeholder="field-study" maxLength={80} /></label><p className="caption">Lowercase words separated by hyphens.</p><Button type="submit" disabled={w.busy}>Create local project</Button></form></details>
  return <div className={`app-shell${w.readOnly ? ' read-only' : ''}`}><a className="skip-link" href="#main-content">Skip to research workspace</a>
    <header className="app-header"><div className="brand"><h1>Qualia</h1><p className="caption">Qualitative coding you can audit.</p></div><div className="project-controls"><label>Local project<select value={w.slug} disabled={w.busy} onChange={event => w.chooseProject(event.target.value)}><option value="" disabled>Choose a project</option>{w.projects.map(project => <option key={project.slug} value={project.slug}>{project.name}</option>)}</select></label>{create}</div><span className="header-wide"><Button onClick={theme.toggle} aria-pressed={theme.theme === 'dark'}>{theme.label}</Button></span><details className="header-more"><summary aria-label="Theme and new project">⋯</summary><div><Button onClick={theme.toggle} aria-pressed={theme.theme === 'dark'}>{theme.label}</Button>{create}</div></details><span className="local-status caption">{w.readOnly ? 'Read-only public snapshot · no API or AI' : 'Local workspace · external AI off by default'}</span></header>
    <div className="messages"><div role="alert">{w.error && <p className="error">Error: {w.error}</p>}</div><div aria-live="polite">{w.notice && <p className="notice">{w.notice}</p>}{w.busy && <p className="caption">Working…</p>}</div></div>
    {w.loading ? <main id="main-content" className="landing workspace-loading"><p role="status">Opening your local research workspace…</p></main> : !w.slug ? <main id="main-content"><Landing w={w} /></main> : !w.data ? <main id="main-content" className="landing"><h2>Project unavailable</h2><Button onClick={() => void w.run(async () => { await w.reload() })}>Retry opening project</Button></main> : <>
      {w.readOnly && <p className="demo-notice" role="note">Read-only public demo with real, licensed interview data. Browse the coding, evidence and results; editing, importing and AI need Qualia on your own computer.</p>}
      <div className="nav-compact"><label>View<select value={w.view} onChange={event => w.setView(event.target.value as View)}>{([['home', 'Home'], ['workspace', 'Workspace'], ['codebook', 'Codebook'], ['memos', 'Memos'], ['retrieval', 'Retrieval'], ['matrix', 'Matrix'], ['review', `Review (${review.suggestions.length})`], ['analysis', 'Analysis'], ['evaluation', 'Evaluation'], ['experiments', 'Experiments']] as Array<[View, string]>).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><Button className="export-action" onClick={() => w.setPanel('export')}>Export</Button></div>
      <nav className="workspace-nav" aria-label="Research views"><Button aria-current={w.view === 'home' ? 'page' : undefined} onClick={() => w.setView('home')}>Home</Button><Button aria-current={w.view === 'workspace' ? 'page' : undefined} onClick={() => w.setView('workspace')}>Workspace</Button><Button aria-current={w.view === 'codebook' ? 'page' : undefined} onClick={() => w.setView('codebook')}>Codebook</Button><Button aria-current={w.view === 'memos' ? 'page' : undefined} onClick={() => w.setView('memos')}>Memos</Button><Button aria-current={w.view === 'retrieval' ? 'page' : undefined} onClick={() => w.setView('retrieval')}>Retrieval</Button><Button aria-current={w.view === 'matrix' ? 'page' : undefined} onClick={() => w.setView('matrix')}>Matrix</Button><Button aria-current={w.view === 'review' ? 'page' : undefined} onClick={() => w.setView('review')}>Review ({review.suggestions.length})</Button><Button aria-current={w.view === 'analysis' ? 'page' : undefined} onClick={() => w.setView('analysis')}>Analysis</Button><Button aria-current={w.view === 'evaluation' ? 'page' : undefined} onClick={() => w.setView('evaluation')}>Evaluation</Button><Button aria-current={w.view === 'experiments' ? 'page' : undefined} onClick={() => w.setView('experiments')}>Experiments</Button><Button className="export-action" onClick={() => w.setPanel('export')}>Export</Button></nav>
      <WorkspaceForms w={w} />
      <main id="main-content" tabIndex={-1}>{w.view === 'home' && <Landing w={w} />}
        {w.view === 'workspace' && <div className="workspace-grid"><aside className="source-panel" aria-label="Sources and cases"><div className="section-heading"><h2>Sources</h2><span className="caption">{w.sources.length}</span></div><Button disabled={w.readOnly} onClick={() => w.setPanel('import')}>Import source</Button><label>Filter by case<select value={w.caseId ?? ''} onChange={event => w.setCaseId(Number(event.target.value) || null)}><option value="">All cases</option>{w.data.cases.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><ul className="source-list">{w.sources.map(source => <li key={source.id}><Button className={w.source?.id === source.id ? 'selected-source' : ''} onClick={() => w.selectSource(source.id)}>{source.name}</Button></li>)}</ul><h3>Cases</h3><Button disabled={w.readOnly} onClick={() => { w.setEditCase(null); w.setPanel('case') }}>Create case</Button>{w.data.cases.map(item => <div className="case-row" key={item.id}><span>{item.name}</span><Button disabled={w.readOnly} aria-label={`Edit case ${item.name}`} onClick={() => { w.setEditCase(item); w.setPanel('case') }}>Edit</Button></div>)}<h3>Code tree</h3><ul className="code-tree">{w.codes.map(code => <li key={code.id}><span className="caption">{code.depth ? '↳ ' : ''}</span>{code.name}<span className="caption">{code.status === 'archived' ? ' · archived' : ''}</span></li>)}</ul><Button onClick={() => w.setView('codebook')}>Manage codebook</Button><h3>Memos</h3>{w.data.memos.map(memo => <Button key={memo.id} className="memo-link" onClick={() => { if (!w.readOnly) w.setEditMemo(memo); w.setView('memos') }}>{memo.title}</Button>)}</aside><Transcript w={w} review={review} /><CodingPanel w={w} review={review} /></div>}
        {w.view === 'codebook' && <Codebook w={w} proposals={proposals} />}{w.view === 'memos' && <Memos w={w} />}{w.view === 'retrieval' && <Retrieval w={w} />}{w.view === 'matrix' && <Matrix w={w} />}{w.view === 'review' && <ReviewQueue w={w} review={review} />}{w.view === 'analysis' && <Analysis w={w} analysis={analysis} />}{w.view === 'evaluation' && <Evaluation w={w} review={review} evaluation={evaluation} benchmarks={benchmarks} />}{w.view === 'experiments' && <Experiments w={w} review={review} experiments={experiments} />}
      </main>
    </>}
    <footer className="app-footer caption">Qualia · Researcher controls the methodology. Every code keeps its evidence.</footer>
  </div>
}
