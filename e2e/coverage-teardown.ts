import { createCoverageReport, isCoverageEnabled } from './coverage'

/** globalTeardown: merge the coverage of every test into one report. */
export default async function generateCoverage() {
  if (isCoverageEnabled) await createCoverageReport().generate()
}
