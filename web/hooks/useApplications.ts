'use client'

import { useQuery } from '@tanstack/react-query'

import { getApplications } from '@/lib/api'

export const APPLICATIONS_KEY = ['applications'] as const

export function useApplications() {
  return useQuery({ queryKey: APPLICATIONS_KEY, queryFn: getApplications })
}
