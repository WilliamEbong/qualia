const token = document.querySelector<HTMLMetaElement>('meta[name="qualia-token"]')?.content ?? ''

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/${path}`, { ...init, headers: { 'Content-Type': 'application/json', 'X-Qualia-Token': token, ...init?.headers } })
  const data = await response.json()
  if (!response.ok) throw new Error(data.detail ?? `Request failed (${response.status})`)
  return data as T
}
