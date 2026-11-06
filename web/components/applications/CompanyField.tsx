'use client'

import { useQuery } from '@tanstack/react-query'
import { useTranslations } from 'next-intl'
import { useEffect, useId, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  type SponsorCheck,
  type SponsorResult,
  getRegisterInfo,
  searchSponsors,
} from '@/lib/api'
import { UNCHECKED } from '@/lib/applicationForm'
import { cn } from '@/lib/utils'

const MIN_CHARS = 2
const DEBOUNCE_MS = 300
const SUGGESTIONS = 8

function useDebounced(value: string, delay: number) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}

export function checkFromHit(
  hit: SponsorResult,
  publishedOn: string | null
): SponsorCheck {
  return {
    status: 'on_list',
    sponsor_id: hit.id,
    registered_name: hit.registered_name,
    town: hit.town,
    match_type: hit.match_type,
    score: hit.score,
    has_skilled_worker: hit.has_skilled_worker,
    rating: hit.rating,
    checked_at: new Date().toISOString(),
    register_published_on: publishedOn,
  }
}

type Props = {
  id: string
  value: string
  onChange: (value: string) => void
  onBlur: () => void
  sponsorCheck: SponsorCheck
  onSponsorCheckChange: (check: SponsorCheck) => void
  invalid?: boolean
}

// a text field with register suggestions underneath; picking one fills sponsor_check
export function CompanyField({
  id,
  value,
  onChange,
  onBlur,
  sponsorCheck,
  onSponsorCheckChange,
  invalid,
}: Props) {
  const t = useTranslations('Applications.form')
  const listId = useId()
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(-1)
  const query = useDebounced(value.trim(), DEBOUNCE_MS)
  const enabled = open && query.length >= MIN_CHARS
  const search = useQuery({
    queryKey: ['sponsors', 'suggest', query],
    queryFn: () => searchSponsors(query, 1, SUGGESTIONS),
    enabled,
    staleTime: 5 * 60 * 1000,
  })
  const register = useQuery({
    queryKey: ['register'],
    queryFn: getRegisterInfo,
    staleTime: Infinity,
  })
  const hits = enabled ? (search.data?.hits ?? []) : []
  const listOpen = enabled && (search.isFetching || search.isSuccess)
  const matched = sponsorCheck.status === 'on_list' ? sponsorCheck : null

  function pick(hit: SponsorResult) {
    onChange(hit.trading_name ?? hit.registered_name)
    onSponsorCheckChange(checkFromHit(hit, register.data?.published_on ?? null))
    setOpen(false)
    setActive(-1)
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (!listOpen || hits.length === 0) return
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActive((index) => (index + 1) % hits.length)
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActive((index) => (index <= 0 ? hits.length - 1 : index - 1))
    } else if (event.key === 'Enter' && active >= 0) {
      event.preventDefault()
      pick(hits[active])
    } else if (event.key === 'Escape') {
      setOpen(false)
    }
  }

  return (
    <div className="relative">
      <Input
        id={id}
        value={value}
        role="combobox"
        autoComplete="off"
        aria-expanded={listOpen}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={active >= 0 ? `${listId}-${active}` : undefined}
        aria-invalid={invalid || undefined}
        placeholder={t('companyPlaceholder')}
        onChange={(event) => {
          onChange(event.target.value)
          setOpen(true)
          setActive(-1)
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => {
          setOpen(false)
          onBlur()
        }}
        onKeyDown={onKeyDown}
      />
      {listOpen ? (
        <ul
          id={listId}
          role="listbox"
          aria-label={t('suggestions')}
          className="absolute z-20 mt-1 max-h-72 w-full overflow-y-auto rounded-md border border-border bg-popover p-1 text-popover-foreground shadow-md"
        >
          {hits.map((hit, index) => (
            <li
              key={hit.id}
              id={`${listId}-${index}`}
              role="option"
              aria-selected={index === active}
              // keep focus in the input, otherwise blur closes the list before the click lands
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => pick(hit)}
              onMouseEnter={() => setActive(index)}
              className={cn(
                'flex cursor-pointer flex-col gap-0.5 rounded-sm px-2 py-1.5',
                index === active && 'bg-accent text-accent-foreground'
              )}
            >
              <span className="font-medium">{hit.registered_name}</span>
              <span className="text-sm text-muted-foreground">
                {[
                  hit.town,
                  hit.rating ? t('rating', { rating: hit.rating }) : null,
                  hit.has_skilled_worker ? t('skilledWorker') : null,
                ]
                  .filter(Boolean)
                  .join(' · ')}
              </span>
            </li>
          ))}
          {hits.length === 0 ? (
            <li className="px-2 py-1.5 text-muted-foreground">
              {search.isFetching ? t('searching') : t('noMatches')}
            </li>
          ) : null}
        </ul>
      ) : null}
      {matched ? (
        <p className="mt-2 flex flex-wrap items-center gap-x-2 text-sm">
          <span className="text-success">
            {t('matched', {
              name: matched.town
                ? `${matched.registered_name} (${matched.town})`
                : (matched.registered_name ?? ''),
            })}
          </span>
          <Button
            type="button"
            variant="link"
            size="xs"
            className="h-auto px-0"
            onClick={() => onSponsorCheckChange(UNCHECKED)}
          >
            {t('clearMatch')}
          </Button>
        </p>
      ) : null}
    </div>
  )
}
