'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useTranslations } from 'next-intl'

import { ThemeToggle } from '@/components/layout/ThemeToggle'
import { cn } from '@/lib/utils'

const links = [
  { href: '/', key: 'sponsors' },
  { href: '/analyse', key: 'analyse' },
] as const

export function SiteHeader() {
  const t = useTranslations('Nav')
  const pathname = usePathname()

  return (
    <header className="relative z-20 overflow-visible border-b border-border bg-background shadow-[0_2px_12px_oklch(0.35_0.03_200_/_0.18)] dark:shadow-[0_4px_20px_oklch(0_0_0_/_0.55)]">
      <div className="flex h-14 items-stretch">
        <div className="flex items-center gap-2 px-4 sm:px-6">
          <ThemeToggle />
          <Link
            href="/"
            className="text-xl font-semibold tracking-tight outline-none hover:text-primary focus-visible:ring-2 focus-visible:ring-ring/30"
          >
            {t('title')}
          </Link>
        </div>
        <nav aria-label={t('nav')} className="ml-auto flex items-stretch">
          {links.map((link) => {
            const active = pathname === link.href
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  'flex items-center px-5 text-lg transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring/30',
                  active
                    ? 'bg-muted font-medium text-foreground'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                )}
                aria-current={active ? 'page' : undefined}
              >
                {t(link.key)}
              </Link>
            )
          })}
        </nav>
      </div>
    </header>
  )
}
