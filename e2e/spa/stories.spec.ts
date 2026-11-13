import { readFileSync, readdirSync } from 'node:fs'
import AxeBuilder from '@axe-core/playwright'
import type { Page } from '@playwright/test'
import { expect, test } from '../fixtures'

const STORYBOOKS = new URL('../.cache/storybook/', import.meta.url)
const VIEWPORTS = [320, 768, 1440]

// Accessibility issues already known and not fixed yet, per app. Remove an
// entry once fixed: the suite then guards against its return.
const KNOWN_VIOLATIONS: Record<string, string[]> = {
  // Yellow and orange values on white (Climadiag palette): contrast 2 to 2.9,
  // WCAG asks 4.5. A design decision, to settle with the design team.
  climadiag: ['color-contrast'],
}

interface IndexEntry {
  id: string
  title: string
  name: string
  type: 'story' | 'docs'
}

const stories = readdirSync(STORYBOOKS).flatMap((app) => {
  const index = JSON.parse(readFileSync(new URL(`${app}/index.json`, STORYBOOKS), 'utf8'))
  return (Object.values(index.entries) as IndexEntry[])
    .filter((entry) => entry.type === 'story')
    .map((entry) => ({ app, ...entry }))
})

test('chaque SPA a des stories', () => {
  expect(new Set(stories.map((story) => story.app))).toEqual(
    new Set(['alert-widget', 'autodiag', 'climadiag']),
  )
})

async function renderStory(page: Page, story: (typeof stories)[number]) {
  await page.goto(`/${story.app}/iframe.html?id=${story.id}&viewMode=story`)
  // Rendered, play function included: Storybook's own render phase. In
  // Storybook 10 the last one is `finished`, after `completed` and `afterEach`.
  await page.waitForFunction(() => {
    const phase = (window as { __STORYBOOK_PREVIEW__?: { currentRender?: { phase?: string } } })
      .__STORYBOOK_PREVIEW__?.currentRender?.phase
    return phase === 'finished' || phase === 'errored' || phase === 'aborted'
  })
  // Some stories render nothing on purpose (no vigilance: no widget).
  await expect(page.locator('.sb-show-errordisplay'), 'story error').toHaveCount(0)
}

for (const story of stories) {
  test(`${story.app} › ${story.title} › ${story.name}`, async ({ page }) => {
    await renderStory(page, story)
    const { violations } = await new AxeBuilder({ page })
      .include('#storybook-root')
      .disableRules(KNOWN_VIOLATIONS[story.app] ?? [])
      .analyze()
    expect(violations.map((v) => `${v.id}: ${v.help} (${v.nodes.length})`)).toEqual([])

    for (const width of VIEWPORTS) {
      await page.setViewportSize({ width, height: 900 })
      await expect(page).toHaveScreenshot(`${story.app}/${story.id}-${width}.png`, {
        fullPage: true,
      })
    }
  })
}
