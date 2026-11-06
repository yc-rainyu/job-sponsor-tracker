'use client'

import { useTranslations } from 'next-intl'
import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { Textarea } from '@/components/ui/textarea'
import { useUpdateApplication } from '@/hooks/useApplicationMutations'
import type { Application } from '@/lib/api'
import { LIMITS } from '@/lib/applicationForm'

// opened from the edit form's "Job description" line; saves on its own, like the cover letter sheet
export function JobDescriptionSheet({
  open,
  application,
  text,
  onClose,
  onSaved,
}: {
  open: boolean
  application: Application
  text: string
  onClose: () => void
  onSaved: (text: string) => void
}) {
  return (
    <Sheet
      open={open}
      onOpenChange={(next) => {
        if (!next) onClose()
      }}
    >
      <SheetContent className="gap-0 p-0 data-[side=right]:w-full data-[side=right]:sm:max-w-xl">
        {/* remount on close so a dropped draft is gone next time, while the slide-out still has content */}
        <JobDescriptionEditor
          key={String(open)}
          application={application}
          initial={text}
          onClose={onClose}
          onSaved={onSaved}
        />
      </SheetContent>
    </Sheet>
  )
}

function JobDescriptionEditor({
  application,
  initial,
  onClose,
  onSaved,
}: {
  application: Application
  initial: string
  onClose: () => void
  onSaved: (text: string) => void
}) {
  const t = useTranslations('Applications')
  const update = useUpdateApplication()
  const [text, setText] = useState(initial)
  const trimmed = text.trim()
  const changed = trimmed !== initial

  function save() {
    update.mutate(
      {
        id: application.id,
        body: { jd_text: trimmed === '' ? null : trimmed },
      },
      {
        onSuccess: () => {
          onSaved(trimmed)
          onClose()
        },
      }
    )
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <SheetHeader className="border-b border-border">
        <SheetTitle className="text-lg">
          {t('jobDescriptionSheet.title')}
        </SheetTitle>
        <SheetDescription>
          {application.company} · {application.role}
        </SheetDescription>
      </SheetHeader>
      <div className="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto px-6 py-5">
        <Label htmlFor="job-description-text" className="sr-only">
          {t('jobDescriptionSheet.title')}
        </Label>
        <Textarea
          id="job-description-text"
          value={text}
          maxLength={LIMITS.long}
          onChange={(event) => setText(event.target.value)}
          placeholder={t('jobDescriptionSheet.placeholder')}
          aria-describedby="job-description-count"
          className="min-h-[60svh] leading-relaxed"
        />
        <p
          id="job-description-count"
          className="text-sm text-muted-foreground tabular-nums"
        >
          {t('jobDescriptionSheet.charCount', { count: text.length })}
        </p>
      </div>
      <SheetFooter className="flex-row flex-wrap items-center justify-end gap-2 border-t border-border">
        {update.isError ? (
          <p role="alert" className="basis-full text-sm text-destructive">
            {t('jobDescriptionSheet.saveError')}
          </p>
        ) : null}
        <Button type="button" variant="outline" onClick={onClose}>
          {t('form.cancel')}
        </Button>
        <Button
          type="button"
          onClick={save}
          disabled={!changed || update.isPending}
        >
          {t('jobDescriptionSheet.save')}
        </Button>
      </SheetFooter>
    </div>
  )
}
