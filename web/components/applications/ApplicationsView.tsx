'use client'

import { ArrowLeft01Icon, ArrowRight01Icon } from '@hugeicons/core-free-icons'
import { HugeiconsIcon } from '@hugeicons/react'
import { useTranslations } from 'next-intl'
import { type ReactNode, useCallback, useRef, useState } from 'react'

import { ApplicationCards } from '@/components/applications/ApplicationCards'
import {
  ApplicationSheet,
  type SheetState,
} from '@/components/applications/ApplicationSheet'
import { ApplicationsTable } from '@/components/applications/ApplicationsTable'
import { CoverLetterSheet } from '@/components/applications/CoverLetterSheet'
import { FilterBar } from '@/components/applications/FilterBar'
import { ViewToggle } from '@/components/applications/ViewToggle'
import { Pagination } from '@/components/Pagination'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { NativeSelect, NativeSelectOption } from '@/components/ui/native-select'
import { Skeleton } from '@/components/ui/skeleton'
import { useApplications } from '@/hooks/useApplications'
import { useMe } from '@/hooks/useMe'
import { type Application, applicationsExportUrl } from '@/lib/api'
import {
  DEFAULT_PAGE_SIZE,
  EMPTY_FILTERS,
  type Filters,
  PAGE_SIZES,
  PAGE_SIZE_STORAGE_KEY,
  VIEW_STORAGE_KEY,
  type ViewMode,
  daysSince,
  exportParams,
  matchesFilters,
} from '@/lib/applications'
import { cn } from '@/lib/utils'

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

function initialPageSize(): number {
  try {
    const stored = Number(localStorage.getItem(PAGE_SIZE_STORAGE_KEY))
    if (PAGE_SIZES.some((size) => size === stored)) return stored
  } catch {
    // storage blocked: use the default
  }
  return DEFAULT_PAGE_SIZE
}

export function ApplicationsView() {
  const t = useTranslations('Applications')
  const tPages = useTranslations('Pagination')
  const { data, isPending, isError } = useApplications()
  const { data: me } = useMe()
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS)
  const [view, setView] = useState<ViewMode>(initialView)
  // 0-based; clamped below, so deleting the last row of the last page is fine
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(initialPageSize)
  const listRef = useRef<HTMLDivElement>(null)
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
    setPage(0)
    try {
      localStorage.setItem(VIEW_STORAGE_KEY, next)
    } catch {
      // storage blocked: the choice just lasts for this page
    }
  }

  function changeFilters(next: Filters) {
    setFilters(next)
    setPage(0)
  }

  // same order, so keep the first row on screen instead of going back to page 1
  function changePageSize(next: number, firstRow: number) {
    setPageSize(next)
    setPage(Math.floor(firstRow / next))
    try {
      localStorage.setItem(PAGE_SIZE_STORAGE_KEY, String(next))
    } catch {
      // storage blocked: the choice just lasts for this page
    }
  }

  // the bottom buttons sit under the list, so bring the new page's first row into view
  function goToPage(index: number) {
    setPage(index)
    listRef.current?.scrollIntoView({ block: 'start' })
    listRef.current?.focus({ preventScroll: true })
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
    const pageCount = Math.max(1, Math.ceil(rows.length / pageSize))
    const pageIndex = Math.min(page, pageCount - 1)
    const first = pageIndex * pageSize
    const paged = rows.length > PAGE_SIZES[0]
    const range = t('range', {
      from: first + 1,
      to: Math.min(first + pageSize, rows.length),
      total: rows.length,
    })
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
        <FilterBar rows={data} filters={filters} onChange={changeFilters} />
        {/* top controls, so changing page or page size needs no scrolling first */}
        <div className="flex flex-wrap items-center gap-3">
          <Input
            type="search"
            value={filters.q}
            onChange={(event) =>
              changeFilters({ ...filters, q: event.target.value })
            }
            placeholder={t('search')}
            aria-label={t('search')}
            className="max-w-md flex-1"
          />
          {paged ? (
            // its own row on phones, so search and the view toggle keep the first
            <div className="order-last flex w-full flex-wrap items-center gap-x-4 gap-y-2 sm:order-none sm:ml-auto sm:w-auto">
              <div className="flex items-center gap-1">
                <p className="mr-1 text-sm text-muted-foreground tabular-nums">
                  {range}
                </p>
                {pageCount > 1 ? (
                  <>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-lg"
                      disabled={pageIndex === 0}
                      onClick={() => setPage(pageIndex - 1)}
                      aria-label={tPages('previousPage')}
                      title={tPages('previousPage')}
                    >
                      <HugeiconsIcon
                        icon={ArrowLeft01Icon}
                        className="size-4"
                      />
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-lg"
                      disabled={pageIndex >= pageCount - 1}
                      onClick={() => setPage(pageIndex + 1)}
                      aria-label={tPages('nextPage')}
                      title={tPages('nextPage')}
                    >
                      <HugeiconsIcon
                        icon={ArrowRight01Icon}
                        className="size-4"
                      />
                    </Button>
                  </>
                ) : null}
              </div>
              <label className="flex items-center gap-2 text-sm text-muted-foreground">
                {t('perPage')}
                <NativeSelect
                  size="sm"
                  value={pageSize}
                  onChange={(event) =>
                    changePageSize(Number(event.target.value), first)
                  }
                  className="w-20"
                >
                  {PAGE_SIZES.map((size) => (
                    <NativeSelectOption key={size} value={size}>
                      {size}
                    </NativeSelectOption>
                  ))}
                </NativeSelect>
              </label>
            </div>
          ) : null}
          <div className={cn('ml-auto', paged && 'sm:ml-0')}>
            <ViewToggle value={view} onChange={changeView} />
          </div>
        </div>
        {rows.length === 0 ? (
          <div className="flex flex-col items-start gap-3">
            <p className="text-muted-foreground">{t('noMatch')}</p>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => changeFilters(EMPTY_FILTERS)}
            >
              {t('clearFilters')}
            </Button>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            <div ref={listRef} tabIndex={-1} className="outline-none">
              {view === 'table' ? (
                <ApplicationsTable
                  rows={rows}
                  pageIndex={pageIndex}
                  pageSize={pageSize}
                  onSortChange={() => setPage(0)}
                  onEdit={openEdit}
                  onCoverLetter={openCoverLetter}
                />
              ) : (
                <ApplicationCards
                  rows={rows.slice(first, first + pageSize)}
                  onEdit={openEdit}
                  onCoverLetter={openCoverLetter}
                />
              )}
            </div>
            {pageCount > 1 ? (
              <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3">
                <p className="text-sm text-muted-foreground tabular-nums">
                  {range}
                </p>
                <Pagination
                  page={pageIndex + 1}
                  pages={pageCount}
                  onPage={(next) => goToPage(next - 1)}
                />
              </div>
            ) : null}
          </div>
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
