'use client'

import { Add01Icon, Cancel01Icon } from '@hugeicons/core-free-icons'
import { HugeiconsIcon } from '@hugeicons/react'
import { useTranslations } from 'next-intl'
import { useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Field, FieldError, FieldLabel } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { LIMITS } from '@/lib/applicationForm'

type Props = {
  id: string
  label: string
  value: string[]
  onChange: (value: string[]) => void
  error?: { message?: string }
}

// removable tags plus a short input; Enter, a comma, the + button or leaving the input adds a tag
export function SkillChips({ id, label, value, onChange, error }: Props) {
  const t = useTranslations('Applications.form')
  const [draft, setDraft] = useState('')

  function merge(names: string[]) {
    const next = [...value]
    for (const name of names) {
      const skill = name.trim().slice(0, LIMITS.skill)
      if (skill === '') continue
      const exists = next.some(
        (item) => item.toLowerCase() === skill.toLowerCase()
      )
      if (!exists) next.push(skill)
    }
    if (next.length !== value.length) onChange(next)
  }

  function add() {
    merge([draft])
    setDraft('')
  }

  // a comma, typed or pasted, finishes a tag; whatever follows it stays in the input
  function onInput(text: string) {
    if (!text.includes(',')) {
      setDraft(text)
      return
    }
    const parts = text.split(',')
    const rest = parts.pop() ?? ''
    merge(parts)
    setDraft(rest)
  }

  return (
    <Field data-invalid={error ? true : undefined}>
      <FieldLabel htmlFor={id}>{label}</FieldLabel>
      {value.length > 0 ? (
        <ul className="flex flex-wrap gap-1.5" aria-label={label}>
          {value.map((skill) => (
            <li key={skill}>
              <Badge variant="secondary" className="gap-1 pr-1.5">
                {skill}
                <button
                  type="button"
                  aria-label={t('skillRemove', { skill })}
                  onClick={() =>
                    onChange(value.filter((item) => item !== skill))
                  }
                  className="rounded-full p-0.5 outline-none hover:bg-foreground/10 focus-visible:ring-2 focus-visible:ring-ring/50"
                >
                  <HugeiconsIcon icon={Cancel01Icon} className="size-3.5" />
                </button>
              </Badge>
            </li>
          ))}
        </ul>
      ) : null}
      <div className="flex items-stretch gap-2">
        <Input
          id={id}
          value={draft}
          maxLength={LIMITS.skill}
          placeholder={t('skillPlaceholder')}
          autoComplete="off"
          aria-invalid={error ? true : undefined}
          className="max-w-60"
          onChange={(event) => onInput(event.target.value)}
          onKeyDown={(event) => {
            // Enter adds a tag instead of submitting the whole form
            if (event.key === 'Enter') {
              event.preventDefault()
              add()
            }
          }}
          onBlur={add}
        />
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="h-auto w-10 shrink-0"
          aria-label={t('skillAdd')}
          disabled={draft.trim() === ''}
          // keep focus in the input, so the user can carry on typing after a click
          onMouseDown={(event) => event.preventDefault()}
          onClick={add}
        >
          <HugeiconsIcon icon={Add01Icon} />
        </Button>
      </div>
      <FieldError errors={[error]} />
    </Field>
  )
}
