import { getTranslations } from 'next-intl/server'

import { RequireSignIn } from '@/components/applications/RequireSignIn'

export default async function Page() {
  const t = await getTranslations('Applications')

  return (
    <main className="flex flex-col gap-8">
      <RequireSignIn>
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-semibold tracking-tight">
            {t('title')}
          </h1>
          <p className="text-lg text-muted-foreground">{t('lead')}</p>
        </div>
        <p className="text-muted-foreground">{t('empty')}</p>
      </RequireSignIn>
    </main>
  )
}
