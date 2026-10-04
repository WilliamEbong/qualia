import type { WorkspaceController } from '../lib/workspace'
import { Button } from './ui/button'

export function Landing({ w }: { w: WorkspaceController }) {
  return <section className="content-page home-page" aria-label="Qualia home"><div className="home-introduction"><p className="caption">{w.readOnly ? 'Read-only public demonstration' : 'Local research workspace'}</p><h2>Qualitative coding you can audit.</h2><p>Read the transcript, trace each coding decision, and inspect the evidence behind an experiment.</p><p>{w.readOnly ? 'Explore a licensed public snapshot. Editing and AI are unavailable in this demonstration.' : 'Your sources, codebook and interpretation stay together in a local project. You decide when to use AI and which suggestions to accept.'}</p></div>
    <h3>Project catalogue</h3>{!w.projects.length && <div className="empty"><p>No projects yet. Use New project above to create your first local workspace.</p></div>}<div className="project-catalogue">{w.projects.map(project => <article className="project-drawer" key={project.slug}><p className="caption">{project.slug}</p><h3>{project.name}</h3><Button onClick={() => { w.chooseProject(project.slug); w.setView('workspace') }}>Open {project.name}</Button></article>)}</div>
    {w.attribution && <aside className="snapshot-attribution" aria-label="Public dataset attribution"><h3>About this snapshot</h3><p>{w.attribution.dataset} · {w.attribution.license}</p>{w.attribution.note && <p>{w.attribution.note}</p>}<p className="caption">{w.attribution.sources.join(' · ')}</p></aside>}
  </section>
}
