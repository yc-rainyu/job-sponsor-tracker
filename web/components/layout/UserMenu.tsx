'use client'

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { useRef, useState } from 'react'
import { toast } from 'sonner'

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
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
import { deleteAccount, logout, type Me } from '@/lib/api'

export function UserMenu({ me }: { me: Me }) {
  const t = useTranslations('Auth')
  const router = useRouter()
  const queryClient = useQueryClient()
  const [confirmOpen, setConfirmOpen] = useState(false)
  const triggerRef = useRef<HTMLButtonElement>(null)

  function forgetUser() {
    queryClient.setQueryData(ME_KEY, null)
    queryClient.removeQueries({ queryKey: APPLICATIONS_KEY })
  }

  const signOut = useMutation({ mutationFn: logout, onSuccess: forgetUser })
  const remove = useMutation({
    mutationFn: deleteAccount,
    onSuccess: () => {
      setConfirmOpen(false)
      forgetUser()
      router.push('/')
      toast.success(t('accountDeleted'))
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
          ref={triggerRef}
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
          {/* demo data is thrown away after 24 hours, so End demo is enough */}
          {me.is_demo ? null : (
            <DropdownMenuItem
              variant="destructive"
              onSelect={() => {
                remove.reset()
                setConfirmOpen(true)
              }}
            >
              {t('deleteAccount')}
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent
          onCloseAutoFocus={(event) => {
            // the menu item that opened it is gone, so focus would fall to the page
            event.preventDefault()
            triggerRef.current?.focus()
          }}
        >
          <AlertDialogHeader>
            <AlertDialogTitle>{t('deleteDialog.title')}</AlertDialogTitle>
            <AlertDialogDescription>
              {t('deleteDialog.description')}
            </AlertDialogDescription>
          </AlertDialogHeader>
          {remove.isError ? (
            <p role="alert" className="text-sm text-destructive">
              {t('deleteDialog.error')}
            </p>
          ) : null}
          <AlertDialogFooter>
            <AlertDialogCancel disabled={remove.isPending}>
              {t('deleteDialog.cancel')}
            </AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              disabled={remove.isPending}
              onClick={(event) => {
                // stay open until the api has answered
                event.preventDefault()
                remove.mutate()
              }}
            >
              {t('deleteDialog.confirm')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
