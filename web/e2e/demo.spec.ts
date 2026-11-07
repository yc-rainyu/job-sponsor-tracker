import { expect, test } from '@playwright/test'

// each run creates a new demo user, and the api allows 5 per IP per hour
test('a demo user can add an application and see it in the list', async ({
  page,
}) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Try the demo' }).click()

  await expect(page).toHaveURL('/applications')
  await expect(page.getByText('30 applications')).toBeVisible()

  await page.getByRole('button', { name: 'Add application' }).click()
  // the button that opens the sheet and the one that saves it share a name
  const sheet = page.getByRole('dialog')
  await sheet.getByLabel('Company', { exact: true }).fill('Northgate Labs')
  await sheet.getByLabel('Role', { exact: true }).fill('Backend Engineer')
  await sheet.getByRole('button', { name: 'Add application' }).click()

  await expect(sheet).toBeHidden()
  await expect(page.getByText('31 applications')).toBeVisible()
  await expect(
    page.getByRole('row').filter({ hasText: 'Northgate Labs' })
  ).toBeVisible()
})
