import { defineConfig, devices } from '@playwright/test'

// Every Storybook story of the SPAs (npm run build-storybook, built into
// .cache/storybook/<app>/), and the autodiag journeys on its build
// (npm run build). No database, no CMS.
const port = Number(process.env.STORYBOOK_PORT ?? 6007)
const autodiagPort = Number(process.env.AUTODIAG_PORT ?? 6008)
const isCI = !!process.env.CI

const autodiagServer = {
  command: `npx vite preview --port ${autodiagPort} --strictPort --host 127.0.0.1`,
  cwd: '../apps/autodiag',
  url: `http://127.0.0.1:${autodiagPort}/autodiag/`,
  reuseExistingServer: !isCI,
}

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
  webServer: [
    {
      command: `python3 -m http.server ${port} --bind 127.0.0.1 --directory .cache/storybook`,
      url: `http://127.0.0.1:${port}/autodiag/index.json`,
      reuseExistingServer: !isCI,
      stderr: 'ignore', // the access log of http.server
    },
    // The built autodiag app, for its journeys (spa/autodiag.spec.ts).
    // Skipped by `just e2e-spa-update-snapshots`: in Docker, Vite would load the
    // macOS binaries of node_modules, and the journeys take no screenshot.
    ...(process.env.E2E_STORIES_ONLY ? [] : [autodiagServer]),
  ],
})
