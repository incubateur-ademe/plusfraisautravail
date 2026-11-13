import { defineConfig, devices } from '@playwright/test'

// Every Storybook story of the SPAs (npm run build-storybook, built into
// .cache/storybook/<app>/). No database, no CMS.
const port = Number(process.env.STORYBOOK_PORT ?? 6007)
const isCI = !!process.env.CI

export default defineConfig({
  testDir: './spa',
  outputDir: './.cache/spa-results',
  // Linux reference screenshots, versioned. Fonts render differently on
  // macOS: compare them in CI or `just e2e-spa-update-snapshots` (Docker) only.
  snapshotPathTemplate: '{testDir}/__screenshots__/{arg}{ext}',
  ignoreSnapshots: !isCI && !process.env.E2E_SNAPSHOTS,
  expect: { toHaveScreenshot: { maxDiffPixelRatio: 0.002 } },
  forbidOnly: isCI,
  retries: isCI ? 2 : 0,
  reporter: isCI
    ? [['github'], ['html', { open: 'never', outputFolder: '.cache/spa-report' }]]
    : [['list']],
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    locale: 'fr-FR',
    timezoneId: 'Europe/Paris',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      // After the device: set at the top level, it does not reach the page.
      use: { ...devices['Desktop Chrome'], contextOptions: { reducedMotion: 'reduce' } },
    },
  ],
  webServer: {
    command: `python3 -m http.server ${port} --bind 127.0.0.1 --directory .cache/storybook`,
    url: `http://127.0.0.1:${port}/autodiag/index.json`,
    reuseExistingServer: !isCI,
    stderr: 'ignore', // the access log of http.server
  },
})
