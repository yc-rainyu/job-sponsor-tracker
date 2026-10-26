export type SponsorHit = {
  id: number
  registered_name: string
  trading_name: string | null
  town: string | null
  rating: string | null
  routes: string[]
  has_skilled_worker: boolean
  match_type: string
  score: number
}

export type AnalyseResult = {
  visa: {
    verdict: string
    sentences: { text: string; label: string }[]
  }
  salary: {
    min: number | null
    max: number | null
    currency: string | null
    period: string | null
    raw: string
  } | null
  work_mode: string | null
  experience_years: {
    min: number | null
    max: number | null
    raw: string
  } | null
  skills: {
    required: string[]
    nice_to_have: string[]
    mentioned: string[]
  }
  company_matches: SponsorHit[]
}

async function errorMessage(res: Response) {
  try {
    const body = await res.json()
    if (typeof body?.detail === 'string') return body.detail
  } catch {}
  return `${res.status} ${res.statusText}`
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...init,
    credentials: 'include',
  })

  if (!res.ok) {
    throw new Error(await errorMessage(res))
  }

  return res.json() as Promise<T>
}

export type SponsorSearchPage = {
  hits: SponsorHit[]
  total: number
}

export function searchSponsors(query: string, page = 1, pageSize = 10) {
  const params = new URLSearchParams({
    q: query,
    limit: String(pageSize),
    offset: String((page - 1) * pageSize),
  })
  return apiFetch<SponsorSearchPage>(`/sponsors/search?${params}`)
}

export function analyseJd(text: string) {
  return apiFetch<AnalyseResult>('/jd/analyse', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
}

export type Health = {
  status: string
  db: string
  version: string
  register_published_on: string | null
}

export function getHealth() {
  return apiFetch<Health>('/health')
}
