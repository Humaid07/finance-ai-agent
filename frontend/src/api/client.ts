const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:7071/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}/${path}`
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const error = await res.text()
    throw new Error(`API error ${res.status}: ${error}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  get: <T>(path: string, params?: Record<string, string>) => {
    const search = params ? '?' + new URLSearchParams(params).toString() : ''
    return request<T>(`${path}${search}`)
  },
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
}
