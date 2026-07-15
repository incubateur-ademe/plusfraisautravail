import { test, expect, type Page } from '@playwright/test';

const BASE = '/autodiag/';

async function selectAndWait(page: Page, nth: number) {
  const label = page.locator('.fr-radio-group').nth(nth);
  await label.click();
  await page.waitForTimeout(200);
  await page.locator('button:has-text("Suivant")').click();
  // Wait for the next question to render
  await page.waitForTimeout(600);
}

test.describe('Autodiag — navigation conditionnelle', () => {

  test('page d\'accueil se charge', async ({ page }) => {
    await page.goto(BASE);
    await expect(page.locator('h1')).toContainText('Evaluez votre site');
    await expect(page.getByText('Commencer')).toBeVisible();
  });

  test('Oui → saute contexte.q2 → désimperméabilisation.q1', async ({ page }) => {
    await page.goto(`${BASE}contexte.q1`);
    await page.waitForSelector('h2');
    await selectAndWait(page, 0);
    await expect(page.locator('h2')).toContainText('sols');
    await expect(page.getByText('DÉSIMPERMÉABILISATION')).toBeVisible();
  });

  test('Non → contexte.q2 4 options + Je ne sais pas', async ({ page }) => {
    await page.goto(`${BASE}contexte.q1`);
    await page.waitForSelector('h2');
    await selectAndWait(page, 1);
    await expect(page.locator('h2')).toContainText('travaux');
    // 4 options métier ; « Je ne sais pas » est désormais un bouton sous les radios
    await expect(page.locator('.fr-radio-group')).toHaveCount(4);
    await expect(page.getByRole('button', { name: 'Je ne sais pas' })).toBeVisible();
  });

  test('Non→Non → fin du questionnaire → résultats', async ({ page }) => {
    await page.goto(`${BASE}contexte.q1`);
    await page.waitForSelector('h2');
    await selectAndWait(page, 1); // Non
    await expect(page.locator('h2')).toContainText('travaux');
    await selectAndWait(page, 3); // Non -> terminal "resultats"
    await expect(page.locator('h1')).toContainText('Vos résultats');
  });

  test('bétonnées → désimperméabilisation.q2', async ({ page }) => {
    await page.goto(`${BASE}contexte.q1`);
    await page.waitForSelector('h2');
    await selectAndWait(page, 0); // Oui
    await page.waitForSelector('h2');
    await expect(page.locator('h2')).toContainText('sols');
    await selectAndWait(page, 0); // bétonnées
    await page.waitForSelector('h2');
    await expect(page.locator('h2')).toContainText('Avez-vous déjà agi');
  });

  test('perméables (opt3) → saute q2 → eaux-pluviales.q1', async ({ page }) => {
    await page.goto(`${BASE}contexte.q1`);
    await page.waitForSelector('h2');
    await selectAndWait(page, 0); // Oui
    await page.waitForSelector('h2');
    await selectAndWait(page, 2); // perméables
    await page.waitForSelector('h2');
    await expect(page.locator('h2')).toContainText('pluie');
  });

  test('pas d\'espaces verts → saute ilots q2 → batiments.q1', async ({ page }) => {
    await page.goto(`${BASE}ilots-rafraichissement.q1`);
    await page.waitForSelector('h2');
    await expect(page.locator('h2')).toContainText('espaces végétalisés');
    await selectAndWait(page, 0); // Il n'y a pas d'espaces verts
    await page.waitForSelector('h2');
    await expect(page.locator('h2')).toContainText('chaleur de rentrer');
  });

  test('batiments.q2 → q2bis', async ({ page }) => {
    await page.goto(`${BASE}batiments.q2`);
    await page.waitForSelector('h2');
    await selectAndWait(page, 2);
    await page.waitForSelector('h2');
    await expect(page.locator('h2')).toContainText('prévoyez-vous');
  });

  test('batiments.q2 → q2ter', async ({ page }) => {
    await page.goto(`${BASE}batiments.q2`);
    await page.waitForSelector('h2');
    await selectAndWait(page, 3);
    await page.waitForSelector('h2');
    await expect(page.locator('h2')).toContainText('utilisez-vous');
  });

  test('q2ter Ventilation → résultats (terminal null)', async ({ page }) => {
    await page.goto(`${BASE}batiments.q2`);
    await page.waitForSelector('h2');
    await selectAndWait(page, 3); // -> q2ter
    await page.waitForSelector('h2');
    await expect(page.locator('h2')).toContainText('utilisez-vous');
    await selectAndWait(page, 0); // Ventilation -> terminal (fin du questionnaire)
    await expect(page.locator('h1')).toContainText('Vos résultats');
  });

  test('Retour suit le chemin réellement parcouru (pas l\'ordre linéaire)', async ({ page }) => {
    await page.goto(`${BASE}contexte.q1`);
    await page.waitForSelector('h2');
    await selectAndWait(page, 0); // Oui -> desimpermeabilisation.q1 (contexte.q2 sautée)
    await page.waitForSelector('h2');
    await page.getByRole('button', { name: 'Retour', exact: true }).click();
    // Retour vers la question réellement visitée, pas contexte.q2
    await expect(page).toHaveURL(/contexte\.q1/);
  });

  test('Je ne sais pas (bouton) → contexte.q2', async ({ page }) => {
    await page.goto(`${BASE}contexte.q1`);
    await page.waitForSelector('h2');
    // « Je ne sais pas » est un bouton sous les radios, navigation immédiate
    await page.getByRole('button', { name: 'Je ne sais pas' }).click();
    await page.waitForTimeout(600);
    await expect(page.locator('h2')).toContainText('travaux');
  });

  test('parcours complet → résultats', async ({ page }) => {
    // On va visiter toutes les questions via URL en répondant progressivement
    await page.goto(`${BASE}contexte.q1`);
    await page.waitForSelector('h2');
    await selectAndWait(page, 0); // Oui
    await page.waitForSelector('h2');
    await selectAndWait(page, 2); // perméables
    await page.waitForSelector('h2');
    await selectAndWait(page, 2); // s'infiltre
    await page.waitForSelector('h2');
    await selectAndWait(page, 3); // aménagements réalisés
    await page.waitForSelector('h2');
    await selectAndWait(page, 2); // régulière
    await page.waitForSelector('h2');
    await selectAndWait(page, 2); // arbres
    await page.waitForSelector('h2');
    await selectAndWait(page, 3); // majorité ombragées
    await page.waitForSelector('h2');
    await selectAndWait(page, 4); // déjà en place (5e)
    await page.waitForSelector('h2');
    await selectAndWait(page, 3); // déjà en place -> q2ter
    await page.waitForSelector('h2');
    await expect(page.locator('h2')).toContainText('utilisez-vous');
    await selectAndWait(page, 0); // ventilation -> résultats

    await expect(page.locator('h1')).toContainText('Vos résultats');
    // Les scores doivent refléter les réponses (pas des zéros)
    await expect(page.getByText('Score global :')).toBeVisible();
    await expect(page.locator('main')).not.toContainText('0/1100');
  });
});
