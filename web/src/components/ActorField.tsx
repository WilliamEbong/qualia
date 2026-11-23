import type { WorkspaceController } from '../lib/workspace'
import { Button } from './ui/button'

// The coder's name: a field until it is set, then one line with a Change link.
export function ActorField({ w, label }: { w: WorkspaceController; label: string }) {
  const name = w.actor.trim()
  if (!w.actorOpen && name) return <p className="actor-line">Recording decisions as <strong>{name}</strong> <Button className="text-link" onClick={() => w.setActorOpen(true)}>Change</Button></p>
  return <div className="actor-field"><label>{label}<input disabled={w.readOnly} value={w.actor} onChange={event => w.setActor(event.target.value)} maxLength={200} /></label>
    <p className="caption">{name ? 'Your name or initials, saved with each decision.' : 'Enter your name or initials to start.'}</p>
    {name && !w.readOnly && <Button onClick={() => w.setActorOpen(false)}>Done</Button>}</div>
}
