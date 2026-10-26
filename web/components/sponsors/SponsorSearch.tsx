'use client'

import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useTranslations } from 'next-intl'
import { useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { searchSponsors, type SponsorHit } from '@/lib/api'

const PAGE_SIZE = 10

export function SponsorSearch() {
  const t = useTranslations('Sponsors')
  const [query, setQuery] = useState('')
  const [submitted, setSubmitted] = useState('')
  const [page, setPage] = useState(1)
  const search = useQuery({
    queryKey: ['sponsors', submitted, page],
    queryFn: () => searchSponsors(submitted, page, PAGE_SIZE),
    enabled: submitted !== '',
    placeholderData: keepPreviousData,
  })

  return (
    <form
      className="flex flex-col gap-6"
      onSubmit={(event) => {
        event.preventDefault()
        const trimmed = query.trim()
        if (!trimmed) return
        setPage(1)
        setSubmitted(trimmed)
      }}
    >
      <div className="flex flex-col gap-2">
        <Label htmlFor="sponsor-query">{t('queryLabel')}</Label>
        <Input
          id="sponsor-query"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={t('queryPlaceholder')}
          autoComplete="off"
        />
      </div>

      <Button
        type="submit"
        size="lg"
        disabled={query.trim() === ''}
        className="w-full"
      >
        {t('search')}
      </Button>

      <SearchStatus
        loading={search.isLoading}
        error={search.isError}
        hits={search.data?.hits}
        total={search.data?.total ?? 0}
        page={page}
        onPage={setPage}
      />
    </form>
  )
}

function pageItems(current: number, pages: number) {
  if (pages <= 7) {
    const all = []
    for (let pageNum = 1; pageNum <= pages; pageNum++) {
      all.push(pageNum)
    }
    return all
  }

  const items: (number | 'gap')[] = [1]
  const start = Math.max(2, current - 1)
  const end = Math.min(pages - 1, current + 1)
  if (start > 2) items.push('gap')
  for (let pageNum = start; pageNum <= end; pageNum++) {
    items.push(pageNum)
  }
  if (end < pages - 1) items.push('gap')
  items.push(pages)
  return items
}

function SearchStatus({
  loading,
  error,
  hits,
  total,
  page,
  onPage,
}: {
  loading: boolean
  error: boolean
  hits: SponsorHit[] | undefined
  total: number
  page: number
  onPage: (page: number) => void
}) {
  const t = useTranslations('Sponsors')
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  if (loading) {
    return (
      <div className="flex flex-col gap-3" aria-label={t('searching')}>
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-20 w-full" />
      </div>
    )
  }

  if (error) {
    return <p className="text-sm text-destructive">{t('searchError')}</p>
  }

  if (hits === undefined) {
    return <p className="text-sm text-muted-foreground">{t('empty')}</p>
  }

  if (hits.length === 0) {
    return <p className="text-sm text-muted-foreground">{t('noneFound')}</p>
  }

  return (
    <div className="flex flex-col gap-4">
      <ul className="divide-y divide-border">
        {hits.map((hit) => (
          <SponsorRow key={hit.id} hit={hit} />
        ))}
      </ul>
      {total > PAGE_SIZE ? (
        <nav
          aria-label={t('pages')}
          className="flex flex-wrap items-center justify-center gap-2"
        >
          <Button
            type="button"
            variant="ghost"
            disabled={page <= 1}
            onClick={() => onPage(page - 1)}
          >
            {t('previous')}
          </Button>
          {pageItems(page, pages).map((pageNum, index) =>
            pageNum === 'gap' ? (
              <span key={`gap-${index}`} className="px-1 text-muted-foreground">
                …
              </span>
            ) : (
              <Button
                key={pageNum}
                type="button"
                variant={pageNum === page ? 'default' : 'ghost'}
                aria-label={t('pageNumber', { page: pageNum })}
                aria-current={pageNum === page ? 'page' : undefined}
                onClick={() => onPage(pageNum)}
              >
                {pageNum}
              </Button>
            )
          )}
          <Button
            type="button"
            variant="ghost"
            disabled={page >= pages}
            onClick={() => onPage(page + 1)}
          >
            {t('next')}
          </Button>
        </nav>
      ) : null}
    </div>
  )
}

function SponsorRow({ hit }: { hit: SponsorHit }) {
  const t = useTranslations('Sponsors')
  let ratingText = t('ratingUnknown')
  if (hit.rating === 'A') ratingText = t('ratingA')
  if (hit.rating === 'B') ratingText = t('ratingB')

  return (
    <li className="flex flex-col gap-2 py-4 first:pt-0">
      <p className="text-base font-medium">{hit.registered_name}</p>
      <p className="text-sm text-muted-foreground">
        {[hit.trading_name, hit.town].filter(Boolean).join(' · ')}
      </p>
      <div className="flex flex-wrap gap-2">
        <Badge variant={hit.rating === 'B' ? 'destructive' : 'secondary'}>
          {ratingText}
        </Badge>
        <Badge variant={hit.has_skilled_worker ? 'default' : 'outline'}>
          {hit.has_skilled_worker ? t('skilledWorker') : t('noSkilledWorker')}
        </Badge>
      </div>
      {hit.rating === 'B' ? (
        <p className="text-sm text-destructive">{t('ratingBHint')}</p>
      ) : null}
      {hit.routes.length > 0 ? (
        <p className="text-sm text-muted-foreground">{hit.routes.join(', ')}</p>
      ) : null}
    </li>
  )
}
