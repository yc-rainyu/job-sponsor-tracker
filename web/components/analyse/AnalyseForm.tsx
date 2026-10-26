'use client'

import { useMutation } from '@tanstack/react-query'
import { useTranslations } from 'next-intl'
import { useState } from 'react'

import { AnalyseResult } from '@/components/analyse/AnalyseResult'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { analyseJd } from '@/lib/api'

const JD_MAX = 20000

export function AnalyseForm() {
  const t = useTranslations('Analyse')
  const [text, setText] = useState('')
  const overLimit = text.length > JD_MAX
  const analyse = useMutation({
    mutationFn: analyseJd,
  })

  return (
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
        ) : analyse.data ? (
          <AnalyseResult result={analyse.data} />
        ) : (
          <p className="text-muted-foreground">{t('empty')}</p>
        )}
      </div>
    </form>
  )
}
