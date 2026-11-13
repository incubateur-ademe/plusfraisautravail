import { test as base, expect } from '@playwright/test'
import { createCoverageReport, isCoverageEnabled } from './coverage'

// 1×1 transparent PNG, served for every media file.
const PLACEHOLDER_PNG = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
  'base64',
)

/**
 * Every test runs offline and fails on uncaught JS errors:
 * - media come from the prod bucket, absent here: a placeholder image instead;
 * - any other origin (analytics, embeds, SPAs in iframes, external links) is
 *   blocked, so a third-party outage never fails the suite.
 */
export const test = base.extend<{ sandbox: void; browserCoverage: boolean }>({
  // Set by spa.config.ts only: the CMS suite has no browser code of ours.
  browserCoverage: [false, { option: true }],

  sandbox: [
    async ({ context, page, baseURL, browserName, browserCoverage }, use) => {
      const collectCoverage = browserCoverage && isCoverageEnabled && browserName === 'chromium'
      if (collectCoverage) await page.coverage.startJSCoverage({ resetOnNavigation: false })
      const origin = new URL(baseURL!).origin
      await context.route('**/*', (route) => {
        const url = new URL(route.request().url())
        if (url.origin !== origin) return route.abort('blockedbyclient')
        if (url.pathname.startsWith('/media/')) {
          return route.fulfill({ contentType: 'image/png', body: PLACEHOLDER_PNG })
        }
        return route.fallback()
      })
      const errors: Error[] = []
      page.on('pageerror', (error) => errors.push(error))
      await use()
      if (collectCoverage) {
        // The page may be gone after a timeout: keep the real failure visible.
        const coverage = await page.coverage.stopJSCoverage().catch(() => [])
        if (coverage.length > 0) await createCoverageReport().add(coverage)
      }
      expect(errors, 'uncaught JavaScript errors').toEqual([])
    },
    { auto: true },
  ],
})

export { expect }
