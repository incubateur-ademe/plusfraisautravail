import type { Preview } from '@storybook/react-vite'
import { MemoryRouter } from 'react-router-dom'
import shared from '../../../e2e/storybook/preview'
import '../src/styles/index.css'

const preview: Preview = {
  ...shared,
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
