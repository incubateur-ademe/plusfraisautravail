import type { Meta, StoryObj } from '@storybook/react-vite'
import { buildFakeClient } from '../demo'
import { MapPage } from './MapPage'

const meta = {
  title: 'Alerte canicule/Carte des vigilances',
  component: MapPage,
  args: { apiBaseUrl: '' },
} satisfies Meta<typeof MapPage>

export default meta
type Story = StoryObj<typeof meta>

export const Quiet: Story = { name: 'Pas de vigilance', args: { client: buildFakeClient('quiet') } }
export const Rouge: Story = {
  name: 'Vigilance rouge',
  args: { client: buildFakeClient('heatwave-rouge') },
}
