'use client'

import { useTranslations } from 'next-intl'

import { Button } from '@/components/ui/button'

// first, last and the neighbours of the current page; the rest collapse to …
function pageItems(current: number, pages: number): (number | 'gap')[] {
  if (pages <= 7) {
    return Array.from({ length: pages }, (_, index) => index + 1)
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

// page is 1-based
export function Pagination({
  page,
  pages,
  onPage,
  className,
}: {
  page: number
  pages: number
  onPage: (page: number) => void
  className?: string
}) {
  const t = useTranslations('Pagination')

  return (
    <nav
      aria-label={t('pages')}
      className={className ?? 'flex flex-wrap items-center gap-2'}
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
  )
}
