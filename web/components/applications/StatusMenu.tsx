'use client'

import { useTranslations } from 'next-intl'
import { toast } from 'sonner'

import { statusTone } from '@/components/applications/ApplicationParts'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useUpdateApplication } from '@/hooks/useApplicationMutations'
import type { Application } from '@/lib/api'
import { STATUSES } from '@/lib/applications'
import { cn } from '@/lib/utils'

type Status = Application['status']

// the status pill itself is the menu button, so a change is one click away
export function StatusMenu({ row }: { row: Application }) {
  const t = useTranslations('Applications')
  const update = useUpdateApplication()

  function change(next: string) {
    if (next === row.status) return
    update.mutate(
      { id: row.id, body: { status: next as Status } },
      { onError: () => toast.error(t('toasts.statusError')) }
    )
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Badge
          asChild
          variant={statusTone[row.status]}
          className={cn(
            'cursor-pointer hover:brightness-95 dark:hover:brightness-110',
            row.status === 'offer' && 'font-semibold'
          )}
        >
          <button type="button" title={t('changeStatus')}>
            {t(`status.${row.status}`)}
          </button>
        </Badge>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start">
        <DropdownMenuRadioGroup value={row.status} onValueChange={change}>
          {STATUSES.map((status) => (
            <DropdownMenuRadioItem key={status} value={status}>
              {t(`status.${status}`)}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
