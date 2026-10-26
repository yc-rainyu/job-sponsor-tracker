'use client'

import { useTranslations } from 'next-intl'

import { Badge } from '@/components/ui/badge'
import type { AnalyseResult as Result } from '@/lib/api'

function visaVariant(verdict: string) {
  if (verdict === 'offers') return 'default'
  if (verdict === 'declines') return 'destructive'
  return 'secondary'
}

export function AnalyseResult({ result }: { result: Result }) {
  const t = useTranslations('Analyse')
  const visaKey = `visa.${result.visa.verdict}`
  const workKey = result.work_mode ? `workModeValue.${result.work_mode}` : null
  const skillGroups = [
    {
      key: 'required',
      label: t('skillsRequired'),
      items: result.skills.required,
    },
    {
      key: 'nice_to_have',
      label: t('skillsNice'),
      items: result.skills.nice_to_have,
    },
    {
      key: 'mentioned',
      label: t('skillsMentioned'),
      items: result.skills.mentioned,
    },
  ].filter((group) => group.items.length > 0)

  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium">{t('visaHeading')}</h2>
        <div className="flex flex-wrap gap-2">
          <Badge
            variant={visaVariant(result.visa.verdict)}
            className="text-base"
          >
            {t.has(visaKey) ? t(visaKey) : result.visa.verdict}
          </Badge>
        </div>
        {result.visa.sentences.length > 0 ? (
          <ul className="flex flex-col gap-2">
            {result.visa.sentences.map((sentence) => (
              <li key={sentence.text}>{sentence.text}</li>
            ))}
          </ul>
        ) : null}
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium">{t('factsHeading')}</h2>
        <dl className="grid gap-4 sm:grid-cols-3">
          <Fact
            label={t('salary')}
            value={result.salary?.raw ?? t('notFound')}
          />
          <Fact
            label={t('workMode')}
            value={workKey && t.has(workKey) ? t(workKey) : t('notFound')}
          />
          <Fact
            label={t('experience')}
            value={result.experience_years?.raw ?? t('notFound')}
          />
        </dl>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium">{t('skillsHeading')}</h2>
        {skillGroups.length === 0 ? (
          <p className="text-muted-foreground">{t('noSkills')}</p>
        ) : (
          skillGroups.map((group) => (
            <div key={group.key} className="flex flex-col gap-2">
              <p className="text-lg font-medium">{group.label}</p>
              <div className="flex flex-wrap gap-2">
                {group.items.map((skill) => (
                  <Badge key={skill} variant="secondary" className="text-base">
                    {skill}
                  </Badge>
                ))}
              </div>
            </div>
          ))
        )}
      </section>
    </div>
  )
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1">
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd>{value}</dd>
    </div>
  )
}
