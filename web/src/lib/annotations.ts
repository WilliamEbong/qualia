import { useEffect, useMemo } from 'react'
import { useAnnotator } from '@annotorious/react'
import type { RecogitoTextAnnotator, TextAnnotation } from '@recogito/react-text-annotator'
import type { HighlightStyleExpression } from '@recogito/text-annotator'
import { codingAnnotation, annotationSpan } from './annotation-offsets'
import type { Coding, Span } from './entities'

export function useAnnotationSync(segmentId: number, text: string, codings: Coding[], onSpan: (span: Span) => void) {
  const anno = useAnnotator<RecogitoTextAnnotator>()
  const annotations = useMemo(() => codings.map(item => codingAnnotation(item, text)), [codings, text])
  useEffect(() => {
    if (!anno) return
    anno.setAnnotations(annotations)
  }, [anno, annotations])
  useEffect(() => {
    if (!anno) return
    const created = (annotation: TextAnnotation) => {
      const span = annotationSpan(annotation, segmentId, text)
      if (span) onSpan(span)
    }
    const selected = (items: TextAnnotation[]) => { if (items[0]) created(items[0]) }
    anno.on('createAnnotation', created)
    anno.on('selectionChanged', selected)
    return () => { anno.off('createAnnotation', created); anno.off('selectionChanged', selected) }
  }, [anno, segmentId, text, onSpan])
}

export function AnnotationSync({ segmentId, text, codings, onSpan }: { segmentId: number; text: string; codings: Coding[]; onSpan: (span: Span) => void }) {
  useAnnotationSync(segmentId, text, codings, onSpan)
  return null
}

export function annotationStyle(codeIds: number[]): HighlightStyleExpression {
  return annotation => {
    const id = Number(annotation.bodies[0]?.value)
    const index = Math.max(0, codeIds.indexOf(id)) % 8 + 1
    const color = getComputedStyle(document.documentElement).getPropertyValue(`--code-${index}`).trim()
    return { fill: color, fillOpacity: 0.22 }
  }
}
