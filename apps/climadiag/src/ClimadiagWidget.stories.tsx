import type { Meta, StoryObj } from '@storybook/react-vite'
import { ApiClient, type ClimadiagLieu } from '@pfat/api-client'
import { expect, userEvent, within } from 'storybook/test'
import { ClimadiagWidget } from './ClimadiagWidget'
import { ClimadiagIndicateurs } from './climadiag/Climadiag'

const projection = (min: number, median: number, max: number) => ({ min, median, max })

// Illustrative values, not real Climadiag data.
const CADENET: ClimadiagLieu = {
  id: 1,
  nom: 'Cadenet',
  code_postal: '84160',
  type_lieu: 'commune',
  seuil_jours_tres_chauds: 35,
  seuil_nuits_chaudes: 20,
  jours_tres_chauds_ref: 6,
  nuits_chaudes_ref: 12,
  jours_vdc_ref: 4,
  jours_tres_chauds_prevision: {
    2030: projection(8, 11, 15),
    2050: projection(12, 17, 24),
    2100: projection(18, 29, 41),
  },
  nuits_chaudes_prevision: {
    2030: projection(15, 19, 24),
    2050: projection(21, 28, 36),
    2100: projection(30, 45, 61),
  },
  jours_vdc_prevision: {
    2030: projection(5, 7, 9),
    2050: projection(7, 10, 14),
    2100: projection(10, 16, 23),
  },
}

const fakeClient = new ApiClient({
  baseUrl: '',
  fetch: async () =>
    new Response(JSON.stringify([CADENET]), { headers: { 'content-type': 'application/json' } }),
})

const meta = {
  title: 'Climadiag/Widget',
  component: ClimadiagWidget,
  args: { apiBaseUrl: '', client: fakeClient },
} satisfies Meta<typeof ClimadiagWidget>

export default meta
type Story = StoryObj<typeof meta>

export const Empty: Story = { name: 'Recherche vide' }

export const CommuneSelected: Story = {
  name: 'Commune sélectionnée',
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement)
    await userEvent.type(canvas.getByRole('combobox'), 'Cadenet')
    await userEvent.click(await canvas.findByRole('option', { name: /Cadenet - 84160/ }))
    await expect(await canvas.findByText(/Cadenet/)).toBeVisible()
  },
}

export const Indicateurs: StoryObj<typeof ClimadiagIndicateurs> = {
  name: 'Indicateurs seuls',
  render: () => <ClimadiagIndicateurs climadiagInfo={CADENET} />,
}
