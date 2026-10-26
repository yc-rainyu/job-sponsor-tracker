'use client'

import { useQuery } from '@tanstack/react-query'
import { useTranslations } from 'next-intl'

import { getRegisterInfo } from '@/lib/api'

const GITHUB_URL = 'https://github.com/yc-rainyu/job-sponsor-tracker'
const OGL_URL =
  'https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/'

export function SiteFooter() {
  const t = useTranslations('Footer')
  const { data } = useQuery({
    queryKey: ['register'],
    queryFn: getRegisterInfo,
  })
  const published = data?.published_on
  const publishedLabel = published
    ? new Date(`${published}T00:00:00`).toLocaleDateString('en-GB', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      })
    : null

  return (
    <footer className="border-t border-border">
      <div className="mx-auto flex w-full max-w-6xl flex-col-reverse gap-3 px-6 py-3 text-sm text-muted-foreground sm:flex-row sm:items-start sm:justify-between sm:gap-8">
        <div className="flex max-w-xl flex-col gap-1">
          <p>
            {t('ogl')}{' '}
            <a
              href={OGL_URL}
              className="underline outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/30"
            >
              {t('oglLink')}
            </a>
            .
          </p>
          <p>{t('disclaimer')}</p>
        </div>
        <div className="flex shrink-0 flex-col gap-1 sm:items-end">
          {publishedLabel ? (
            <p className="tabular-nums">
              {t('registerDate', { date: publishedLabel })}
            </p>
          ) : null}
          <a
            href={GITHUB_URL}
            className="underline outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/30"
          >
            {t('github')}
          </a>
        </div>
      </div>
    </footer>
  )
}
