import { getTranslations } from 'next-intl/server'

import { HealthStatus } from '@/components/health-status'

export default async function Page() {
  const t = await getTranslations('Home')

  return (
    <main className="mx-auto flex min-h-svh max-w-3xl flex-col gap-4 p-6">
      <h1 className="text-lg font-medium">{t('title')}</h1>
      <section className="flex flex-col gap-2">
        <h2 className="text-sm text-muted-foreground">{t('apiStatus')}</h2>
        <HealthStatus />
      </section>
    </main>
  )
}
