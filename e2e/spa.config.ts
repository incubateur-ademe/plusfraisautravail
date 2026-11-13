import { defineConfig } from '@playwright/test'
import base, { isCI, reporter } from './base.config'

// Every Storybook story of the SPAs (npm run build-storybook, built into
// .cache/storybook/<app>/), and the autodiag journeys on its build
// (npm run build). No database, no CMS.
const port = Number(process.env.STORYBOOK_PORT ?? 6007)
const autodiagPort = Number(process.env.AUTODIAG_PORT ?? 6008)

const autodiagServer = {
  command: `npx vite preview --port ${autodiagPort} --strictPort --host 127.0.0.1`,
  cwd: '../apps/autodiag',
  url: `http://127.0.0.1:${autodiagPort}/autodiag/`,
  reuseExistingServer: !isCI,
}

export default defineConfig(base, {
  testDir: './spa',
  // E2E_COVERAGE=1: browser coverage of the SPAs (coverage.ts).
  globalSetup: './coverage.ts',
  globalTeardown: './coverage-teardown.ts',
  outputDir: './.cache/spa-results',
  // Linux reference screenshots, versioned. Fonts render differently on
  // macOS: compare them in CI or `just e2e-spa-update-snapshots` (Docker) only.
  snapshotPathTemplate: '{testDir}/__screenshots__/{arg}{ext}',
  ignoreSnapshots: !isCI && !process.env.E2E_SNAPSHOTS,
  expect: { toHaveScreenshot: { maxDiffPixelRatio: 0.002 } },
  reporter: reporter('.cache/spa-report'),
  use: { baseURL: `http://127.0.0.1:${port}` },
  // Merged by name with the chromium project of base.config.ts. Browser
  // coverage only with E2E_COVERAGE=1 (coverage.ts).
  projects: [{ name: 'chromium', use: { browserCoverage: true } }],
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
