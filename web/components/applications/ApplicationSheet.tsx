'use client'

import { zodResolver } from '@hookform/resolvers/zod'
import { useTranslations } from 'next-intl'
import { type RefObject, useEffect, useMemo, useRef, useState } from 'react'
import { Controller, useForm, useWatch } from 'react-hook-form'
import { toast } from 'sonner'

import { CompanyField } from '@/components/applications/CompanyField'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Field,
  FieldDescription,
  FieldError,
  FieldLabel,
} from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { NativeSelect, NativeSelectOption } from '@/components/ui/native-select'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { Textarea } from '@/components/ui/textarea'
import {
  useCreateApplication,
  useDeleteApplication,
  useUpdateApplication,
} from '@/hooks/useApplicationMutations'
import { ApiError, type Application, type SponsorCheck } from '@/lib/api'
import {
  type FormValues,
  UNCHECKED,
  buildSchema,
  emptyValues,
  toCreateBody,
  toFormValues,
  toUpdateBody,
} from '@/lib/applicationForm'
import {
  CHANNELS,
  COUNTRIES,
  SPONSOR_STATUSES,
  STATUSES,
  WORK_MODES,
} from '@/lib/applications'

export type SheetState =
  | { mode: 'closed' }
  | { mode: 'create' }
  | { mode: 'edit'; application: Application }

export function ApplicationSheet({
  state,
  onClose,
}: {
  state: SheetState
  onClose: () => void
}) {
  const dirtyRef = useRef(false)
  // keep the last open state while the sheet slides out, so it does not go blank
  const [shown, setShown] = useState(state)
  if (state.mode !== 'closed' && state !== shown) setShown(state)
  const application = shown.mode === 'edit' ? shown.application : null

  return (
    <Sheet
      open={state.mode !== 'closed'}
      onOpenChange={(open) => {
        if (!open) onClose()
      }}
    >
      <SheetContent
        className="gap-0 p-0 data-[side=right]:w-full data-[side=right]:sm:max-w-xl"
        // a stray click on the backdrop must not throw away a half-filled form
        onInteractOutside={(event) => {
          if (dirtyRef.current) event.preventDefault()
        }}
      >
        {shown.mode !== 'closed' ? (
          <ApplicationForm
            key={application?.id ?? 'new'}
            application={application}
            dirtyRef={dirtyRef}
            onClose={onClose}
          />
        ) : null}
      </SheetContent>
    </Sheet>
  )
}

type Option = { value: string; label: string; disabled?: boolean }
type FieldErrorLike = { message?: string } | undefined

function SelectField({
  id,
  label,
  options,
  error,
  hint,
  className,
  ...props
}: React.ComponentProps<typeof NativeSelect> & {
  label: string
  options: readonly Option[]
  error?: FieldErrorLike
  hint?: string
}) {
  return (
    <Field className={className} data-invalid={error ? true : undefined}>
      <FieldLabel htmlFor={id}>{label}</FieldLabel>
      <NativeSelect id={id} aria-invalid={error ? true : undefined} {...props}>
        {options.map((option) => (
          <NativeSelectOption
            key={option.value}
            value={option.value}
            disabled={option.disabled}
          >
            {option.label}
          </NativeSelectOption>
        ))}
      </NativeSelect>
      {hint ? <FieldDescription>{hint}</FieldDescription> : null}
      <FieldError errors={[error]} />
    </Field>
  )
}

function TextField({
  id,
  label,
  error,
  className,
  ...props
}: React.ComponentProps<typeof Input> & {
  label: string
  error?: FieldErrorLike
}) {
  return (
    <Field className={className} data-invalid={error ? true : undefined}>
      <FieldLabel htmlFor={id}>{label}</FieldLabel>
      <Input id={id} aria-invalid={error ? true : undefined} {...props} />
      <FieldError errors={[error]} />
    </Field>
  )
}

function TextareaField({
  id,
  label,
  error,
  className,
  ...props
}: React.ComponentProps<typeof Textarea> & {
  label: string
  error?: FieldErrorLike
}) {
  return (
    <Field className={className} data-invalid={error ? true : undefined}>
      <FieldLabel htmlFor={id}>{label}</FieldLabel>
      <Textarea id={id} aria-invalid={error ? true : undefined} {...props} />
      <FieldError errors={[error]} />
    </Field>
  )
}

function ApplicationForm({
  application,
  dirtyRef,
  onClose,
}: {
  application: Application | null
  dirtyRef: RefObject<boolean>
  onClose: () => void
}) {
  const t = useTranslations('Applications')
  const create = useCreateApplication()
  const update = useUpdateApplication()
  const remove = useDeleteApplication()
  const schema = useMemo(
    () =>
      buildSchema({
        required: t('form.errors.required'),
        tooLong: (max) => t('form.errors.tooLong', { max }),
      }),
    [t]
  )
  const {
    register,
    control,
    handleSubmit,
    setValue,
    formState: { errors, isDirty, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: application ? toFormValues(application) : emptyValues(),
  })
  const [error, setError] = useState<string | null>(null)
  const sponsorCheck = useWatch({ control, name: 'sponsor_check' })

  useEffect(() => {
    dirtyRef.current = isDirty
    return () => {
      dirtyRef.current = false
    }
  }, [isDirty, dirtyRef])

  function setSponsorStatus(next: string) {
    const status = next as SponsorCheck['status']
    // "licensed sponsor" only comes from picking a register entry in the company field
    if (status === 'on_list') return
    setValue(
      'sponsor_check',
      status === 'unchecked'
        ? UNCHECKED
        : { status, checked_at: new Date().toISOString() },
      { shouldDirty: true }
    )
  }

  async function onSubmit(values: FormValues) {
    setError(null)
    try {
      if (application) {
        const body = toUpdateBody(values, application)
        if (Object.keys(body).length > 0) {
          await update.mutateAsync({ id: application.id, body })
        }
      } else {
        await create.mutateAsync(toCreateBody(values))
      }
      onClose()
    } catch (caught) {
      setError(
        caught instanceof ApiError && caught.detail
          ? caught.detail
          : t('form.saveError')
      )
    }
  }

  function onDelete() {
    if (!application) return
    remove.mutate(application.id, {
      onSuccess: onClose,
      onError: () => toast.error(t('toasts.deleteError')),
    })
  }

  const labels = (keys: readonly string[], prefix: string): Option[] =>
    keys.map((key) => ({ value: key, label: t(`${prefix}.${key}`) }))

  return (
    <form
      noValidate
      onSubmit={handleSubmit(onSubmit)}
      className="flex h-full min-h-0 flex-col"
    >
      <SheetHeader className="border-b border-border">
        <SheetTitle className="text-lg">
          {application ? t('form.editTitle') : t('form.addTitle')}
        </SheetTitle>
        <SheetDescription>
          {application
            ? `${application.company} · ${application.role}`
            : t('form.addDescription')}
        </SheetDescription>
      </SheetHeader>

      <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5">
        <div className="grid gap-5 sm:grid-cols-2">
          <div className="flex flex-col gap-3">
            <TextField
              id="applied_on"
              type="date"
              label={t('form.appliedOn')}
              error={errors.applied_on}
              {...register('applied_on')}
            />
            <Controller
              control={control}
              name="is_approx"
              render={({ field }) => (
                <Field orientation="horizontal">
                  <Checkbox
                    id="is_approx"
                    checked={field.value}
                    onCheckedChange={(checked) =>
                      field.onChange(checked === true)
                    }
                    onBlur={field.onBlur}
                  />
                  <FieldLabel htmlFor="is_approx" className="font-normal">
                    {t('form.approx')}
                  </FieldLabel>
                </Field>
              )}
            />
          </div>
          <SelectField
            id="country"
            label={t('form.country')}
            options={labels(COUNTRIES, 'country')}
            error={errors.country}
            {...register('country')}
          />

          <Field
            className="sm:col-span-2"
            data-invalid={errors.company ? true : undefined}
          >
            <FieldLabel htmlFor="company">{t('form.company')}</FieldLabel>
            <Controller
              control={control}
              name="company"
              render={({ field }) => (
                <CompanyField
                  id="company"
                  value={field.value}
                  onChange={field.onChange}
                  onBlur={field.onBlur}
                  sponsorCheck={sponsorCheck}
                  onSponsorCheckChange={(check) =>
                    setValue('sponsor_check', check, { shouldDirty: true })
                  }
                  invalid={Boolean(errors.company)}
                />
              )}
            />
            <FieldDescription>{t('form.companyHint')}</FieldDescription>
            <FieldError errors={[errors.company]} />
          </Field>

          <TextField
            id="role"
            className="sm:col-span-2"
            label={t('form.role')}
            error={errors.role}
            autoComplete="off"
            {...register('role')}
          />

          <TextField
            id="location"
            label={t('form.location')}
            placeholder={t('form.locationPlaceholder')}
            error={errors.location}
            autoComplete="off"
            {...register('location')}
          />
          <SelectField
            id="work_mode"
            label={t('form.workMode')}
            options={labels(WORK_MODES, 'workMode')}
            error={errors.work_mode}
            {...register('work_mode')}
          />

          <SelectField
            id="channel"
            label={t('form.channel')}
            options={labels(CHANNELS, 'channel')}
            error={errors.channel}
            {...register('channel')}
          />
          <SelectField
            id="status"
            label={t('form.status')}
            options={labels(STATUSES, 'status')}
            error={errors.status}
            {...register('status')}
          />

          <SelectField
            id="sponsor_status"
            label={t('form.sponsor')}
            value={sponsorCheck.status}
            onChange={(event) => setSponsorStatus(event.target.value)}
            options={SPONSOR_STATUSES.map((status) => ({
              value: status,
              label: t(`sponsor.${status}`),
              disabled:
                status === 'on_list' && sponsorCheck.status !== 'on_list',
            }))}
            hint={t('form.sponsorHint')}
          />
          <TextField
            id="salary_stated"
            label={t('form.salary')}
            placeholder={t('form.salaryPlaceholder')}
            error={errors.salary_stated}
            autoComplete="off"
            {...register('salary_stated')}
          />

          <TextField
            id="job_url"
            type="url"
            inputMode="url"
            className="sm:col-span-2"
            label={t('form.jobUrl')}
            placeholder="https://"
            error={errors.job_url}
            autoComplete="off"
            {...register('job_url')}
          />

          <TextField
            id="next_step"
            label={t('form.nextStep')}
            placeholder={t('form.nextStepPlaceholder')}
            error={errors.next_step}
            autoComplete="off"
            {...register('next_step')}
          />
          <TextField
            id="next_step_at"
            type="datetime-local"
            label={t('form.nextStepAt')}
            error={errors.next_step_at}
            {...register('next_step_at')}
          />

          <TextareaField
            id="cover_letter"
            className="sm:col-span-2"
            label={t('form.coverLetter')}
            placeholder={t('form.coverLetterPlaceholder')}
            error={errors.cover_letter}
            rows={4}
            {...register('cover_letter')}
          />
          <TextareaField
            id="notes"
            className="sm:col-span-2"
            label={t('form.notes')}
            placeholder={t('form.notesPlaceholder')}
            error={errors.notes}
            rows={4}
            {...register('notes')}
          />
        </div>
      </div>

      <SheetFooter className="flex-row flex-wrap items-center justify-end gap-2 border-t border-border">
        {error ? (
          <p role="alert" className="basis-full text-sm text-destructive">
            {error}
          </p>
        ) : null}
        {application ? (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                className="mr-auto text-destructive hover:bg-destructive/10 hover:text-destructive"
              >
                {t('form.delete')}
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>{t('deleteDialog.title')}</AlertDialogTitle>
                <AlertDialogDescription>
                  {t('deleteDialog.description', {
                    company: application.company,
                    role: application.role,
                  })}
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>
                  {t('deleteDialog.cancel')}
                </AlertDialogCancel>
                <AlertDialogAction
                  variant="destructive"
                  disabled={remove.isPending}
                  onClick={(event) => {
                    // stay open until the api has answered
                    event.preventDefault()
                    onDelete()
                  }}
                >
                  {t('deleteDialog.confirm')}
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        ) : null}
        <Button type="button" variant="outline" onClick={onClose}>
          {t('form.cancel')}
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {application ? t('form.save') : t('form.create')}
        </Button>
      </SheetFooter>
    </form>
  )
}
