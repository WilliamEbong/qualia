import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import type { components } from '../api/schema'
import { request } from './client'
import { useMatrix } from './matrix'
import { codeDepth, eventCodeName, frozenCodes, isEditingTarget, orderedCodes, segmentText, shortcut } from './entities'
import type { Case, Code, Coding, MatrixCell, Memo, Project, Retrieval, Span, View, Workspace } from './entities'

const field = (form: FormData, name: string) => String(form.get(name) ?? '').trim()
const idField = (form: FormData, name: string) => Number(form.get(name)) || null
const lines = (value: string) => value.split(/\r?\n/).map(item => item.trim()).filter(Boolean)
export const exampleLines = (value: string) => { try { return (JSON.parse(value) as string[]).join('\n') } catch { return value } }

export function useWorkspace() {
  const [projects, setProjects] = useState<Project[]>([])
  const [slug, setSlug] = useState(new URLSearchParams(location.search).get('project') ?? '')
  const [data, setData] = useState<Workspace | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [view, setView] = useState<View>('workspace')
  const [sourceId, setSourceId] = useState<number | null>(null)
  const [caseId, setCaseId] = useState<number | null>(null)
  const [activeId, setActiveId] = useState<number | null>(null)
  const [span, setSpan] = useState<Span | null>(null)
  const [versionId, setVersionId] = useState<number | null>(null)
  const [actor, setActor] = useState('researcher')
  const [panel, setPanel] = useState<'import' | 'case' | 'export' | null>(null)
  const [editCode, setEditCode] = useState<Code | null>(null)
  const [editMemo, setEditMemo] = useState<Memo | null>(null)
  const [editCase, setEditCase] = useState<Case | null>(null)
  const [retrievalCode, setRetrievalCode] = useState<number | null>(null)
  const [retrievalCase, setRetrievalCase] = useState<number | null>(null)
  const [retrieval, setRetrieval] = useState<Retrieval[]>([])
  const [queryLoading, setQueryLoading] = useState(false)
  const [matrix, setMatrix] = useState<MatrixCell[]>([])
  const mutationLock = useRef(false)
  const scope = useRef(slug)
  scope.current = slug

  const chooseProject = useCallback((value: string) => {
    setSlug(value); setData(null); setSourceId(null); setCaseId(null); setActiveId(null); setSpan(null); setVersionId(null)
    setEditCode(null); setEditMemo(null); setEditCase(null); setPanel(null); setView('workspace'); setError(''); setNotice('')
    setRetrievalCode(null); setRetrievalCase(null); setRetrieval([]); setMatrix([]); setQueryLoading(false)
    const url = new URL(location.href)
    url.searchParams.set('project', value)
    history.replaceState(null, '', url)
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    request<Project[]>('projects', { signal: controller.signal }).then(items => {
      setProjects(items)
      if (!slug && items.length) chooseProject(items[0].slug)
      else if (!slug) setLoading(false)
    }).catch(reason => { if (!controller.signal.aborted) { setError(String(reason.message ?? reason)); setLoading(false) } })
    return () => controller.abort()
  }, [])

  const reload = useCallback(async () => {
    const value = await request<Workspace>(`projects/${encodeURIComponent(slug)}`)
    if (scope.current === slug) setData(value)
    return value
  }, [slug])

  useEffect(() => {
    if (!slug) return
    let current = true
    setLoading(true); setError('')
    reload().catch(reason => { if (current) setError(reason.message) }).finally(() => { if (current) setLoading(false) })
    return () => { current = false }
  }, [reload])

  const run = useCallback(async (action: () => Promise<void>) => {
    if (mutationLock.current) return
    mutationLock.current = true; setBusy(true); setError(''); setNotice('')
    try { await action() } catch (reason) { setError(reason instanceof Error ? reason.message : 'The operation could not be completed.') }
    finally { mutationLock.current = false; setBusy(false) }
  }, [])

  const mutate = useCallback(async <T,>(route: string, body?: T, method = 'POST') => {
    return request<components['schemas']['IdResult']>(`projects/${encodeURIComponent(slug)}/${route}`, { method, body: body === undefined ? undefined : JSON.stringify(body) })
  }, [slug])

  const sources = useMemo(() => data?.sources.filter(source => caseId === null || data.source_cases.some(link => link.source_id === source.id && link.case_id === caseId)) ?? [], [data, caseId])
  const source = sources.find(item => item.id === sourceId) ?? sources[0]
  const segments = useMemo(() => data?.segments.filter(item => item.source_id === source?.id).sort((a, b) => a.ordinal - b.ordinal) ?? [], [data, source?.id])
  const active = segments.find(item => item.id === activeId) ?? segments[0]
  const activeText = data && active ? segmentText(data, active) : ''
  const currentSpan = span?.segmentId === active?.id ? span : null
  const version = data?.codebook_versions.find(item => item.id === versionId) ?? data?.codebook_versions.at(-1)
  const codes = useMemo(() => orderedCodes(data?.codes ?? []), [data])
  const codingCodes = useMemo(() => orderedCodes(frozenCodes(version)).filter(item => item.status === 'active'), [version])
  const activeCodings = useMemo(() => data?.current_codings.filter(item => item.segment_id === active?.id) ?? [], [data, active?.id])
  const activeEvents = useMemo(() => data?.coding_events.filter(item => item.segment_id === active?.id).reverse() ?? [], [data, active?.id])
  const segmentViews = useMemo(() => segments.map(segment => ({ ...segment, text: data ? segmentText(data, segment) : '', codings: data?.current_codings.filter(item => item.segment_id === segment.id) ?? [] })), [data, segments])
  const codeViews = useMemo(() => codes.map(code => ({ ...code, depth: codeDepth(code, codes), positive: exampleLines(code.examples_pos), negative: exampleLines(code.examples_neg) })), [codes])

  const activate = useCallback((id: number) => {
    setActiveId(id)
    setSpan(value => value?.segmentId === id ? value : null)
  }, [])
  const receiveSpan = useCallback((value: Span) => { setActiveId(value.segmentId); setSpan(value) }, [])
  const selectSource = (id: number) => { setSourceId(id); setActiveId(null); setSpan(null); setView('workspace') }

  const assign = useCallback((codeId: number) => run(async () => {
    if (!active || !version) throw new Error('Choose a segment and freeze a codebook before coding.')
    const input: components['schemas']['CodingInput'] = { segment_id: active.id, code_id: codeId, span_start: currentSpan?.start ?? 0, span_end: currentSpan?.end ?? Array.from(activeText).length, codebook_version_id: version.id, action: 'assign', actor }
    await mutate('coding', input); await reload(); setNotice('Code assigned. The decision is saved in provenance.')
  }), [active, version, currentSpan, activeText, actor, mutate, reload, run])

  const remove = (item: Coding) => run(async () => {
    const input: components['schemas']['CodingInput'] = { segment_id: item.segment_id, code_id: item.code_id, span_start: item.span_start, span_end: item.span_end, codebook_version_id: item.codebook_version_id, action: 'remove', actor }
    await mutate('coding', input); await reload(); setNotice('Assignment removed; its history remains.')
  })

  useEffect(() => {
    const handle = (event: KeyboardEvent) => {
      if (view !== 'workspace' || panel || isEditingTarget(event.target) || event.ctrlKey || event.metaKey || event.altKey || busy || !segments.length) return
      const action = shortcut(event.key, segments.findIndex(item => item.id === active?.id), segments.length)
      if (action.index !== undefined) {
        event.preventDefault(); const next = segments[action.index]; activate(next.id)
        document.getElementById(`segment-${next.id}`)?.focus({ preventScroll: true })
        document.getElementById(`segment-${next.id}`)?.scrollIntoView({ block: 'nearest' })
      } else if (action.codeIndex !== undefined && codingCodes[action.codeIndex]) {
        event.preventDefault(); void assign(codingCodes[action.codeIndex].id)
      } else if (event.key === 'Escape') setSpan(null)
    }
    document.addEventListener('keydown', handle)
    return () => document.removeEventListener('keydown', handle)
  }, [view, panel, busy, segments, active?.id, codingCodes, activate, assign])

  useEffect(() => {
    if (!slug || !data || (view !== 'retrieval' && view !== 'matrix')) return
    const controller = new AbortController()
    setQueryLoading(true)
    const query = new URLSearchParams()
    if (retrievalCode !== null) query.set('code_id', String(retrievalCode))
    if (retrievalCase !== null) query.set('case_id', String(retrievalCase))
    const route = view === 'matrix' ? 'matrix' : `retrieval?${query}`
    request<MatrixCell[] | Retrieval[]>(`projects/${encodeURIComponent(slug)}/${route}`, { signal: controller.signal }).then(value => {
      if (controller.signal.aborted) return
      if (view === 'matrix') setMatrix(value as MatrixCell[])
      else setRetrieval(value as Retrieval[])
    }).catch(reason => { if (!controller.signal.aborted) setError(reason.message) }).finally(() => { if (!controller.signal.aborted) setQueryLoading(false) })
    return () => controller.abort()
  }, [slug, data, view, retrievalCode, retrievalCase])

  const createProject = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); const form = new FormData(event.currentTarget)
    void run(async () => {
      const project = await request<Project>('projects', { method: 'POST', body: JSON.stringify({ name: field(form, 'name') }) })
      const all = await request<Project[]>('projects'); setProjects(all); chooseProject(project.slug)
    })
  }

  const importSource = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); const form = new FormData(event.currentTarget)
    void run(async () => {
      const file = form.get('file') as File | null
      const content = file?.size ? await file.text() : String(form.get('content') ?? '')
      const input: components['schemas']['ImportInput'] = { name: field(form, 'name') || file?.name || 'Untitled transcript', content, format: field(form, 'format') as 'txt' | 'md' | 'csv', text_column: field(form, 'text_column') || 'text', case_column: field(form, 'case_column') || 'case', speaker_column: field(form, 'speaker_column') || 'speaker', attribute_columns: field(form, 'attribute_columns').split(',').map(item => item.trim()).filter(Boolean), version_of: idField(form, 'version_of') }
      const result = await request<components['schemas']['ImportResult']>(`projects/${encodeURIComponent(slug)}/import`, { method: 'POST', body: JSON.stringify(input) })
      await reload(); setNotice(`${result.new_sources} new sources · ${result.new_segments} new segments`)
      setPanel(null); setCaseId(null); if (result.source_ids[0]) selectSource(result.source_ids[0])
    })
  }

  const saveCode = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); const form = new FormData(event.currentTarget)
    void run(async () => {
      const input: components['schemas']['CodeInput'] = { name: field(form, 'name'), parent_id: idField(form, 'parent_id'), definition: field(form, 'definition'), include: field(form, 'include'), exclude: field(form, 'exclude'), examples_pos: lines(field(form, 'examples_pos')), examples_neg: lines(field(form, 'examples_neg')), status: field(form, 'status') as 'active' | 'archived' }
      await mutate(editCode ? `codes/${editCode.id}` : 'codes', input, editCode ? 'PUT' : 'POST')
      await reload(); setEditCode(null); setNotice('Draft code saved. Freeze a new version to use this definition for coding.')
    })
  }
  const freeze = () => run(async () => { const result = await mutate('codebook/freeze'); await reload(); setVersionId(result.id); setNotice(`Codebook version ${result.id} frozen.`) })

  const saveMemo = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); const form = new FormData(event.currentTarget)
    void run(async () => {
      const input: components['schemas']['MemoInput'] = { title: field(form, 'title'), text: String(form.get('text') ?? ''), segment_id: idField(form, 'segment_id'), code_id: idField(form, 'code_id') }
      await mutate(editMemo ? `memos/${editMemo.id}` : 'memos', input, editMemo ? 'PUT' : 'POST'); await reload(); setEditMemo(null); setNotice('Memo saved.')
    })
  }

  const saveCase = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); const form = new FormData(event.currentTarget)
    void run(async () => {
      const attributes: Record<string, string> = {}
      for (const line of lines(field(form, 'attributes'))) {
        const separator = line.indexOf('=')
        if (separator < 1) throw new Error('Write case attributes as name=value, one per line.')
        attributes[line.slice(0, separator).trim()] = line.slice(separator + 1).trim()
      }
      const input: components['schemas']['CaseInput'] = { name: field(form, 'name'), source_ids: form.getAll('source_ids').map(Number), attributes }
      await mutate(editCase ? `cases/${editCase.id}` : 'cases', input, editCase ? 'PUT' : 'POST'); await reload(); setPanel(null); setEditCase(null); setNotice('Case saved.')
    })
  }

  const exportData = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); const form = new FormData(event.currentTarget)
    void run(async () => {
      const query = new URLSearchParams({ format: field(form, 'format'), no_text: String(form.get('include_text') !== 'on') })
      if (form.get('bundle') === 'on') query.set('bundle', 'reproducibility')
      const result = await request<components['schemas']['ExportResult']>(`projects/${encodeURIComponent(slug)}/export?${query}`)
      const url = URL.createObjectURL(new Blob([result.content], { type: result.media_type }))
      const link = document.createElement('a'); link.href = url; link.download = result.filename; link.click()
      setTimeout(() => URL.revokeObjectURL(url), 1000); setPanel(null); setNotice(`Downloaded ${result.filename}.`)
    })
  }

  const drillDown = useCallback((code: number, case_: number) => { setRetrievalCode(code); setRetrievalCase(case_); setView('retrieval') }, [])
  const openSegment = (id: number) => {
    const segment = data?.segments.find(item => item.id === id)
    if (segment) { setCaseId(null); setSourceId(segment.source_id); setActiveId(id); setSpan(null); setView('workspace'); setTimeout(() => document.getElementById(`segment-${id}`)?.scrollIntoView({ block: 'center' }), 100) }
  }
  const matrixView = useMatrix(codeViews, data?.cases ?? [], matrix, drillDown)

  return { projects, slug, data, loading, busy, error, notice, view, setView, chooseProject, createProject, run, reload,
    sources, source, segments: segmentViews, active, activeText, currentSpan, activate, receiveSpan, selectSource, caseId, setCaseId,
    codes: codeViews, codingCodes, version, setVersionId, activeCodings, activeEvents, actor, setActor, assign, remove,
    clearSpan: () => setSpan(null), panel, setPanel, editCode, setEditCode, editMemo, setEditMemo, editCase, setEditCase,
    importSource, saveCode, freeze, saveMemo, saveCase, exportData, retrieval, retrievalCode, setRetrievalCode, retrievalCase, setRetrievalCase,
    queryLoading, matrix, matrixView, drillDown, openSegment,
    retrievalSegmentCount: new Set(retrieval.map(item => item.segment_id)).size,
    caseAttributes: data?.attributes.filter(item => item.case_id === editCase?.id).map(item => `${item.key}=${item.value}`).join('\n') ?? '',
    caseSources: data?.source_cases.filter(item => item.case_id === editCase?.id).map(item => item.source_id) ?? [],
    codeName: (id: number) => codes.find(item => item.id === id)?.name ?? `Code ${id}`,
    eventCodeName: (item: Coding) => eventCodeName(item, data?.codebook_versions ?? []),
    codeIndex: (id: number) => Math.max(0, codes.findIndex(item => item.id === id)),
    spanText: (item: Coding) => Array.from(activeText).slice(item.span_start, item.span_end).join(''),
    selectionText: currentSpan ? Array.from(activeText).slice(currentSpan.start, currentSpan.end).join('') : '',
  }
}
export type WorkspaceController = ReturnType<typeof useWorkspace>
