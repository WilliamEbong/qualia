import { useEffect, useMemo, useState } from 'react'
import type { WorkspaceController } from './workspace'
import { experimentHistory } from './experiment-state'
import type { ExperimentRecord } from './experiment-state'

export function useExperiments(w: WorkspaceController) {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  useEffect(() => setSelectedId(null), [w.slug])
  const history = useMemo(() => experimentHistory((w.data?.experiments ?? []) as ExperimentRecord[]), [w.data])
  const selected = history.find(item => item.id === selectedId) ?? history[0]
  return { history, selected, select: setSelectedId }
}
export type ExperimentsController = ReturnType<typeof useExperiments>
