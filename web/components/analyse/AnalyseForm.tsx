'use client'

import { useMutation, useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { useState } from 'react'
import { toast } from 'sonner'

import { AnalyseResult } from '@/components/analyse/AnalyseResult'
import {
  ApplicationSheet,
  type CreatePrefill,
  type SheetState,
} from '@/components/applications/ApplicationSheet'
import { checkFromHit } from '@/components/applications/CompanyField'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { useMe } from '@/hooks/useMe'
import {
  type AnalyseResult as Result,
  type ApplicationSkills,
  analyseJd,
  getRegisterInfo,
} from '@/lib/api'
import { UNCHECKED } from '@/lib/applicationForm'

const JD_MAX = 20000

// the drawer keeps two groups; what the rules saw without a heading counts as required until the user prunes it
function foldSkills(skills: Result['skills']): ApplicationSkills {
  const required = [...skills.required]
  for (const skill of skills.mentioned) {
    const exists = required.some(
      (item) => item.toLowerCase() === skill.toLowerCase()
    )
    if (!exists) required.push(skill)
  }
  return { required, nice_to_have: skills.nice_to_have }
}

// what the rules found, laid out for the add drawer; company and role are left to the user
function prefillFrom(
  result: Result,
  jdText: string,
  publishedOn: string | null
): CreatePrefill {
  const hit = result.company_matches[0]
  return {
    values: {
      country: 'UK',
      work_mode: result.work_mode ?? 'unknown',
      company: hit ? (hit.trading_name ?? hit.registered_name) : '',
      sponsor_check: hit ? checkFromHit(hit, publishedOn) : UNCHECKED,
      skills: foldSkills(result.skills),
    },
    jd_text: jdText,
    analysis: {
      visa: result.visa.verdict,
      salary: result.salary,
      work_mode: result.work_mode,
      experience_years: result.experience_years,
    },
  }
}

export function AnalyseForm() {
  const t = useTranslations('Analyse')
  const router = useRouter()
  const { data: me } = useMe()
  const [text, setText] = useState('')
  const [sheet, setSheet] = useState<SheetState>({ mode: 'closed' })
  const overLimit = text.length > JD_MAX
  const analyse = useMutation({
    mutationFn: analyseJd,
  })
  // same key as the footer, so this is served from cache
  const register = useQuery({
    queryKey: ['register'],
    queryFn: getRegisterInfo,
    staleTime: Infinity,
  })
  const result = analyse.data

  function openSave() {
    if (!result) return
    setSheet({
      mode: 'create',
      prefill: prefillFrom(
        result,
        analyse.variables ?? '',
        register.data?.published_on ?? null
      ),
    })
  }

  function onSaved() {
    toast.success(t('savedToast'), {
      action: {
        label: t('savedToastAction'),
        onClick: () => router.push('/applications'),
      },
    })
  }

  return (
    <>
      <form
        className="grid items-start gap-8 lg:grid-cols-2"
        onSubmit={(event) => {
          event.preventDefault()
          const trimmed = text.trim()
          if (overLimit || trimmed === '') return
          analyse.mutate(trimmed)
        }}
      >
        <div className="flex flex-col gap-6">
          <div className="flex flex-col gap-2">
            <Label htmlFor="jd">{t('jdLabel')}</Label>
            <Textarea
              id="jd"
              value={text}
              onChange={(event) => setText(event.target.value)}
              placeholder={t('jdPlaceholder')}
              className="min-h-56"
              aria-invalid={overLimit}
              aria-describedby="jd-count"
            />
            <p
              id="jd-count"
              className="text-sm text-muted-foreground tabular-nums"
            >
              {t('charCount', { count: text.length.toLocaleString('en-GB') })}
            </p>
          </div>

          <Button
            type="submit"
            size="lg"
            disabled={analyse.isPending || overLimit || text.trim() === ''}
            className="w-full"
          >
            {t('analyse')}
          </Button>

          {overLimit ? (
            <p className="text-sm text-destructive">{t('overLimit')}</p>
          ) : null}
        </div>

        <div>
          {analyse.isPending ? (
            <div className="flex flex-col gap-3" aria-label={t('analysing')}>
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          ) : analyse.isError ? (
            <p className="text-destructive">{t('analyseError')}</p>
          ) : result ? (
            <div className="flex flex-col gap-8">
              <AnalyseResult result={result} />
              {me ? (
                <Button
                  type="button"
                  size="lg"
                  className="self-start"
                  onClick={openSave}
                >
                  {t('saveToTracker')}
                </Button>
              ) : me === null ? (
                <p className="text-muted-foreground">{t('signInToSave')}</p>
              ) : null}
            </div>
          ) : (
            <p className="text-muted-foreground">{t('empty')}</p>
          )}
        </div>
      </form>
      <ApplicationSheet
        state={sheet}
        onClose={() => setSheet({ mode: 'closed' })}
        onCreated={onSaved}
      />
    </>
  )
}
