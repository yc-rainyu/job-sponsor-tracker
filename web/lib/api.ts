import type { components } from '@/lib/api-schema'

// generated from the FastAPI schema, run `pnpm gen:api` after changing the api
type Schemas = components['schemas']

export type SponsorResult = Schemas['SponsorResult']
export type SearchResult = Schemas['SearchResult']
export type AnalyseResult = Schemas['AnalyseResult']
export type RegisterInfo = Schemas['RegisterInfo']
export type Me = Schemas['Me']

async function request(path: string, init?: RequestInit): Promise<Response> {
  const response = await fetch(`/api${path}`, init)
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`)
  }
  return response
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await request(path, init)
  return response.json() as Promise<T>
}

export function searchSponsors(query: string, page = 1, pageSize = 10) {
  const params = new URLSearchParams({
    q: query,
    limit: String(pageSize),
    offset: String((page - 1) * pageSize),
  })
  return apiFetch<SearchResult>(`/sponsors/search?${params}`)
}

export function analyseJd(text: string) {
  return apiFetch<AnalyseResult>('/jd/analyse', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text } satisfies Schemas['AnalyseBody']),
  })
}

export function getRegisterInfo() {
  return apiFetch<RegisterInfo>('/sponsors/register')
}

// null means not signed in, which is a normal state rather than an error
export async function getMe(): Promise<Me | null> {
  const response = await fetch('/api/auth/me')
  if (response.status === 401) return null
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`)
  }
  return response.json() as Promise<Me>
}

export function signInWithGoogle(credential: string) {
  return apiFetch<Me>('/auth/google', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ credential } satisfies Schemas['GoogleSignInBody']),
  })
}

export async function logout() {
  await request('/auth/logout', { method: 'POST' })
}
