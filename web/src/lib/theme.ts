import { useEffect, useState } from 'react'

export type Theme = 'light' | 'dark'
export const resolveTheme = (saved: string | null, prefersDark = false): Theme => saved === 'dark' || (saved !== 'light' && prefersDark) ? 'dark' : 'light'
export const nextTheme = (theme: Theme): Theme => theme === 'light' ? 'dark' : 'light'

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => {
    const prefersDark = matchMedia('(prefers-color-scheme: dark)').matches
    try { return resolveTheme(localStorage.getItem('qualia.theme'), prefersDark) } catch { return resolveTheme(null, prefersDark) }
  })
  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])
  const toggle = () => {
    const value = nextTheme(theme)
    setTheme(value)
    try { localStorage.setItem('qualia.theme', value) } catch { /* Theme still works without storage permission. */ }
  }
  return { theme, toggle, label: theme === 'light' ? 'Use dark theme' : 'Use light theme' }
}
