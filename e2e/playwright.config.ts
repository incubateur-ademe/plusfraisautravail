import { defineConfig, devices } from '@playwright/test'

// The CMS runs on a database restored from the anonymised prod dump
// (`just e2e-restore`, or e2e/restore.sh in CI).
const port = Number(process.env.E2E_PORT ?? 8765)
const isCI = !!process.env.CI

export default defineConfig({
  testDir: './tests',
  outputDir: './.cache/test-results',
  forbidOnly: isCI,
  retries: isCI ? 2 : 0,
  reporter: isCI
    ? [['github'], ['html', { open: 'never', outputFolder: '.cache/report' }]]
    : [['list']],
  use: {
    baseURL: `http://localhost:${port}`,
    locale: 'fr-FR',
    timezoneId: 'Europe/Paris',
    reducedMotion: 'reduce',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: `uv run python manage.py compilemessages -l fr > /dev/null && uv run python manage.py runserver ${port} --noreload`,
    cwd: '../apps/cms',
    url: `http://localhost:${port}/healthz/`,
    reuseExistingServer: !isCI,
    timeout: 120_000,
    env: {
      DJANGO_SETTINGS_MODULE: 'cms.settings.e2e',
      E2E_PORT: String(port),
    },
  },
})
