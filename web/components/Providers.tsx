'use client'

import { GoogleOAuthProvider } from '@react-oauth/google'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ?? ''

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient())

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID} locale="en">
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </GoogleOAuthProvider>
  )
}
