import { defineConfig } from '@playwright/test'
import base, { isCI, reporter } from './base.config'

// The CMS runs on a database restored from the anonymised prod dump
// (`just e2e-restore`, or e2e/restore.sh in CI).
const port = Number(process.env.E2E_PORT ?? 8765)
// E2E_COVERAGE=1: the CMS runs under coverage.py, to measure what the e2e
// tests exercise on the server (report: see README.md).
const python = process.env.E2E_COVERAGE
  ? 'coverage run --data-file=../../e2e/.cache/coverage/server.coverage'
  : 'python'

export default defineConfig(base, {
  testDir: './tests',
  outputDir: './.cache/test-results',
  reporter: reporter('.cache/report'),
  use: { baseURL: `http://localhost:${port}`, screenshot: 'only-on-failure' },
  webServer: {
    command: `uv run python manage.py compilemessages -l fr > /dev/null && uv run ${python} manage.py runserver ${port} --noreload`,
    gracefulShutdown: { signal: 'SIGTERM', timeout: 10_000 },
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
