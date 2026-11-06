'use client'

import { useTranslations } from 'next-intl'
import { type ReactNode, useCallback, useState } from 'react'

import { ApplicationCards } from '@/components/applications/ApplicationCards'
import {
  ApplicationSheet,
  type SheetState,
} from '@/components/applications/ApplicationSheet'
import { ApplicationsTable } from '@/components/applications/ApplicationsTable'
import { CoverLetterSheet } from '@/components/applications/CoverLetterSheet'
import { FilterBar } from '@/components/applications/FilterBar'
import { ViewToggle } from '@/components/applications/ViewToggle'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { useApplications } from '@/hooks/useApplications'
import { useMe } from '@/hooks/useMe'
import { type Application, applicationsExportUrl } from '@/lib/api'
import {
  EMPTY_FILTERS,
  type Filters,
  VIEW_STORAGE_KEY,
  type ViewMode,
  daysSince,
  exportParams,
  matchesFilters,
} from '@/lib/applications'

// only rendered in the browser (behind RequireSignIn), so window is safe here
function initialView(): ViewMode {
  try {
    const stored = localStorage.getItem(VIEW_STORAGE_KEY)
    if (stored === 'table' || stored === 'cards') return stored
  } catch {
    // storage blocked: fall through to the width default
  }
  return window.matchMedia('(min-width: 640px)').matches ? 'table' : 'cards'
}

export function ApplicationsView() {
  const t = useTranslations('Applications')
  const { data, isPending, isError } = useApplications()
  const { data: me } = useMe()
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS)
  const [view, setView] = useState<ViewMode>(initialView)
  const [sheet, setSheet] = useState<SheetState>({ mode: 'closed' })
  const [coverLetterFor, setCoverLetterFor] = useState<Application | null>(null)
  const closeSheet = useCallback(() => setSheet({ mode: 'closed' }), [])
  const openCreate = useCallback(() => setSheet({ mode: 'create' }), [])
  const openEdit = useCallback(
    (row: Application) => setSheet({ mode: 'edit', application: row }),
    []
  )
  const openCoverLetter = useCallback(
    (row: Application) => setCoverLetterFor(row),
    []
  )

  function changeView(next: ViewMode) {
    setView(next)
    try {
      localStorage.setItem(VIEW_STORAGE_KEY, next)
    } catch {
      // storage blocked: the choice just lasts for this page
    }
  }

  let content: ReactNode
  if (isError) {
    content = (
      <p role="alert" className="text-destructive">
        {t('loadError')}
      </p>
    )
  } else if (isPending) {
    content = (
      <div aria-busy className="flex flex-col gap-4">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="h-8 w-full max-w-xl" />
        <Skeleton className="h-8 w-full max-w-xl" />
        <Skeleton className="h-40 w-full" />
      </div>
    )
  } else if (data.length === 0) {
    content = (
      <div className="flex flex-col items-start gap-3">
        <p className="text-muted-foreground">{t('empty')}</p>
        <Button type="button" onClick={openCreate}>
          {t('add')}
        </Button>
      </div>
    )
  } else {
    const today = data.filter(
      (row) => row.applied_on !== null && daysSince(row.applied_on) === 0
    ).length
    const rows = data.filter((row) => matchesFilters(row, filters))
    content = (
      <div className="flex flex-col gap-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex flex-col gap-1">
            <p className="text-muted-foreground tabular-nums">
              {t('count', { count: data.length })} ·{' '}
              {t('today', { count: today })}
            </p>
            {me?.is_demo ? (
              <p className="text-sm text-muted-foreground">{t('demoNotice')}</p>
            ) : null}
          </div>
          <div className="flex items-center gap-2">
            <Button asChild variant="outline">
              <a href={applicationsExportUrl(exportParams(filters))} download>
                {t('export')}
              </a>
            </Button>
            <Button type="button" onClick={openCreate}>
              {t('add')}
            </Button>
          </div>
        </div>
        <FilterBar rows={data} filters={filters} onChange={setFilters} />
        <div className="flex items-center justify-between gap-3">
          <Input
            type="search"
            value={filters.q}
            onChange={(event) =>
              setFilters({ ...filters, q: event.target.value })
            }
            placeholder={t('search')}
            aria-label={t('search')}
            className="max-w-md"
          />
          <ViewToggle value={view} onChange={changeView} />
        </div>
        {rows.length === 0 ? (
          <div className="flex flex-col items-start gap-3">
            <p className="text-muted-foreground">{t('noMatch')}</p>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setFilters(EMPTY_FILTERS)}
            >
              {t('clearFilters')}
            </Button>
          </div>
        ) : view === 'table' ? (
          <ApplicationsTable
            rows={rows}
            onEdit={openEdit}
            onCoverLetter={openCoverLetter}
          />
        ) : (
          <ApplicationCards
            rows={rows}
            onEdit={openEdit}
            onCoverLetter={openCoverLetter}
          />
        )}
      </div>
    )
  }

  return (
    <>
      {content}
      <ApplicationSheet state={sheet} onClose={closeSheet} />
      <CoverLetterSheet
        application={coverLetterFor}
        onClose={() => setCoverLetterFor(null)}
      />
    </>
  )
}
