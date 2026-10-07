import type { ModelChoiceController } from '../lib/models'

export function ModelPicker({ id, label = 'Model', m, disabled, withDefault = true }: { id: string; label?: string; m: ModelChoiceController; disabled: boolean; withDefault?: boolean }) {
  return <div className="model-picker">
    <label>{label}<select value={m.choice} onChange={event => m.setChoice(event.target.value)} disabled={disabled} aria-describedby={`${id}-description`}>
      {withDefault ? <option value="">Task default · {m.defaultLabel}</option> : <option value="" disabled>Choose a model</option>}
      {m.models.map(model => <option key={model.id} value={model.id}>{model.label}</option>)}
      <option value="__custom">Other exact model ID…</option>
    </select></label>
    <p id={`${id}-description`} className="caption">{m.description}</p>
    {m.choice === '__custom' && <label>Exact model ID<input value={m.custom} onChange={event => m.setCustom(event.target.value)} disabled={disabled} placeholder="For example: claude-opus-5-5" /></label>}
  </div>
}
