'use client'

import { Moon02Icon, Sun01Icon } from '@hugeicons/core-free-icons'
import { HugeiconsIcon } from '@hugeicons/react'
import { useTheme } from 'next-themes'
import { useTranslations } from 'next-intl'
import { useState, useSyncExternalStore } from 'react'

import { Button } from '@/components/ui/button'
import { revealThemeChange } from '@/lib/revealTheme'
import { cn } from '@/lib/utils'

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
  const [preview, setPreview] = useState(false)
  const isDark = hydrated && resolvedTheme === 'dark'

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon-lg"
      className="relative z-20 size-9 overflow-visible"
      aria-label={isDark ? t('themeToLight') : t('themeToDark')}
      onMouseEnter={() => setPreview(true)}
      onMouseLeave={() => setPreview(false)}
      onClick={() => {
        if (!resolvedTheme) return
        setPreview(false)
        revealThemeChange(isDark ? 'light' : 'dark', setTheme)
      }}
    >
      {hydrated && resolvedTheme ? (
        <>
          <span
            aria-hidden
            className={cn(
              'pointer-events-none fixed top-0 left-0 z-10 size-[18rem] origin-center -translate-x-[42%] -translate-y-[42%] rounded-full bg-[var(--theme-other)] transition-[transform,opacity] duration-700 ease-[cubic-bezier(0.16,1,0.3,1)]',
              preview ? 'scale-100 opacity-35' : 'scale-0 opacity-0'
            )}
          />
          <HugeiconsIcon
            icon={isDark ? Sun01Icon : Moon02Icon}
            size={18}
            strokeWidth={1.5}
            className="relative z-20"
          />
        </>
      ) : (
        <span className="size-[18px]" />
      )}
    </Button>
  )
}
