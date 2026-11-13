import type { Meta, StoryObj } from '@storybook/react-vite'
import { ApiClient } from '@pfat/api-client'
import { AlertWidget } from './AlertWidget'
import { buildFakeClient } from './demo'

// Same canned data as the demo mode (?test=<scenario>, see demo.ts).
const meta = {
  title: 'Alerte canicule/Widget',
  component: AlertWidget,
  args: { apiBaseUrl: '' },
} satisfies Meta<typeof AlertWidget>

export default meta
type Story = StoryObj<typeof meta>

export const Quiet: Story = { name: 'Pas de vigilance', args: { client: buildFakeClient('quiet') } }
export const Heatwave: Story = { name: 'Canicule', args: { client: buildFakeClient('heatwave') } }
export const Orange: Story = {
  name: 'Vigilance orange',
  args: { client: buildFakeClient('heatwave-orange') },
}
export const Rouge: Story = {
  name: 'Vigilance rouge',
  args: { client: buildFakeClient('heatwave-rouge') },
}
export const ApiDown: Story = {
  name: 'API indisponible',
  args: {
    client: new ApiClient({ baseUrl: '', fetch: () => Promise.reject(new Error('API indisponible')) }),
  },
}
