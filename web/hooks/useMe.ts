'use client'

import { useQuery } from '@tanstack/react-query'

import { getMe } from '@/lib/api'

export const ME_KEY = ['me'] as const

// undefined when loading, null when signed out
export function useMe() {
  return useQuery({
    queryKey: ME_KEY,
    queryFn: getMe,
    retry: false,
    staleTime: 5 * 60 * 1000,
  })
}
