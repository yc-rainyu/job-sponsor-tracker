import { expect, test } from '@playwright/test'

// made up for this test; the last line is the kind of refusal the rules catch
const JOB_DESCRIPTION = `Backend Engineer
Northgate Labs | Manchester (Hybrid)
Salary: £55,000 - £65,000 per annum

Requirements
- Strong Python and PostgreSQL
- Experience with Docker

We are unable to offer visa sponsorship for this role.`

test('analysing a pasted job description shows the visa verdict and skills', async ({
  page,
}) => {
  await page.goto('/analyse')
  await page.getByLabel('Job description').fill(JOB_DESCRIPTION)
  await page.getByRole('button', { name: 'Analyse description' }).click()

  const sponsorship = page.locator('section', {
    has: page.getByRole('heading', { name: 'Sponsorship' }),
  })
  await expect(sponsorship.getByText('Says no sponsorship')).toBeVisible()
  await expect(
    sponsorship.getByText(
      'We are unable to offer visa sponsorship for this role.'
    )
  ).toBeVisible()

  const skills = page.locator('section', {
    has: page.getByRole('heading', { name: 'Skills' }),
  })
  await expect(skills.getByText('Python', { exact: true })).toBeVisible()
})
