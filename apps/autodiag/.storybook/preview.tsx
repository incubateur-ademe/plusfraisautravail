import type { Preview } from '@storybook/react-vite'
import { startReactDsfr } from '@codegouvfr/react-dsfr/spa'
import { MemoryRouter } from 'react-router-dom'
import '@codegouvfr/react-dsfr/main.css'
import '../src/styles/index.css'

// Light scheme whatever the OS theme: stable screenshots.
startReactDsfr({ defaultColorScheme: 'light' })

const preview: Preview = {
  parameters: { layout: 'padded' },
  // Some components navigate (ProgressHeader): give them a router.
  decorators: [
    (Story) => (
      <MemoryRouter>
        <Story />
      </MemoryRouter>
    ),
  ],
}

export default preview
