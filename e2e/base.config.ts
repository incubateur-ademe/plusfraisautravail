import { defineConfig, devices, type ReporterDescription } from '@playwright/test'

// Shared by playwright.config.ts (CMS) and spa.config.ts (SPAs).
export const isCI = !!process.env.CI

export const reporter = (outputFolder: string): ReporterDescription[] =>
  isCI ? [['github'], ['html', { open: 'never', outputFolder }]] : [['list']]

export default defineConfig({
  forbidOnly: isCI,
  retries: isCI ? 2 : 0,
  use: { locale: 'fr-FR', timezoneId: 'Europe/Paris', trace: 'on-first-retry' },
  projects: [
    {
      name: 'chromium',
      // After the device: set at the top level, it does not reach the page.
      use: { ...devices['Desktop Chrome'], contextOptions: { reducedMotion: 'reduce' } },
    },
  ],
})
