import type { components } from '@/lib/api-schema'

// generated from the FastAPI schema, run `pnpm gen:api` after changing the api
type Schemas = components['schemas']

export type SponsorHit = Schemas['SponsorHit']
export type SearchResult = Schemas['SearchResult']
export type AnalyseResult = Schemas['AnalyseResult']
export type RegisterInfo = Schemas['RegisterInfo']

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, init)
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`)
  }
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
