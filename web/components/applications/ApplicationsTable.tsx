'use client'

import {
  type ColumnDef,
  type SortingState,
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table'
import { useTranslations } from 'next-intl'
import { useMemo, useState } from 'react'

import {
  AppliedDate,
  CompanyBlock,
  LocationText,
} from '@/components/applications/ApplicationParts'
import { StatusMenu } from '@/components/applications/StatusMenu'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import type { Application } from '@/lib/api'
import { STATUSES, daysSince, formatApplied } from '@/lib/applications'
import { cn } from '@/lib/utils'

// shadcn cells are nowrap by default; these columns hold prose and must wrap
const WRAPPING = new Set(['company', 'location', 'channel'])

export function ApplicationsTable({
  rows,
  pageIndex,
  pageSize,
  onSortChange,
  onEdit,
  onCoverLetter,
}: {
  rows: Application[]
  pageIndex: number
  pageSize: number
  onSortChange: () => void
  onEdit: (row: Application) => void
  onCoverLetter: (row: Application) => void
}) {
  const t = useTranslations('Applications')
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'applied_on', desc: true },
  ])

  const columns = useMemo<ColumnDef<Application>[]>(
    () => [
      {
        id: 'applied_on',
        accessorFn: (row) => row.applied_on ?? undefined,
        sortingFn: 'text',
        sortUndefined: 'last',
        header: t('columns.applied'),
        cell: ({ row }) => (
          <AppliedDate
            value={row.original.applied_on}
            label={
              row.original.applied_on
                ? formatApplied(row.original.applied_on)
                : ''
            }
          />
        ),
      },
      {
        id: 'country',
        enableSorting: false,
        header: t('columns.country'),
        cell: ({ row }) => t(`country.${row.original.country}`),
      },
      {
        id: 'company',
        accessorFn: (row) => row.company,
        sortingFn: 'text',
        header: t('columns.company'),
        cell: ({ row }) => (
          <div className="max-w-md min-w-64">
            <CompanyBlock
              row={row.original}
              clampNotes
              onCoverLetter={onCoverLetter}
            />
          </div>
        ),
      },
      {
        id: 'location',
        enableSorting: false,
        header: t('columns.location'),
        cell: ({ row }) => (
          <span className="block min-w-28">
            <LocationText row={row.original} />
          </span>
        ),
      },
      {
        id: 'channel',
        enableSorting: false,
        header: t('columns.channel'),
        cell: ({ row }) => t(`channel.${row.original.channel}`),
      },
      {
        id: 'status',
        accessorFn: (row) => STATUSES.indexOf(row.status),
        header: t('columns.status'),
        cell: ({ row }) => <StatusMenu row={row.original} />,
      },
      {
        id: 'salary',
        enableSorting: false,
        header: t('columns.salary'),
        cell: ({ row }) => row.original.salary_stated ?? '—',
      },
      {
        id: 'days',
        enableSorting: false,
        header: t('columns.days'),
        cell: ({ row }) =>
          row.original.applied_on ? (
            <span className="tabular-nums">
              {t('days', { count: daysSince(row.original.applied_on) })}
            </span>
          ) : (
            '—'
          ),
      },
      {
        id: 'actions',
        enableSorting: false,
        header: () => <span className="sr-only">{t('edit')}</span>,
        cell: ({ row }) => (
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="-my-1"
            onClick={() => onEdit(row.original)}
          >
            {t('edit')}
          </Button>
        ),
      },
    ],
    [t, onEdit, onCoverLetter]
  )

  // sorted before paginated, so page 2 continues the whole sorted list
  const table = useReactTable({
    data: rows,
    columns,
    state: { sorting, pagination: { pageIndex, pageSize } },
    onSortingChange: (updater) => {
      setSorting(updater)
      onSortChange()
    },
    // the page is owned by the parent; editing a row must not jump to page 1
    autoResetPageIndex: false,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  })

  return (
    <div className="rounded-lg border border-border bg-card">
      <Table>
        <TableHeader>
          {table.getHeaderGroups().map((group) => (
            <TableRow key={group.id} className="hover:bg-transparent">
              {group.headers.map((header) => {
                const sorted = header.column.getIsSorted()
                const label = flexRender(
                  header.column.columnDef.header,
                  header.getContext()
                )
                return (
                  <TableHead
                    key={header.id}
                    aria-sort={
                      sorted === 'asc'
                        ? 'ascending'
                        : sorted === 'desc'
                          ? 'descending'
                          : undefined
                    }
                    className={cn(
                      'whitespace-nowrap',
                      header.column.id === 'days' && 'text-right'
                    )}
                  >
                    {header.column.getCanSort() ? (
                      <button
                        type="button"
                        onClick={header.column.getToggleSortingHandler()}
                        className="inline-flex items-center gap-1 rounded-sm outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/30"
                      >
                        {label}
                        <span aria-hidden className="text-muted-foreground">
                          {sorted === 'asc'
                            ? '↑'
                            : sorted === 'desc'
                              ? '↓'
                              : ''}
                        </span>
                      </button>
                    ) : (
                      label
                    )}
                  </TableHead>
                )
              })}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows.map((row) => (
            <TableRow key={row.id}>
              {row.getVisibleCells().map((cell) => (
                <TableCell
                  key={cell.id}
                  className={cn(
                    'py-3 align-top',
                    WRAPPING.has(cell.column.id) && 'whitespace-normal',
                    cell.column.id === 'days' && 'text-right',
                    cell.column.id === 'actions' && 'text-right'
                  )}
                >
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
