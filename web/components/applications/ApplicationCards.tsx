'use client'

import { useTranslations } from 'next-intl'

import {
  AppliedDate,
  CompanyBlock,
  LocationText,
} from '@/components/applications/ApplicationParts'
import { StatusMenu } from '@/components/applications/StatusMenu'
import { Button } from '@/components/ui/button'
import type { Application } from '@/lib/api'
import { daysSince, formatApplied } from '@/lib/applications'

export function ApplicationCards({
  rows,
  onEdit,
  onCoverLetter,
}: {
  rows: Application[]
  onEdit: (row: Application) => void
  onCoverLetter: (row: Application) => void
}) {
  const t = useTranslations('Applications')
  return (
    <ul className="divide-y divide-border rounded-lg border border-border bg-card">
      {rows.map((row) => (
        <li key={row.id} className="flex flex-col gap-3 p-4 sm:p-5">
          <div className="flex items-start justify-between gap-3">
            <p className="flex flex-wrap items-center gap-x-2 text-muted-foreground">
              <span className="text-foreground">
                <AppliedDate
                  value={row.applied_on}
                  label={row.applied_on ? formatApplied(row.applied_on) : ''}
                />
              </span>
              <span>{t(`country.${row.country}`)}</span>
              <span aria-hidden>·</span>
              <span className="tabular-nums">
                {row.applied_on
                  ? t('days', { count: daysSince(row.applied_on) })
                  : '—'}
              </span>
            </p>
            <StatusMenu row={row} />
          </div>
          <CompanyBlock row={row} onCoverLetter={onCoverLetter} />
          <div className="flex items-end justify-between gap-4">
            <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-1">
              <dt className="text-muted-foreground">{t('columns.location')}</dt>
              <dd>
                <LocationText row={row} />
              </dd>
              <dt className="text-muted-foreground">{t('columns.channel')}</dt>
              <dd>{t(`channel.${row.channel}`)}</dd>
              <dt className="text-muted-foreground">{t('columns.salary')}</dt>
              <dd>{row.salary_stated ?? '—'}</dd>
            </dl>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => onEdit(row)}
            >
              {t('edit')}
            </Button>
          </div>
        </li>
      ))}
    </ul>
  )
}
