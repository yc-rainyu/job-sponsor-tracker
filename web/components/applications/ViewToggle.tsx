'use client'

import { LayoutGridIcon, LayoutTable01Icon } from '@hugeicons/core-free-icons'
import { HugeiconsIcon } from '@hugeicons/react'
import { useTranslations } from 'next-intl'

import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import type { ViewMode } from '@/lib/applications'

const item =
  'size-8 px-0 data-[state=on]:bg-primary/10 data-[state=on]:text-foreground'

export function ViewToggle({
  value,
  onChange,
}: {
  value: ViewMode
  onChange: (view: ViewMode) => void
}) {
  const t = useTranslations('Applications')
  return (
    <ToggleGroup
      type="single"
      variant="outline"
      spacing={0}
      value={value}
      // ignore '' so one view is always selected
      onValueChange={(next) => {
        if (next === 'table' || next === 'cards') onChange(next)
      }}
      aria-label={t('view.label')}
    >
      <ToggleGroupItem
        value="table"
        className={item}
        aria-label={t('view.table')}
        title={t('view.table')}
      >
        <HugeiconsIcon icon={LayoutTable01Icon} className="size-4" />
      </ToggleGroupItem>
      <ToggleGroupItem
        value="cards"
        className={item}
        aria-label={t('view.cards')}
        title={t('view.cards')}
      >
        <HugeiconsIcon icon={LayoutGridIcon} className="size-4" />
      </ToggleGroupItem>
    </ToggleGroup>
  )
}
