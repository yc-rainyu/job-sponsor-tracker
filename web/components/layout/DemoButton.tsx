'use client'

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'

import { Button } from '@/components/ui/button'
import { APPLICATIONS_KEY } from '@/hooks/useApplications'
import { ME_KEY } from '@/hooks/useMe'
import { startDemo } from '@/lib/api'

export function DemoButton() {
  const t = useTranslations('Auth')
  const router = useRouter()
  const queryClient = useQueryClient()
  const demo = useMutation({
    mutationFn: startDemo,
    onSuccess: (me) => {
      // a brand new user, so nothing cached for the previous one may show
      queryClient.removeQueries({ queryKey: APPLICATIONS_KEY })
      queryClient.setQueryData(ME_KEY, me)
      router.push('/applications')
    },
  })

  return (
    <div className="flex flex-wrap items-center justify-end gap-x-3 gap-y-1">
      {demo.isError ? (
        <p role="alert" className="text-sm text-destructive">
          {t('demoError')}
        </p>
      ) : null}
      <Button
        type="button"
        variant="outline"
        size="sm"
        disabled={demo.isPending}
        onClick={() => demo.mutate()}
      >
        {t('tryDemo')}
      </Button>
    </div>
  )
}
