'use client'

import { useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { useEffect } from 'react'

import { Skeleton } from '@/components/ui/skeleton'
import { useMe } from '@/hooks/useMe'

export function RequireSignIn({ children }: { children: React.ReactNode }) {
  const t = useTranslations('Auth')
  const router = useRouter()
  const { data: me, isError } = useMe()
  const signedOut = me === null

  useEffect(() => {
    if (signedOut) router.replace('/')
  }, [signedOut, router])

  if (isError) {
    return (
      <p role="alert" className="text-destructive">
        {t('meError')}
      </p>
    )
  }
  if (!me) {
    return (
      <div aria-busy className="flex flex-col gap-4">
        <Skeleton className="h-9 w-56" />
        <Skeleton className="h-6 w-80 max-w-full" />
      </div>
    )
  }
  return children
}
