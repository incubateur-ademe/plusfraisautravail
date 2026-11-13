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
    .then((all) => all.filter((href) => href.startsWith('/'))) // site pages only
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

// On a copy of the production content: every published page must render.
// Catches templates and blocks that fail on real data (500).
test('chaque page du plan du site répond sans erreur', async ({ page, request }) => {
  test.setTimeout(180_000) // one request per published page
  await page.goto('/sitemap.xml')
  const paths = await page
    .locator('loc')
    .evaluateAll((locs) => locs.map((loc) => new URL(loc.textContent ?? '').pathname))
  expect(paths.length).toBeGreaterThan(10)

  const failures: string[] = []
  for (const path of paths) {
    const response = await request.get(path)
    if (response.status() !== 200) failures.push(`${response.status()} ${path}`)
  }
  expect(failures).toEqual([])
})
