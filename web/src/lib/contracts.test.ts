import { describe, expect, it } from 'vitest'
import { toCodePointOffset, toUtf16Offset } from './offsets'

describe('workspace text offsets', () => {
  it('round-trips saved spans across emoji and combining characters', () => {
    const text = 'a😀e\u0301b'
    expect(toCodePointOffset(text, 3)).toBe(2)
    expect(toUtf16Offset(text, 2)).toBe(3)
    const start = toUtf16Offset(text, 1)
    const end = toUtf16Offset(text, 4)
    expect(text.slice(start, end)).toBe('😀e\u0301')
    expect(toCodePointOffset(text, end)).toBe(4)
  })
})
