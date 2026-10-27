import { Geist_Mono, Inter } from 'next/font/google'
import { NextIntlClientProvider } from 'next-intl'
import { getMessages } from 'next-intl/server'

import './globals.css'
import { Providers } from '@/components/Providers'
import { SiteFooter } from '@/components/layout/SiteFooter'
import { SiteHeader } from '@/components/layout/SiteHeader'
import { ThemeProvider } from '@/components/ThemeProvider'
import { cn } from '@/lib/utils'

export const metadata = {
  title: 'Job Sponsor Tracker',
  description: 'Look up UK visa sponsors and analyse job descriptions.',
}

const inter = Inter({ subsets: ['latin'], variable: '--font-sans' })

const fontMono = Geist_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
})

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  const messages = await getMessages()

  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={cn('font-sans antialiased', inter.variable, fontMono.variable)}
    >
      <body>
        <ThemeProvider>
          <NextIntlClientProvider messages={messages}>
            <Providers>
              <div className="flex min-h-svh flex-col">
                <SiteHeader />
                <div className="mx-auto w-full max-w-6xl flex-1 px-6 py-10">
                  {children}
                </div>
                <SiteFooter />
              </div>
            </Providers>
          </NextIntlClientProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
