import { LegalPage } from '@/components/legal/LegalPage'

export default function Page() {
  return (
    <LegalPage
      namespace="Privacy"
      sections={{
        stored: ['account', 'tracker'],
        notStored: ['analyse', 'tracking'],
        browser: ['session', 'local', 'google'],
        where: ['hosting', 'backups', 'logs'],
        delete: ['how', 'backups', 'export', 'demo'],
        sources: ['register', 'demo'],
        contact: ['github'],
      }}
    />
  )
}
