'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useTranslations } from 'next-intl'

import { DemoButton } from '@/components/layout/DemoButton'
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

// below md the nav drops to a second row, so brand, nav and auth all fit a phone
export function SiteHeader() {
  const t = useTranslations('Nav')
  const pathname = usePathname()
  const { data: me, isPending } = useMe()
  const links = me ? signedInLinks : publicLinks
  const signedOut = !isPending && !me

  return (
    <header className="relative z-20 border-b border-border bg-background shadow-[0_2px_12px_oklch(0.3_0.03_260_/_0.16)] md:sticky md:top-0 dark:shadow-[0_4px_20px_oklch(0_0_0_/_0.55)]">
      <div className="flex flex-wrap items-center md:h-14 md:flex-nowrap md:items-stretch">
        <div className="flex h-12 items-center gap-2 px-3 md:h-14 md:px-4 lg:px-6">
          <ThemeToggle />
          <Link
            href="/"
            className="text-base font-semibold tracking-tight whitespace-nowrap outline-none hover:text-primary focus-visible:ring-2 focus-visible:ring-ring/30 md:text-xl"
          >
            {t('title')}
          </Link>
        </div>
        <div className="ml-auto flex h-12 items-center px-3 md:order-last md:ml-0 md:h-14 md:px-4 lg:px-6">
          {isPending ? (
            <Skeleton className="size-8 rounded-full" />
          ) : me ? (
            <UserMenu me={me} />
          ) : (
            <SignInButton />
          )}
        </div>
        <nav
          aria-label={t('nav')}
          className="flex w-full items-stretch border-t border-border md:ml-auto md:w-auto md:border-t-0"
        >
          {links.map((link) => {
            const active = pathname === link.href
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  'flex items-center px-4 py-2.5 text-base transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring/30 md:px-4 md:py-0 md:text-lg lg:px-5',
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
          {signedOut ? (
            <div className="ml-auto flex items-center pr-3 pl-3 md:pr-2">
              <DemoButton />
            </div>
          ) : null}
        </nav>
      </div>
    </header>
  )
}
