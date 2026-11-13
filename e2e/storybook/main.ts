import type { StorybookConfig } from '@storybook/react-vite'
import { mergeConfig } from 'vite'

// Storybook of each SPA (apps/*/.storybook), with the app's own vite.config.ts.
// Built into e2e/.cache/storybook/<app>/, where spa.config.ts checks every story.
const config: StorybookConfig = {
  framework: '@storybook/react-vite',
  stories: ['../src/**/*.stories.tsx'], // relative to the app's .storybook/
  core: { disableTelemetry: true },
  // Sourcemaps: the e2e coverage maps the browser's coverage back to src/.
  viteFinal: (viteConfig) => mergeConfig(viteConfig, { build: { sourcemap: true } }),
}

export default config
