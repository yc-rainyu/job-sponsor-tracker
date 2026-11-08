import type { Application } from '@/lib/api'

export type ViewMode = 'table' | 'cards'
export const VIEW_STORAGE_KEY = 'jst.applications.view'

export const PAGE_SIZES = [25, 50, 100] as const
export const DEFAULT_PAGE_SIZE = 50
export const PAGE_SIZE_STORAGE_KEY = 'jst.applications.pageSize'

export const STATUSES = [
  'draft',
  'applied',
  'interviewing',
  'offer',
  'rejected',
  'withdrawn',
  'no_response',
] as const satisfies readonly Application['status'][]
export const COUNTRIES = [
  'UK',
  'TW',
  'NL',
  'US',
  'other',
] as const satisfies readonly Application['country'][]
export const WORK_MODES = [
  'onsite',
  'hybrid',
  'remote',
  'unknown',
] as const satisfies readonly Application['work_mode'][]
export const CHANNELS = [
  'company_site',
  'linkedin_easy_apply',
  'job_board_104',
  'job_board_cake',
  'agency',
  'email',
  'other',
] as const satisfies readonly Application['channel'][]
export const SPONSOR_STATUSES = [
  'on_list',
  'not_found',
  'agency',
  'not_applicable',
  'unchecked',
] as const satisfies readonly Application['sponsor_check']['status'][]

// '' means no filter; NO_DATE is a pseudo status for rows without applied_on
export const NO_DATE = 'no_date'
export type Filters = {
  country: string
  status: string
  sponsor: string
  q: string
}
export const EMPTY_FILTERS: Filters = {
  country: '',
  status: '',
  sponsor: '',
  q: '',
}

export function hasCoverLetter(row: Application) {
  return row.cover_letter !== ''
}

export function skillCount(row: Application) {
  return row.skills.required.length + row.skills.nice_to_have.length
}

// the same filters as the list, for the CSV link; "no date" has no api equivalent
export function exportParams(filters: Filters) {
  const params = new URLSearchParams()
  if (filters.country) params.set('country', filters.country)
  if (filters.status && filters.status !== NO_DATE) {
    params.set('status', filters.status)
  }
  if (filters.sponsor) params.set('sponsor_status', filters.sponsor)
  if (filters.q.trim()) params.set('q', filters.q.trim())
  return params
}

// applied_on is a plain date; parse it in local time so the day never shifts
export function localDate(value: string) {
  return new Date(`${value}T00:00:00`)
}

export function daysSince(value: string, now = new Date()) {
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  return Math.round((today.getTime() - localDate(value).getTime()) / 86_400_000)
}

export function formatApplied(value: string, now = new Date()) {
  const date = localDate(value)
  return date.toLocaleDateString('en-GB', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: date.getFullYear() === now.getFullYear() ? undefined : 'numeric',
  })
}

export function formatDateTime(value: string) {
  return new Date(value).toLocaleString('en-GB', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function matchesFilters(row: Application, filters: Filters) {
  if (filters.country && row.country !== filters.country) return false
  if (filters.status === NO_DATE) {
    if (row.applied_on !== null) return false
  } else if (filters.status && row.status !== filters.status) {
    return false
  }
  if (filters.sponsor && row.sponsor_check.status !== filters.sponsor)
    return false
  const needle = filters.q.trim().toLowerCase()
  if (needle) {
    const haystack = [
      row.company,
      row.role,
      row.location ?? '',
      row.notes ?? '',
    ]
      .join('\n')
      .toLowerCase()
    if (!haystack.includes(needle)) return false
  }
  return true
}

export function countBy<K extends string>(
  rows: Application[],
  pick: (row: Application) => K
) {
  const counts = new Map<K, number>()
  for (const row of rows) {
    const key = pick(row)
    counts.set(key, (counts.get(key) ?? 0) + 1)
  }
  return counts
}
