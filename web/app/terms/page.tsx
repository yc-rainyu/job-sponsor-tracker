import { LegalPage } from '@/components/legal/LegalPage'

export default function Page() {
  return (
    <LegalPage
      namespace="Terms"
      sections={{
        advice: ['info', 'adviser'],
        guarantees: ['register', 'date', 'analysis', 'service'],
        account: ['delete', 'use'],
        licence: ['data'],
      }}
    />
  )
}
