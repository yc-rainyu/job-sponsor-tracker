'use client'

import { GoogleLogin, useGoogleOAuth } from '@react-oauth/google'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useTheme } from 'next-themes'
import { useTranslations } from 'next-intl'
import { useState } from 'react'

import { Skeleton } from '@/components/ui/skeleton'
import { ME_KEY } from '@/hooks/useMe'
import { signInWithGoogle } from '@/lib/api'

export function SignInButton() {
  const t = useTranslations('Auth')
  const { resolvedTheme } = useTheme()
  const { scriptLoadedSuccessfully } = useGoogleOAuth()
  const queryClient = useQueryClient()
  const [googleFailed, setGoogleFailed] = useState(false)
  const signIn = useMutation({
    mutationFn: signInWithGoogle,
    onSuccess: (me) => queryClient.setQueryData(ME_KEY, me),
  })
  const failed = googleFailed || signIn.isError

  return (
    // the button is a light-only iframe, and a dark page would give it an opaque white backdrop
    <div className="flex items-center gap-3 [&_iframe]:scheme-light">
      {failed ? (
        <p role="alert" className="text-sm text-destructive">
          {t('signInError')}
        </p>
      ) : null}
      {scriptLoadedSuccessfully ? (
        <GoogleLogin
          onSuccess={({ credential }) => {
            setGoogleFailed(false)
            if (credential) signIn.mutate(credential)
          }}
          onError={() => setGoogleFailed(true)}
          theme={resolvedTheme === 'dark' ? 'filled_black' : 'outline'}
          size="medium"
          text="signin"
          shape="rectangular"
          useOneTap={false}
        />
      ) : (
        <Skeleton className="h-8 w-28" />
      )}
    </div>
  )
}
