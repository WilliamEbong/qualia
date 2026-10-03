/** API offsets count Unicode code points; browser selectors count UTF-16 units. */
export function toCodePointOffset(text: string, utf16Offset: number): number {
  return Array.from(text.slice(0, utf16Offset)).length
}

export function toUtf16Offset(text: string, codePointOffset: number): number {
  return Array.from(text).slice(0, codePointOffset).join('').length
}
