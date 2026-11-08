import { defineConfig, devices } from '@playwright/test'

const CI = Boolean(process.env.CI)

export default defineConfig({
  testDir: './e2e',
  forbidOnly: CI,
  reporter: CI ? [['github'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  // locally this reuses a running `pnpm dev`; CI runs `pnpm build` first
  webServer: {
    command: 'pnpm start',
    url: 'http://localhost:3000',
    reuseExistingServer: !CI,
  },
})
