import type { Preview } from '@storybook/react-vite'
import { startReactDsfr } from '@codegouvfr/react-dsfr/spa'
import '@codegouvfr/react-dsfr/main.css'

// Light scheme whatever the OS theme: stable screenshots.
startReactDsfr({ defaultColorScheme: 'light' })

const preview: Preview = { parameters: { layout: 'padded' } }

export default preview
