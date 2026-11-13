import type { Page } from '@playwright/test'
import { expect, test } from '../fixtures'

// The built autodiag app (vite preview, see spa.config.ts), not Storybook:
// routing and questionnaire branching from questions.yaml.
test.use({ baseURL: `http://127.0.0.1:${process.env.AUTODIAG_PORT ?? 6008}` })

const question = (page: Page) => page.getByRole('heading', { level: 2 })

/** Pick the nth answer, go to the next screen and wait for it. */
async function answer(page: Page, nth: number) {
  const before = page.url()
  await page.locator('.fr-radio-group').nth(nth).click()
  await page.getByRole('button', { name: 'Suivant' }).click()
  await page.waitForURL((url) => url.href !== before)
}

test.describe('Autodiag, navigation conditionnelle', () => {
  test('la page d’accueil se charge', async ({ page }) => {
    await page.goto('/autodiag/')
    await expect(page.getByRole('heading', { level: 1 })).toContainText('Evaluez votre site')
    await expect(page.getByText('Commencer')).toBeVisible()
  })

  test('Oui → saute contexte.q2 → désimperméabilisation.q1', async ({ page }) => {
    await page.goto('/autodiag/contexte.q1')
    await answer(page, 0)
    await expect(question(page)).toContainText('sols')
    await expect(page.getByText('DÉSIMPERMÉABILISATION')).toBeVisible()
  })

  test('Non → contexte.q2 : 4 options et « Je ne sais pas »', async ({ page }) => {
    await page.goto('/autodiag/contexte.q1')
    await answer(page, 1)
    await expect(question(page)).toContainText('travaux')
    await expect(page.locator('.fr-radio-group')).toHaveCount(4)
    await expect(page.getByRole('button', { name: 'Je ne sais pas' })).toBeVisible()
  })

  test('Non → Non → fin du questionnaire → résultats', async ({ page }) => {
    await page.goto('/autodiag/contexte.q1')
    await answer(page, 1)
    await expect(question(page)).toContainText('travaux')
    await answer(page, 3)
    await expect(page.getByRole('heading', { level: 1 })).toContainText('Vos résultats')
  })

  test('bétonnées → désimperméabilisation.q2', async ({ page }) => {
    await page.goto('/autodiag/contexte.q1')
    await answer(page, 0)
    await expect(question(page)).toContainText('sols')
    await answer(page, 0)
    await expect(question(page)).toContainText('Avez-vous déjà agi')
  })

  test('perméables → saute q2 → eaux-pluviales.q1', async ({ page }) => {
    await page.goto('/autodiag/contexte.q1')
    await answer(page, 0)
    await answer(page, 2)
    await expect(question(page)).toContainText('pluie')
  })

  test('pas d’espaces verts → saute ilots q2 → batiments.q1', async ({ page }) => {
    await page.goto('/autodiag/ilots-rafraichissement.q1')
    await expect(question(page)).toContainText('espaces végétalisés')
    await answer(page, 0)
    await expect(question(page)).toContainText('chaleur de rentrer')
  })

  test('batiments.q2 → q2bis', async ({ page }) => {
    await page.goto('/autodiag/batiments.q2')
    await answer(page, 2)
    await expect(question(page)).toContainText('prévoyez-vous')
  })

  test('batiments.q2 → q2ter → ventilation → résultats', async ({ page }) => {
    await page.goto('/autodiag/batiments.q2')
    await answer(page, 3)
    await expect(question(page)).toContainText('utilisez-vous')
    await answer(page, 0)
    await expect(page.getByRole('heading', { level: 1 })).toContainText('Vos résultats')
  })

  test('« Retour » suit le chemin réellement parcouru', async ({ page }) => {
    await page.goto('/autodiag/contexte.q1')
    await answer(page, 0) // Oui : contexte.q2 sautée
    await page.getByRole('button', { name: 'Retour', exact: true }).click()
    await expect(page).toHaveURL(/contexte\.q1$/)
  })

  test('« Je ne sais pas » → contexte.q2', async ({ page }) => {
    await page.goto('/autodiag/contexte.q1')
    await page.getByRole('button', { name: 'Je ne sais pas' }).click()
    await expect(question(page)).toContainText('travaux')
  })

  test('parcours complet → résultats avec des scores', async ({ page }) => {
    await page.goto('/autodiag/contexte.q1')
    for (const nth of [0, 2, 2, 3, 2, 2, 3, 4, 3]) await answer(page, nth)
    await expect(question(page)).toContainText('utilisez-vous')
    await answer(page, 0)
    await expect(page.getByRole('heading', { level: 1 })).toContainText('Vos résultats')
    await expect(page.getByText(/Score global/)).toBeVisible()
    await expect(page.getByRole('main')).not.toContainText('0/1100')
  })
})
