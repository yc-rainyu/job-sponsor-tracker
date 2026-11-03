'use client'

import { Moon02Icon, Sun01Icon } from '@hugeicons/core-free-icons'
import { HugeiconsIcon } from '@hugeicons/react'
import { useTheme } from 'next-themes'
import { useTranslations } from 'next-intl'
import { useSyncExternalStore } from 'react'

import { Button } from '@/components/ui/button'

const subscribe = () => () => {}

function useIsHydrated() {
  return useSyncExternalStore(
    subscribe,
    () => true,
    () => false
  )
}

export function ThemeToggle() {
  const t = useTranslations('Nav')
  const hydrated = useIsHydrated()
  const { resolvedTheme, setTheme } = useTheme()
  const isDark = hydrated && resolvedTheme === 'dark'

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon-lg"
      className="size-9"
      aria-label={isDark ? t('themeToLight') : t('themeToDark')}
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
    >
      {hydrated && resolvedTheme ? (
        <HugeiconsIcon
          icon={isDark ? Sun01Icon : Moon02Icon}
          size={18}
          strokeWidth={1.5}
        />
      ) : (
        <span className="size-[18px]" />
      )}
    </Button>
  )
}
