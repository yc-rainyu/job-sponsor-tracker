import type { components } from '@/lib/api-schema'

// generated from the FastAPI schema, run `pnpm gen:api` after changing the api
type Schemas = components['schemas']

export type SponsorResult = Schemas['SponsorResult']
export type SearchResult = Schemas['SearchResult']
export type AnalyseResult = Schemas['AnalyseResult']
export type RegisterInfo = Schemas['RegisterInfo']
export type Me = Schemas['Me']
export type Application = Schemas['Application']
export type ApplicationCreate = Schemas['ApplicationCreate']
export type ApplicationUpdate = Schemas['ApplicationUpdate']
export type SponsorCheck = Schemas['SponsorCheck']
export type ApplicationSkills = Schemas['ApplicationSkills']
export type Analysis = Schemas['Analysis']

// the api explains failures as {"detail": "..."}; keep it so the ui can show it
export class ApiError extends Error {
  status: number
  detail: string | null

  constructor(status: number, statusText: string, detail: string | null) {
    super(`${status} ${statusText}`)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

async function errorDetail(response: Response): Promise<string | null> {
  const body: unknown = await response.json().catch(() => null)
  if (body && typeof body === 'object' && 'detail' in body) {
    return typeof body.detail === 'string' ? body.detail : null
  }
  return null
}

async function request(path: string, init?: RequestInit): Promise<Response> {
  const response = await fetch(`/api${path}`, init)
  if (!response.ok) {
    throw new ApiError(
      response.status,
      response.statusText,
      await errorDetail(response)
    )
  }
  return response
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await request(path, init)
  return response.json() as Promise<T>
}

function json(body: unknown): RequestInit {
  return {
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }
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
    ...json({ text } satisfies Schemas['AnalyseBody']),
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
    ...json({ credential } satisfies Schemas['GoogleSignInBody']),
  })
}

export async function logout() {
  await request('/auth/logout', { method: 'POST' })
}

// the browser's local date, so "today" matches what the user sees
export function localToday() {
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${now.getFullYear()}-${month}-${day}`
}

export function startDemo() {
  return apiFetch<Me>('/auth/demo', {
    method: 'POST',
    ...json({ today: localToday() }),
  })
}

export function getApplications() {
  return apiFetch<Application[]>('/applications')
}

export function createApplication(body: ApplicationCreate) {
  return apiFetch<Application>('/applications', {
    method: 'POST',
    ...json(body),
  })
}

export function updateApplication(id: string, body: ApplicationUpdate) {
  return apiFetch<Application>(`/applications/${id}`, {
    method: 'PATCH',
    ...json(body),
  })
}

export async function deleteApplication(id: string) {
  await request(`/applications/${id}`, { method: 'DELETE' })
}

// a plain link: the browser downloads the file and sends the session cookie itself
export function applicationsExportUrl(params: URLSearchParams) {
  const query = params.toString()
  return `/api/applications/export.csv${query ? `?${query}` : ''}`
}
