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

// opened from the "Cover letter" tag: read or change the letter without the full form
export function CoverLetterSheet({
  application,
  onClose,
}: {
  application: Application | null
  onClose: () => void
}) {
  const [shown, setShown] = useState(application)
  if (application && application !== shown) setShown(application)

  return (
    <Sheet
      open={application !== null}
      onOpenChange={(open) => {
        if (!open) onClose()
      }}
    >
      <SheetContent className="gap-0 p-0 data-[side=right]:w-full data-[side=right]:sm:max-w-xl">
        {shown ? (
          <CoverLetterEditor
            key={shown.id}
            application={shown}
            onClose={onClose}
          />
        ) : null}
      </SheetContent>
    </Sheet>
  )
}

function CoverLetterEditor({
  application,
  onClose,
}: {
  application: Application
  onClose: () => void
}) {
  const t = useTranslations('Applications')
  const update = useUpdateApplication()
  const [text, setText] = useState(application.cover_letter)
  const changed = text.trim() !== application.cover_letter

  function save() {
    update.mutate(
      { id: application.id, body: { cover_letter: text.trim() } },
      { onSuccess: onClose }
    )
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <SheetHeader className="border-b border-border">
        <SheetTitle className="text-lg">
          {t('coverLetterSheet.title')}
        </SheetTitle>
        <SheetDescription>
          {application.company} · {application.role}
        </SheetDescription>
      </SheetHeader>
      <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5">
        <Label htmlFor="cover-letter-text" className="sr-only">
          {t('coverLetterSheet.title')}
        </Label>
        <Textarea
          id="cover-letter-text"
          value={text}
          maxLength={LIMITS.long}
          onChange={(event) => setText(event.target.value)}
          placeholder={t('form.coverLetterPlaceholder')}
          className="min-h-[60svh] leading-relaxed"
        />
      </div>
      <SheetFooter className="flex-row flex-wrap items-center justify-end gap-2 border-t border-border">
        {update.isError ? (
          <p role="alert" className="basis-full text-sm text-destructive">
            {t('coverLetterSheet.saveError')}
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
          {t('coverLetterSheet.save')}
        </Button>
      </SheetFooter>
    </div>
  )
}
