import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  expect: { timeout: 10000 },
  fullyParallel: true,
  forbidOnly: true,
  retries: 0,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:5201',
    headless: true,
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: 'npx vite --port 5201',
    url: 'http://localhost:5201/autodiag/',
    reuseExistingServer: false,
    cwd: '/Users/fabienlefrapper/Developer/beta.gouv.fr/plusfraisautravail/apps/autodiag',
    timeout: 15000,
  },
});
