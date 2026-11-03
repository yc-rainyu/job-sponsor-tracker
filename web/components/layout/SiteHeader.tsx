'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useTranslations } from 'next-intl'

import { SignInButton } from '@/components/layout/SignInButton'
import { ThemeToggle } from '@/components/layout/ThemeToggle'
import { UserMenu } from '@/components/layout/UserMenu'
import { Skeleton } from '@/components/ui/skeleton'
import { useMe } from '@/hooks/useMe'
import { cn } from '@/lib/utils'

const publicLinks = [
  { href: '/', key: 'sponsors' },
  { href: '/analyse', key: 'analyse' },
] as const
const signedInLinks = [
  ...publicLinks,
  { href: '/applications', key: 'applications' },
] as const

export function SiteHeader() {
  const t = useTranslations('Nav')
  const pathname = usePathname()
  const { data: me, isPending } = useMe()
  const links = me ? signedInLinks : publicLinks

  return (
    <header className="relative z-20 border-b border-border bg-background shadow-[0_2px_12px_oklch(0.35_0.03_200_/_0.18)] dark:shadow-[0_4px_20px_oklch(0_0_0_/_0.55)]">
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
        <div className="flex items-center px-4 sm:px-6">
          {isPending ? (
            <Skeleton className="size-8 rounded-full" />
          ) : me ? (
            <UserMenu me={me} />
          ) : (
            <SignInButton />
          )}
        </div>
      </div>
    </header>
  )
}
