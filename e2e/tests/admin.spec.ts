import { expect, test } from '../fixtures'

// Account created by e2e/restore.sh: the dump has no usable password.
test('un compte éditeur se connecte à l’admin', async ({ page }) => {
  await page.goto('/cms-admin/login/')
  await page.getByRole('textbox', { name: /utilisateur/i }).fill('e2e')
  // Wagtail leaves this label untranslated ("Password").
  await page.getByRole('textbox', { name: /mot de passe|password/i }).fill('e2e')
  await page.getByRole('button', { name: /s.identifier/i }).click()
  await expect(page).toHaveURL(/\/cms-admin\/$/)
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
})
