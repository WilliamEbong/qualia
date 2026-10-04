import { useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'
import type { components } from '../api/schema'
import type { WorkspaceController } from './workspace'
import type { Workspace } from './entities'
import { request } from './client'
import { analysisCriteria, analysisExcerpts, analysisNumber, analysisOptions, currentAnalysis, defaultAnalysisOptions, scatterPoints } from './analysis-state'
import type { AnalysisFormat, AnalysisOptions, AnalysisReport, AnalysisResult } from './analysis-state'

function download(content: string, mediaType: string, filename: string) {
  const url = URL.createObjectURL(new Blob([content], { type: mediaType }))
  const link = document.createElement('a'); link.href = url; link.download = filename; link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export function useAnalysis(w: WorkspaceController) {
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const report = currentAnalysis(result, w.slug, w.data, w.view)
  const [loading, setLoading] = useState(false), [error, setError] = useState(''), [notice, setNotice] = useState('')
  const [drill, setDrill] = useState<{ label: string; ids: number[] } | null>(null)
  const [page, setPage] = useState(0), [correlationIndex, setCorrelationIndex] = useState(0)
  const scope = useRef({ slug: w.slug, data: w.data }), generation = useRef(0)
  const synchronizing = useRef({ pending: false, previous: null as Workspace | null })
  const nextOptions = useRef<AnalysisOptions | null>(null)
  const [workspaceRevision, setWorkspaceRevision] = useState(0)
  const applied = useRef<AnalysisOptions>(defaultAnalysisOptions)
  scope.current = { slug: w.slug, data: w.data }
  useEffect(() => {
    generation.current++; applied.current = defaultAnalysisOptions; setResult(null); setLoading(false); setError(''); setNotice(''); setDrill(null); setPage(0); setCorrelationIndex(0)
  }, [w.slug])
  const load = async (options: AnalysisOptions = applied.current) => {
    const slug = w.slug, workspace = w.data, ticket = ++generation.current
    if (!workspace) return
    setResult(null); setLoading(true); setError(''); setNotice('')
    try {
      const fresh = await request<AnalysisReport>(`projects/${encodeURIComponent(slug)}/analysis`, { method: 'POST', body: JSON.stringify(options) })
      if (scope.current.slug !== slug || scope.current.data !== workspace || generation.current !== ticket) return
      applied.current = fresh.options
      setResult({ report: fresh, workspace, slug }); setDrill(null); setPage(0); setCorrelationIndex(0)
    } catch (reason) {
      if (scope.current.slug === slug && scope.current.data === workspace && generation.current === ticket) { setResult(null); setError(reason instanceof Error ? reason.message : 'Analysis unavailable.') }
    } finally { if (scope.current.slug === slug && scope.current.data === workspace && generation.current === ticket) setLoading(false) }
  }
  const refresh = async (options: AnalysisOptions = applied.current) => {
    const slug = w.slug, ticket = ++generation.current
    synchronizing.current = { pending: true, previous: w.data }
    nextOptions.current = options
    setResult(null); setLoading(true); setError(''); setNotice('')
    try {
      await w.reload()
      if (scope.current.slug !== slug || generation.current !== ticket) return
      synchronizing.current.pending = false
      setWorkspaceRevision(value => value + 1)
    } catch (reason) {
      if (scope.current.slug !== slug || generation.current !== ticket) return
      synchronizing.current.pending = false; setLoading(false)
      setError(reason instanceof Error ? reason.message : 'Workspace refresh failed.')
    }
  }
  useEffect(() => {
    setResult(null)
    if (w.view === 'analysis' && w.slug) void refresh()
    else setLoading(false)
    return () => { generation.current++ }
  }, [w.view, w.slug])
  useEffect(() => {
    // Only the entry/Refresh action reloads the workspace. A new snapshot then
    // recalculates analysis, so calculation cannot start a reload/fetch loop.
    if (w.view === 'analysis' && w.slug && w.data && !synchronizing.current.pending
      && w.data !== synchronizing.current.previous) {
      const options = nextOptions.current ?? applied.current
      nextOptions.current = null
      void load(options)
    }
  }, [w.view, w.slug, w.data, workspaceRevision])
  const submit = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); void refresh(analysisOptions(new FormData(event.currentTarget))) }
  const fields = useMemo(() => [...new Set(w.data?.attributes.filter(item => item.case_id !== null).map(item => item.key))].sort(), [w.data])
  const select = (label: string, ids: number[]) => { setDrill({ label, ids }); setPage(0); setTimeout(() => document.getElementById('analysis-evidence')?.scrollIntoView({ block: 'start' }), 0) }
  const evidence = useMemo(() => w.data && report ? analysisExcerpts(w.data, report, drill?.ids ?? report.selected_segment_ids) : [], [w.data, report, drill])
  const correlation = report?.correlations[correlationIndex]
  const scatter = scatterPoints(correlation?.points ?? [])
  const maxFrequency = Math.max(1, ...report?.frequencies.map(row => row.segment_count) ?? [])
  const maxPair = Math.max(1, ...report?.pairs.map(row => row.count) ?? [])
  const bars = (report?.frequencies ?? []).map((row, index) => ({ ...row, y: 52 + index * 48, width: row.segment_count / maxFrequency * 350 }))
  const pairLookup = new Map((report?.pairs ?? []).map(pair => [`${Math.min(pair.left_code_id, pair.right_code_id)}:${Math.max(pair.left_code_id, pair.right_code_id)}`, pair]))
  const heatRows = (report?.frequencies ?? []).map(left => ({ ...left, cells: (report?.frequencies ?? []).map(right => {
    const pair = pairLookup.get(`${Math.min(left.code_id, right.code_id)}:${Math.max(left.code_id, right.code_id)}`)
    return { right, pair, opacity: pair ? .08 + pair.count / maxPair * .42 : 0 }
  }) }))
  const selectCase = (id: number) => {
    const sources = new Set(w.data?.source_cases.filter(item => item.case_id === id).map(item => item.source_id))
    select(`Case ${w.data?.cases.find(item => item.id === id)?.name ?? id}`, w.data?.segments.filter(segment => sources.has(segment.source_id)).map(segment => segment.id) ?? [])
  }
  const activateChart = (event: KeyboardEvent<SVGGElement>, action: () => void) => {
    if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); action() }
  }
  const exportReport = async (format: AnalysisFormat) => {
    if (!report) return
    const slug = w.slug, ticket = generation.current
    setError(''); setNotice('')
    try {
      const input: components['schemas']['AnalysisExportRequest'] = { options: report.options, format, expected_input_hash: report.input_hash }
      const result = await request<components['schemas']['ExportResult']>(`projects/${encodeURIComponent(slug)}/analysis/export`, { method: 'POST', body: JSON.stringify(input) })
      if (scope.current.slug !== slug || generation.current !== ticket) return
      download(result.content, result.media_type, result.filename); setNotice(`Downloaded ${result.filename}.`)
    } catch (reason) { if (scope.current.slug === slug && generation.current === ticket) setError(reason instanceof Error ? reason.message : 'Export unavailable.') }
  }
  const exportChart = (id: string, title: string) => {
    const svg = document.getElementById(id)
    if (!(svg instanceof SVGSVGElement)) return
    const copy = svg.cloneNode(true) as SVGSVGElement
    copy.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
    // Resolve theme colors so the downloaded standalone SVG remains readable.
    const originals = [svg, ...svg.querySelectorAll('*')], copies = [copy, ...copy.querySelectorAll('*')]
    originals.forEach((node, index) => { const style = getComputedStyle(node); for (const key of ['fill', 'stroke', 'color', 'font-family', 'font-size']) copies[index].setAttribute(key, style.getPropertyValue(key)) })
    const background = document.createElementNS('http://www.w3.org/2000/svg', 'rect')
    background.setAttribute('width', '100%'); background.setAttribute('height', '100%'); background.setAttribute('fill', getComputedStyle(svg).backgroundColor)
    copy.insertBefore(background, copy.firstChild)
    download(new XMLSerializer().serializeToString(copy), 'image/svg+xml', `qualia-${title}.svg`)
    setNotice(`Downloaded ${title} chart.`)
  }
  return { report, appliedOptions: applied.current, loading, error, notice, submit, reload: () => void refresh(), fields, select, selectCase, drill,
    evidence: evidence.slice(page * 25, (page + 1) * 25), evidenceCount: evidence.length, page, setPage,
    correlation, correlationIndex, setCorrelationIndex, scatter, exportReport, exportChart, number: analysisNumber,
    criteria: report ? analysisCriteria(report.options) : '',
    bars, barHeight: Math.max(140, bars.length * 48 + 100), heatRows, activateChart,
  }
}
export type AnalysisController = ReturnType<typeof useAnalysis>
