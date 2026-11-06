'use client'

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslations } from 'next-intl'

import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { APPLICATIONS_KEY } from '@/hooks/useApplications'
import { ME_KEY } from '@/hooks/useMe'
import { logout, type Me } from '@/lib/api'

export function UserMenu({ me }: { me: Me }) {
  const t = useTranslations('Auth')
  const queryClient = useQueryClient()
  const signOut = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.setQueryData(ME_KEY, null)
      queryClient.removeQueries({ queryKey: APPLICATIONS_KEY })
    },
  })
  const initial = (me.display_name ?? me.email ?? '').charAt(0).toUpperCase()

  return (
    <div className="flex items-center gap-3">
      {signOut.isError ? (
        <p role="alert" className="text-sm text-destructive">
          {t('signOutError')}
        </p>
      ) : null}
      <DropdownMenu>
        <DropdownMenuTrigger
          aria-label={t('account')}
          className="rounded-full outline-none focus-visible:ring-2 focus-visible:ring-ring/30"
        >
          <Avatar>
            <AvatarImage
              src={me.avatar_url ?? undefined}
              alt=""
              referrerPolicy="no-referrer"
            />
            <AvatarFallback>{initial}</AvatarFallback>
          </Avatar>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="min-w-56">
          <DropdownMenuLabel className="flex flex-col gap-0.5">
            {me.display_name ? (
              <span className="text-sm text-foreground">{me.display_name}</span>
            ) : null}
            <span>{me.is_demo ? t('demoAccount') : me.email}</span>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            disabled={signOut.isPending}
            onSelect={() => signOut.mutate()}
          >
            {me.is_demo ? t('endDemo') : t('signOut')}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
