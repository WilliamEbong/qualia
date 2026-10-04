import { createDemoRequester, parseSnapshot } from './demo'

export const readOnly = import.meta.env.VITE_DEMO === '1'
const demoRequest = createDemoRequester(async () => {
  const response = await fetch(import.meta.env.BASE_URL + 'snapshot.json', { credentials: 'omit' })
  if (!response.ok) throw new Error('The public demo snapshot could not be loaded.')
  return parseSnapshot(await response.json())
})

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  if (readOnly) return demoRequest<T>(path, init)
  const token = document.querySelector<HTMLMetaElement>('meta[name="qualia-token"]')?.content ?? ''
  const response = await fetch(`/api/${path}`, { ...init, headers: { 'Content-Type': 'application/json', 'X-Qualia-Token': token, ...init?.headers } })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = data?.detail
    const message = typeof detail === 'string' ? detail : Array.isArray(detail)
      ? detail.map((item: {loc?: unknown[]; msg?: string}) => `${item.loc?.join('.') ?? 'Record'}: ${item.msg ?? 'Invalid value'}`).join('; ')
      : `Request failed (${response.status})`
    throw new Error(message)
  }
  if (data === null) throw new Error('The local server returned an unreadable response. Refresh the page and retry.')
  return data as T
}
