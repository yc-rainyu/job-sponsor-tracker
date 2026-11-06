'use client'

import { useTranslations } from 'next-intl'

import { Badge } from '@/components/ui/badge'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import type { Application } from '@/lib/api'
import { formatDateTime, hasCoverLetter, skillCount } from '@/lib/applications'
import { cn } from '@/lib/utils'

type Status = Application['status']
type SponsorStatus = Application['sponsor_check']['status']
type Tone = 'secondary' | 'success' | 'destructive' | 'warning' | 'outline'

export const statusTone: Record<Status, Tone> = {
  draft: 'warning',
  applied: 'secondary',
  interviewing: 'success',
  offer: 'success',
  rejected: 'destructive',
  withdrawn: 'outline',
  no_response: 'outline',
}

export function StatusBadge({ status }: { status: Status }) {
  const t = useTranslations('Applications')
  return (
    <Badge
      variant={statusTone[status]}
      className={status === 'offer' ? 'font-semibold' : undefined}
    >
      {t(`status.${status}`)}
    </Badge>
  )
}

const sponsorTone: Partial<Record<SponsorStatus, Tone>> = {
  on_list: 'success',
  not_found: 'secondary',
  agency: 'outline',
}

// small tag next to the company name; nothing for rows that were never checked
export function SponsorBadge({ status }: { status: SponsorStatus }) {
  const t = useTranslations('Applications')
  const tone = sponsorTone[status]
  if (!tone) return null
  return (
    <Badge variant={tone} className="px-2 py-0">
      {t(`sponsor.${status}`)}
    </Badge>
  )
}

// tag with the skill count; opens a read-only list, editing stays in the drawer
export function SkillsBadge({ row }: { row: Application }) {
  const t = useTranslations('Applications')
  const count = skillCount(row)
  if (count === 0) return null
  const groups = [
    {
      key: 'required',
      label: t('form.skillsRequired'),
      items: row.skills.required,
    },
    {
      key: 'nice_to_have',
      label: t('form.skillsNice'),
      items: row.skills.nice_to_have,
    },
  ].filter((group) => group.items.length > 0)

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Badge
          asChild
          variant="outline"
          className="cursor-pointer px-2 py-0 hover:bg-muted"
        >
          <button type="button" title={t('skillsOpen')}>
            {t('skillsCount', { count })}
          </button>
        </Badge>
      </PopoverTrigger>
      <PopoverContent className="flex w-80 max-w-[calc(100vw-2rem)] flex-col gap-3">
        {groups.map((group) => (
          <div key={group.key} className="flex flex-col gap-1.5">
            <p className="text-sm text-muted-foreground">{group.label}</p>
            <ul className="flex flex-wrap gap-1.5">
              {group.items.map((skill) => (
                <li key={skill}>
                  <Badge variant="secondary">{skill}</Badge>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </PopoverContent>
    </Popover>
  )
}

export function CompanyBlock({
  row,
  clampNotes = false,
  onCoverLetter,
}: {
  row: Application
  clampNotes?: boolean
  onCoverLetter: (row: Application) => void
}) {
  const t = useTranslations('Applications')
  const nextStep = row.next_step
    ? row.next_step_at
      ? `${row.next_step} · ${formatDateTime(row.next_step_at)}`
      : row.next_step
    : null

  return (
    <div className="flex flex-col gap-1">
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="font-medium">{row.company}</span>
        {hasCoverLetter(row) ? (
          <Badge
            asChild
            variant="outline"
            className="cursor-pointer px-2 py-0 hover:bg-muted"
          >
            <button
              type="button"
              title={t('coverLetterOpen')}
              onClick={() => onCoverLetter(row)}
            >
              {t('coverLetter')}
            </button>
          </Badge>
        ) : null}
        <SkillsBadge row={row} />
        <SponsorBadge status={row.sponsor_check.status} />
      </div>
      <span>{row.role}</span>
      {row.notes ? (
        <p
          className={cn('text-muted-foreground', clampNotes && 'line-clamp-3')}
        >
          {row.notes}
        </p>
      ) : null}
      {nextStep ? (
        <p className="text-muted-foreground">{t('next', { step: nextStep })}</p>
      ) : null}
    </div>
  )
}

export function LocationText({ row }: { row: Application }) {
  const t = useTranslations('Applications')
  const mode =
    row.work_mode === 'unknown' ? null : t(`workMode.${row.work_mode}`)
  return <>{[row.location, mode].filter(Boolean).join(' · ') || '—'}</>
}

export function AppliedDate({
  value,
  label,
}: {
  value: string | null
  label: string
}) {
  const t = useTranslations('Applications')
  return value ? (
    <span className="whitespace-nowrap tabular-nums">{label}</span>
  ) : (
    <span className="text-warning">{t('noDate')}</span>
  )
}
