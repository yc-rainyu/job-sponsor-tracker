'use client'

import { useMutation, useQueryClient } from '@tanstack/react-query'

import { APPLICATIONS_KEY } from '@/hooks/useApplications'
import {
  type Application,
  type ApplicationCreate,
  type ApplicationUpdate,
  createApplication,
  deleteApplication,
  updateApplication,
} from '@/lib/api'

type Rows = Application[] | undefined

// the api validated the patch, so fields it leaves out keep their value
function applyPatch(row: Application, body: ApplicationUpdate): Application {
  const changes = Object.fromEntries(
    Object.entries(body).filter(([, value]) => value !== undefined)
  )
  return { ...row, ...changes } as Application
}

export function useCreateApplication() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: ApplicationCreate) => createApplication(body),
    onSuccess: (created) => {
      queryClient.setQueryData<Rows>(APPLICATIONS_KEY, (rows) =>
        rows ? [created, ...rows] : [created]
      )
      return queryClient.invalidateQueries({ queryKey: APPLICATIONS_KEY })
    },
  })
}

// shown as done straight away and rolled back if the api refuses
export function useUpdateApplication() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: ApplicationUpdate }) =>
      updateApplication(id, body),
    onMutate: async ({ id, body }) => {
      await queryClient.cancelQueries({ queryKey: APPLICATIONS_KEY })
      const previous = queryClient.getQueryData<Rows>(APPLICATIONS_KEY)
      queryClient.setQueryData<Rows>(APPLICATIONS_KEY, (rows) =>
        rows?.map((row) => (row.id === id ? applyPatch(row, body) : row))
      )
      return { previous }
    },
    onError: (_error, _variables, context) => {
      if (context) queryClient.setQueryData(APPLICATIONS_KEY, context.previous)
    },
    onSuccess: (updated) => {
      queryClient.setQueryData<Rows>(APPLICATIONS_KEY, (rows) =>
        rows?.map((row) => (row.id === updated.id ? updated : row))
      )
    },
    onSettled: () =>
      queryClient.invalidateQueries({ queryKey: APPLICATIONS_KEY }),
  })
}

export function useDeleteApplication() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteApplication(id),
    onSuccess: (_result, id) => {
      queryClient.setQueryData<Rows>(APPLICATIONS_KEY, (rows) =>
        rows?.filter((row) => row.id !== id)
      )
      return queryClient.invalidateQueries({ queryKey: APPLICATIONS_KEY })
    },
  })
}
