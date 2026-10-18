'use client'

import { useQuery } from '@tanstack/react-query'
import { useTranslations } from 'next-intl'

import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { apiFetch } from '@/lib/api'

type Health = {
  status: string
  db: string
  version: string
}

export function HealthStatus() {
  const t = useTranslations('Home')
  const { data, status } = useQuery({
    queryKey: ['health'],
    queryFn: () => apiFetch<Health>('/health'),
  })

  if (status === 'pending') {
    return <Skeleton className="h-6 w-48" aria-label={t('loading')} />
  }

  if (status === 'error') {
    return <p className="text-sm text-destructive">{t('error')}</p>
  }

  return (
    <div className="flex flex-wrap items-center gap-2 text-sm">
      <Badge variant={data.status === 'ok' ? 'default' : 'destructive'}>
        {data.status}
      </Badge>
      <span className="text-muted-foreground">
        {t('db', { status: data.db })}
      </span>
      <span className="text-muted-foreground tabular-nums">
        {t('version', { version: data.version })}
      </span>
    </div>
  )
}
