/**
 * Named demo scenarios for the alert-widget.
 *
 * Triggered via the `?test` URL flag on the standalone preview (main.tsx).
 * NOT included in the embed bundle - visitors of the live host page can't enable it.
 */
import { ApiClient, type MeteoSnapshot } from '@pfat/api-client';

export type ScenarioName = 'heatwave' | 'quiet';

const NOW = new Date().toISOString();

const QUIET_METEO: MeteoSnapshot = {
  active: false,
  departments: [],
  fetched_at: NOW,
  source: 'meteofrance.vigilance',
};

const HEATWAVE_DEPARTMENTS: MeteoSnapshot['departments'] = [
  { code: '04', name: 'Alpes-de-Haute-Provence', phenomena: [{ id: '6', name: 'canicule', day1: 'orange', day2: 'orange' }] },
  { code: '11', name: 'Aude', phenomena: [{ id: '6', name: 'canicule', day1: 'orange', day2: 'orange' }] },
  { code: '13', name: 'Bouches-du-Rhône', phenomena: [{ id: '6', name: 'canicule', day1: 'orange', day2: 'rouge' }] },
  { code: '26', name: 'Drôme', phenomena: [{ id: '6', name: 'canicule', day1: 'orange', day2: 'orange' }] },
  { code: '30', name: 'Gard', phenomena: [{ id: '6', name: 'canicule', day1: 'orange', day2: 'orange' }] },
  { code: '34', name: 'Hérault', phenomena: [{ id: '6', name: 'canicule', day1: 'orange', day2: 'orange' }] },
  { code: '66', name: 'Pyrénées-Orientales', phenomena: [{ id: '6', name: 'canicule', day1: 'orange', day2: 'orange' }] },
  { code: '69', name: 'Rhône', phenomena: [{ id: '6', name: 'canicule', day1: 'orange', day2: 'orange' }] },
  { code: '83', name: 'Var', phenomena: [{ id: '6', name: 'canicule', day1: 'orange', day2: 'orange' }] },
  {
    code: '84',
    name: 'Vaucluse',
    phenomena: [
      { id: '6', name: 'canicule', day1: 'orange', day2: 'orange' },
      // Non-canicule phenomenon to verify the widget filters it out.
      { id: '3', name: 'orages', day1: 'jaune', day2: 'vert' },
    ],
  },
  { code: '06', name: 'Alpes-Maritimes', phenomena: [{ id: '6', name: 'canicule', day1: 'orange', day2: 'orange' }] },
  { code: '07', name: 'Ardèche', phenomena: [{ id: '6', name: 'canicule', day1: 'orange', day2: 'orange' }] },
  { code: '38', name: 'Isère', phenomena: [{ id: '6', name: 'canicule', day1: 'orange', day2: 'orange' }] },
  { code: '73', name: 'Savoie', phenomena: [{ id: '6', name: 'canicule', day1: 'orange', day2: 'orange' }] },
];

const HEATWAVE_METEO: MeteoSnapshot = {
  active: true,
  departments: HEATWAVE_DEPARTMENTS,
  fetched_at: NOW,
  source: 'meteofrance.vigilance',
};

const SCENARIOS: Record<ScenarioName, { meteo: MeteoSnapshot }> = {
  heatwave: { meteo: HEATWAVE_METEO },
  quiet: { meteo: QUIET_METEO },
};

const KNOWN_SCENARIOS = new Set<ScenarioName>(['heatwave', 'quiet']);

function isScenarioName(value: string): value is ScenarioName {
  return (KNOWN_SCENARIOS as Set<string>).has(value);
}

/** Read `?test` / `?test=<name>` from the URL and return the matching scenario, or null. */
export function detectScenario(search: string): ScenarioName | null {
  const params = new URLSearchParams(search);
  if (!params.has('test')) return null;
  const value = params.get('test');
  if (!value) return 'heatwave';
  return isScenarioName(value) ? value : 'heatwave';
}

/** Build an ApiClient backed by an in-process fake fetch returning the chosen scenario. */
export function buildFakeClient(scenario: ScenarioName): ApiClient {
  const { meteo } = SCENARIOS[scenario];

  const fakeFetch: typeof fetch = async (input) => {
    const url = typeof input === 'string' ? input : (input as Request).url;
    const body = url.endsWith('/alerts/meteo') ? meteo : {};
    return new Response(JSON.stringify(body), {
      status: 200,
      headers: { 'content-type': 'application/json' },
    });
  };

  return new ApiClient({ baseUrl: '/fake', fetch: fakeFetch });
}
