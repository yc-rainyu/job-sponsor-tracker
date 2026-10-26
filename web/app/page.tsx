import { getTranslations } from 'next-intl/server'

import { SponsorSearch } from '@/components/sponsors/SponsorSearch'

export default async function Page() {
  const t = await getTranslations('Sponsors')

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-col gap-8">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold tracking-tight">{t('title')}</h1>
        <p className="text-lg text-muted-foreground">{t('lead')}</p>
      </div>
      <SponsorSearch />
    </main>
  )
}
