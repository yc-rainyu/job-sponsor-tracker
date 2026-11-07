import Link from 'next/link'
import { getTranslations } from 'next-intl/server'

import { GITHUB_URL, REGISTER_URL } from '@/lib/links'

const LINK =
  'underline underline-offset-2 outline-none hover:text-primary focus-visible:ring-2 focus-visible:ring-ring/30'

// privacy and terms share one shape: a title, a lead, then titled lists
export async function LegalPage({
  namespace,
  sections,
}: {
  namespace: 'Privacy' | 'Terms'
  sections: Record<string, string[]>
}) {
  const t = await getTranslations(namespace)
  const tags = {
    code: (chunks: React.ReactNode) => (
      <code className="font-mono">{chunks}</code>
    ),
    github: (chunks: React.ReactNode) => (
      <a href={GITHUB_URL} className={LINK}>
        {chunks}
      </a>
    ),
    issues: (chunks: React.ReactNode) => (
      <a href={`${GITHUB_URL}/issues`} className={LINK}>
        {chunks}
      </a>
    ),
    register: (chunks: React.ReactNode) => (
      <a href={REGISTER_URL} className={LINK}>
        {chunks}
      </a>
    ),
    privacy: (chunks: React.ReactNode) => (
      <Link href="/privacy" className={LINK}>
        {chunks}
      </Link>
    ),
  }

  return (
    <main className="flex max-w-2xl flex-col gap-8">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold tracking-tight">{t('title')}</h1>
        <p className="text-lg text-muted-foreground">{t('lead')}</p>
      </div>
      {Object.entries(sections).map(([section, items]) => (
        <section key={section} className="flex flex-col gap-2">
          <h2 className="text-lg font-semibold">{t(`${section}.title`)}</h2>
          <ul className="flex list-disc flex-col gap-1.5 pl-5">
            {items.map((item) => (
              <li key={item}>{t.rich(`${section}.${item}`, tags)}</li>
            ))}
          </ul>
        </section>
      ))}
    </main>
  )
}
