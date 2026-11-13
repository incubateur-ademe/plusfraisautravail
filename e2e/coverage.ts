import { rmSync } from 'node:fs'
import MCR, { type CoverageReportOptions } from 'monocart-coverage-reports'

// Browser coverage of the SPAs (E2E_COVERAGE=1): Chromium's V8 coverage of
// every test, mapped back to apps/*/src through the sourcemaps.
export const isCoverageEnabled = !!process.env.E2E_COVERAGE

const options: CoverageReportOptions = {
  name: 'Couverture front des tests e2e',
  outputDir: './.cache/coverage/front',
  reports: ['console-summary', 'markdown-summary', 'lcovonly'],
  // Bundled scripts only (they carry the sourcemaps), then our code only:
  // no dependencies, stories, assets or inline scripts of the HTML pages.
  entryFilter: (entry) =>
    /\/assets\/.+\.js$/.test(new URL(entry.url).pathname) && !entry.url.includes('preload-helper'),
  sourceFilter: (path) =>
    /(^|\/)src\//.test(path) &&
    !path.includes('node_modules') &&
    !path.includes('.stories.') &&
    /\.(tsx?|jsx?)$/.test(path),
  // The app build (autodiag journeys) names its sources src/..., Storybook
  // apps/<app>/src/...: same files, one name, taken from the served path.
  sourcePath: (path, { distFile }) => {
    const app = distFile?.split('/')[1]
    return path.startsWith('src/') && app ? `apps/${app}/${path}` : path
  },
}

export const createCoverageReport = () => MCR(options)

/** globalSetup: forget the previous run. */
export default function clearCoverage() {
  if (isCoverageEnabled) rmSync(options.outputDir!, { recursive: true, force: true })
}
