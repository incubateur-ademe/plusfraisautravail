import type { StorybookConfig } from '@storybook/react-vite'

// Uses this app's vite.config.ts. Built into e2e/.cache/storybook/, where the
// Playwright "spa" suite checks every story (e2e/spa.config.ts).
const config: StorybookConfig = {
  framework: '@storybook/react-vite',
  stories: ['../src/**/*.stories.tsx'],
  core: { disableTelemetry: true },
}

export default config
