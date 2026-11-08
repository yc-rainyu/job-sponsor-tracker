'use client'

import { useTranslations } from 'next-intl'

import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import type { Application } from '@/lib/api'
import {
  COUNTRIES,
  type Filters,
  NO_DATE,
  SPONSOR_STATUSES,
  STATUSES,
  countBy,
} from '@/lib/applications'
import { cn } from '@/lib/utils'

type Option = { value: string; label: string; count: number; dashed?: boolean }

function Pill({ value, label, count, dashed }: Option) {
  return (
    <ToggleGroupItem
      value={value}
      className={cn(
        'h-8 gap-1.5 rounded-full border border-border bg-transparent px-3 text-sm font-normal text-foreground hover:bg-muted data-[state=on]:border-primary data-[state=on]:bg-primary/10 data-[state=on]:text-foreground',
        dashed && 'border-dashed'
      )}
    >
      {label}
      <span className="text-muted-foreground tabular-nums">{count}</span>
    </ToggleGroupItem>
  )
}

function FilterRow({
  label,
  value,
  total,
  options,
  onChange,
}: {
  label: string
  value: string
  total: number
  options: Option[]
  onChange: (value: string) => void
}) {
  const t = useTranslations('Applications')
  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:gap-4">
      <span className="w-24 shrink-0 pt-1.5 text-sm text-muted-foreground">
        {label}
      </span>
      <ToggleGroup
        type="single"
        value={value || 'all'}
        onValueChange={(next) => onChange(next === 'all' ? '' : next)}
        aria-label={label}
        className="flex-wrap gap-2"
      >
        <Pill value="all" label={t('filters.all')} count={total} />
        {options.map((option) => (
          <Pill key={option.value} {...option} />
        ))}
      </ToggleGroup>
    </div>
  )
}

function present<K extends string>(
  keys: readonly K[],
  counts: Map<K, number>,
  label: (key: K) => string
): Option[] {
  return keys
    .filter((key) => counts.has(key))
    .map((key) => ({
      value: key,
      label: label(key),
      count: counts.get(key) ?? 0,
    }))
}

export function FilterBar({
  rows,
  filters,
  onChange,
}: {
  rows: Application[]
  filters: Filters
  onChange: (filters: Filters) => void
}) {
  const t = useTranslations('Applications')
  const set = (patch: Partial<Filters>) => onChange({ ...filters, ...patch })
  const undated = rows.filter((row) => row.applied_on === null).length
  const statusOptions = present(
    STATUSES,
    countBy(rows, (row) => row.status),
    (key) => t(`status.${key}`)
  )
  if (undated) {
    statusOptions.push({
      value: NO_DATE,
      label: t('filters.noDate'),
      count: undated,
      dashed: true,
    })
  }

  return (
    <div className="flex flex-col gap-3">
      <FilterRow
        label={t('filters.country')}
        value={filters.country}
        total={rows.length}
        options={present(
          COUNTRIES,
          countBy(rows, (row) => row.country),
          (key) => t(`country.${key}`)
        )}
        onChange={(country) => set({ country })}
      />
      <FilterRow
        label={t('filters.status')}
        value={filters.status}
        total={rows.length}
        options={statusOptions}
        onChange={(status) => set({ status })}
      />
      <FilterRow
        label={t('filters.sponsor')}
        value={filters.sponsor}
        total={rows.length}
        options={present(
          SPONSOR_STATUSES,
          countBy(rows, (row) => row.sponsor_check.status),
          (key) => t(`sponsor.${key}`)
        )}
        onChange={(sponsor) => set({ sponsor })}
      />
      <p className="text-sm text-muted-foreground sm:pl-28">
        {t('sponsorHelp')}
      </p>
    </div>
  )
}
