/**
 * Named demo scenarios for the alert-widget.
 *
 * Triggered via the `?test` URL flag on the standalone preview (main.tsx).
 * NOT included in the embed bundle - visitors of the live host page can't enable it.
 */
import {
  ApiClient,
  type ElectricitySnapshot,
  type MeteoSnapshot,
} from '@pfat/api-client';

export type ScenarioName = 'full' | 'heatwave' | 'electricity' | 'quiet';

const NOW = new Date().toISOString();

function offsetDate(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

const QUIET_METEO: MeteoSnapshot = {
  active: false,
  departments: [],
  fetched_at: NOW,
  source: 'meteofrance.vigilance',
};

const QUIET_ELECTRICITY: ElectricitySnapshot = {
  days: [
    { date: offsetDate(0), level: 'vert', code: 1, message: "Pas d'alerte" },
    { date: offsetDate(1), level: 'vert', code: 1, message: "Pas d'alerte" },
    { date: offsetDate(2), level: 'vert', code: 1, message: "Pas d'alerte" },
    { date: offsetDate(3), level: 'vert', code: 1, message: "Pas d'alerte" },
  ],
  currently_strained: false,
  upcoming_strain: false,
  fetched_at: NOW,
  source: 'rte.ecowatt',
};

const HEATWAVE_METEO: MeteoSnapshot = {
  active: true,
  departments: [
    {
      code: '13',
      name: 'Bouches-du-Rhône',
      phenomena: [{ id: '6', name: 'canicule', day1: 'orange', day2: 'rouge' }],
    },
    {
      code: '30',
      name: 'Gard',
      phenomena: [{ id: '6', name: 'canicule', day1: 'rouge', day2: 'orange' }],
    },
    {
      code: '84',
      name: 'Vaucluse',
      phenomena: [
        { id: '6', name: 'canicule', day1: 'orange', day2: 'orange' },
        { id: '3', name: 'orages', day1: 'jaune', day2: 'vert' },
      ],
    },
  ],
  fetched_at: NOW,
  source: 'meteofrance.vigilance',
};

const ELECTRICITY_STRAINED: ElectricitySnapshot = {
  days: [
    { date: offsetDate(0), level: 'vert', code: 1, message: "Pas d'alerte" },
    { date: offsetDate(1), level: 'orange', code: 2, message: 'Système électrique tendu' },
    { date: offsetDate(2), level: 'rouge', code: 3, message: 'Coupures probables' },
    { date: offsetDate(3), level: 'vert', code: 1, message: "Pas d'alerte" },
  ],
  currently_strained: false,
  upcoming_strain: true,
  fetched_at: NOW,
  source: 'rte.ecowatt',
};

const SCENARIOS: Record<ScenarioName, { meteo: MeteoSnapshot; electricity: ElectricitySnapshot }> = {
  full: { meteo: HEATWAVE_METEO, electricity: ELECTRICITY_STRAINED },
  heatwave: { meteo: HEATWAVE_METEO, electricity: QUIET_ELECTRICITY },
  electricity: { meteo: QUIET_METEO, electricity: ELECTRICITY_STRAINED },
  quiet: { meteo: QUIET_METEO, electricity: QUIET_ELECTRICITY },
};

const KNOWN_SCENARIOS = new Set(Object.keys(SCENARIOS));

/** Read `?test` / `?test=<name>` from the URL and return the matching scenario, or null. */
export function detectScenario(search: string): ScenarioName | null {
  const params = new URLSearchParams(search);
  if (!params.has('test')) return null;
  const value = params.get('test');
  if (!value) return 'full';
  return KNOWN_SCENARIOS.has(value) ? (value as ScenarioName) : 'full';
}

/** Build an ApiClient backed by an in-process fake fetch returning the chosen scenario. */
export function buildFakeClient(scenario: ScenarioName): ApiClient {
  const { meteo, electricity } = SCENARIOS[scenario];

  const fakeFetch: typeof fetch = async (input) => {
    const url = typeof input === 'string' ? input : (input as Request).url;
    let body: unknown;
    if (url.endsWith('/alerts/meteo')) body = meteo;
    else if (url.endsWith('/alerts/electricity')) body = electricity;
    else body = {};
    return new Response(JSON.stringify(body), {
      status: 200,
      headers: { 'content-type': 'application/json' },
    });
  };

  return new ApiClient({ baseUrl: '/fake', fetch: fakeFetch });
}
