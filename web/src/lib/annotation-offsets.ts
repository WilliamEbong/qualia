import type { TextAnnotation } from '@recogito/react-text-annotator'
import { toCodePointOffset, toUtf16Offset } from './offsets'
import type { Coding, Span } from './entities'

export function codingAnnotation(coding: Coding, text: string): TextAnnotation {
  const id = `coding-${coding.id}`
  const start = toUtf16Offset(text, coding.span_start)
  const end = toUtf16Offset(text, coding.span_end)
  return { id, bodies: [{ id: `${id}-code`, annotation: id, purpose: 'tagging', value: String(coding.code_id) }], target: { annotation: id, selector: [{ start, end, quote: text.slice(start, end) }] } }
}

export function annotationSpan(annotation: TextAnnotation, segmentId: number, text: string): Span | null {
  const range = annotation.target.selector[0]
  if (!range || !Number.isInteger(range.start) || !Number.isInteger(range.end) || range.start < 0 || range.end <= range.start || range.end > text.length) return null
  return { segmentId, start: toCodePointOffset(text, range.start), end: toCodePointOffset(text, range.end) }
}
