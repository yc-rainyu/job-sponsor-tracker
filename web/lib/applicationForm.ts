import { z } from 'zod'

import {
  type Application,
  type ApplicationCreate,
  type ApplicationUpdate,
  type SponsorCheck,
  localToday,
} from '@/lib/api'
import { CHANNELS, COUNTRIES, STATUSES, WORK_MODES } from '@/lib/applications'

export const UNCHECKED: SponsorCheck = { status: 'unchecked' }

// what the inputs hold: strings for everything typed, '' when empty
export type FormValues = {
  applied_on: string
  is_approx: boolean
  country: Application['country']
  company: string
  role: string
  location: string
  work_mode: Application['work_mode']
  channel: Application['channel']
  status: Application['status']
  sponsor_check: SponsorCheck
  salary_stated: string
  job_url: string
  next_step: string
  next_step_at: string
  cover_letter: string
  notes: string
}

export const LIMITS = {
  name: 200,
  short: 500,
  url: 2000,
  long: 20000,
} as const

type Messages = {
  required: string
  tooLong: (max: number) => string
}

// mirrors the api limits so the user hears about them before the request
export function buildSchema(messages: Messages) {
  const text = (max: number) =>
    z
      .string()
      .trim()
      .max(max, { error: messages.tooLong(max) })
  return z.object({
    applied_on: z.string(),
    is_approx: z.boolean(),
    country: z.enum(COUNTRIES),
    company: text(LIMITS.name).min(1, { error: messages.required }),
    role: text(LIMITS.name).min(1, { error: messages.required }),
    location: text(LIMITS.short),
    work_mode: z.enum(WORK_MODES),
    channel: z.enum(CHANNELS),
    status: z.enum(STATUSES),
    sponsor_check: z.custom<SponsorCheck>(),
    salary_stated: text(LIMITS.short),
    job_url: text(LIMITS.url),
    next_step: text(LIMITS.short),
    next_step_at: z.string(),
    cover_letter: z
      .string()
      .max(LIMITS.long, { error: messages.tooLong(LIMITS.long) }),
    notes: z
      .string()
      .max(LIMITS.long, { error: messages.tooLong(LIMITS.long) }),
  })
}

export function emptyValues(): FormValues {
  return {
    applied_on: localToday(),
    is_approx: false,
    country: 'UK',
    company: '',
    role: '',
    location: '',
    work_mode: 'unknown',
    channel: 'other',
    status: 'applied',
    sponsor_check: UNCHECKED,
    salary_stated: '',
    job_url: '',
    next_step: '',
    next_step_at: '',
    cover_letter: '',
    notes: '',
  }
}

// datetime-local wants local wall-clock time without a zone
function toLocalDateTime(iso: string) {
  const date = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export function toFormValues(row: Application): FormValues {
  return {
    applied_on: row.applied_on ?? '',
    is_approx: row.is_approx,
    country: row.country,
    company: row.company,
    role: row.role,
    location: row.location ?? '',
    work_mode: row.work_mode,
    channel: row.channel,
    status: row.status,
    sponsor_check: row.sponsor_check,
    salary_stated: row.salary_stated ?? '',
    job_url: row.job_url ?? '',
    next_step: row.next_step ?? '',
    next_step_at: row.next_step_at ? toLocalDateTime(row.next_step_at) : '',
    cover_letter: row.cover_letter,
    notes: row.notes ?? '',
  }
}

function blank(value: string) {
  const trimmed = value.trim()
  return trimmed === '' ? null : trimmed
}

export function toCreateBody(values: FormValues): ApplicationCreate {
  return {
    applied_on: values.applied_on || null,
    is_approx: values.is_approx,
    country: values.country,
    company: values.company.trim(),
    role: values.role.trim(),
    location: blank(values.location),
    work_mode: values.work_mode,
    channel: values.channel,
    status: values.status,
    salary_stated: blank(values.salary_stated),
    cover_letter: values.cover_letter.trim(),
    notes: blank(values.notes),
    job_url: blank(values.job_url),
    next_step: blank(values.next_step),
    next_step_at: values.next_step_at
      ? new Date(values.next_step_at).toISOString()
      : null,
    sponsor_check: values.sponsor_check,
  }
}

const CHECK_KEYS = [
  'status',
  'sponsor_id',
  'registered_name',
  'town',
  'match_type',
  'score',
  'has_skilled_worker',
  'rating',
  'checked_at',
  'register_published_on',
] as const

// the api fills every key with null, the form may leave keys out
function sameCheck(a: SponsorCheck, b: SponsorCheck) {
  return CHECK_KEYS.every((key) => (a[key] ?? null) === (b[key] ?? null))
}

function sameValue(key: keyof ApplicationCreate, next: unknown, prev: unknown) {
  if (key === 'sponsor_check') {
    return sameCheck(next as SponsorCheck, prev as SponsorCheck)
  }
  if (key === 'next_step_at' && next && prev) {
    return (
      new Date(next as string).getTime() === new Date(prev as string).getTime()
    )
  }
  return next === prev
}

// only the fields that changed, so PATCH leaves the rest alone
export function toUpdateBody(
  values: FormValues,
  original: Application
): ApplicationUpdate {
  const body = toCreateBody(values)
  const patch: Record<string, unknown> = {}
  for (const key of Object.keys(body) as (keyof ApplicationCreate)[]) {
    if (!sameValue(key, body[key], original[key])) patch[key] = body[key]
  }
  return patch as ApplicationUpdate
}
