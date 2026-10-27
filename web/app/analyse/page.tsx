import { getTranslations } from 'next-intl/server'

import { AnalyseForm } from '@/components/analyse/AnalyseForm'

export default async function Page() {
  const t = await getTranslations('Analyse')

  return (
    <main className="flex flex-col gap-8">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold tracking-tight">{t('title')}</h1>
        <p className="text-lg text-muted-foreground">{t('lead')}</p>
      </div>
      <AnalyseForm />
    </main>
  )
}
