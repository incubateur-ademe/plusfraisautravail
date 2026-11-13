import { expect, test } from '../fixtures'

test('la page d’accueil s’affiche', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveTitle(/Plus frais au travail/)
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  await expect(page.getByRole('navigation', { name: 'Menu principal' })).toBeVisible()
})

test('chaque rubrique du menu principal s’affiche', async ({ page }) => {
  await page.goto('/')
  const hrefs = await page
    .getByRole('navigation', { name: 'Menu principal' })
    .getByRole('link')
    .evaluateAll((links) => links.map((link) => link.getAttribute('href') ?? ''))
  expect(hrefs.length).toBeGreaterThan(1)

  for (const href of new Set(hrefs)) {
    const response = await page.goto(href)
    expect(response?.status(), href).toBe(200)
    await expect(page.getByRole('heading', { level: 1 }), href).toBeVisible()
  }
})

test('une adresse inconnue affiche la page 404 du site', async ({ page }) => {
  const response = await page.goto('/cette-page-n-existe-pas/')
  expect(response?.status()).toBe(404)
  await expect(page.getByRole('navigation', { name: 'Menu principal' })).toBeVisible()
})
