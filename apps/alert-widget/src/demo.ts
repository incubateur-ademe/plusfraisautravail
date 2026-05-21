/**
 * Named demo scenarios for the alert-widget.
 *
 * Triggered via the `?test` URL flag on the standalone preview (main.tsx) and
 * via the `data-demo` script attribute / `demo` mount option on the embed bundle.
 */
import { ApiClient, type MeteoSnapshot, type Severity } from '@pfat/api-client';

export type ScenarioName = 'heatwave' | 'heatwave-orange' | 'heatwave-rouge' | 'quiet';

const NOW = new Date().toISOString();

const QUIET_METEO: MeteoSnapshot = {
  active: false,
  departments: [],
  fetched_at: NOW,
  source: 'meteofrance.vigilance',
};

interface DeptSpec {
  code: string;
  name: string;
  tone: Severity;
}

const SOUTH_DEPTS: ReadonlyArray<Omit<DeptSpec, 'tone'>> = [
  { code: '04', name: 'Alpes-de-Haute-Provence' },
  { code: '11', name: 'Aude' },
  { code: '13', name: 'Bouches-du-Rhône' },
  { code: '26', name: 'Drôme' },
  { code: '30', name: 'Gard' },
  { code: '34', name: 'Hérault' },
  { code: '66', name: 'Pyrénées-Orientales' },
  { code: '69', name: 'Rhône' },
  { code: '83', name: 'Var' },
  { code: '84', name: 'Vaucluse' },
  { code: '06', name: 'Alpes-Maritimes' },
  { code: '07', name: 'Ardèche' },
  { code: '38', name: 'Isère' },
  { code: '73', name: 'Savoie' },
];

function buildDepartments(specs: ReadonlyArray<DeptSpec>): MeteoSnapshot['departments'] {
  return specs.map(({ code, name, tone }) => ({
    code,
    name,
    phenomena: [{ id: '6', name: 'canicule', day1: tone, day2: tone }],
  }));
}

function buildSnapshot(specs: ReadonlyArray<DeptSpec>): MeteoSnapshot {
  return {
    active: true,
    departments: buildDepartments(specs),
    fetched_at: NOW,
    source: 'meteofrance.vigilance',
  };
}

const ORANGE_SCENARIO = buildSnapshot(
  SOUTH_DEPTS.map((d) => ({ ...d, tone: 'orange' as Severity })),
);

const ROUGE_SCENARIO = buildSnapshot(
  SOUTH_DEPTS.map((d, i) => ({ ...d, tone: i < 4 ? ('rouge' as Severity) : ('orange' as Severity) })),
);

// Mixed scenario - keeps the original "heatwave" behaviour with a non-canicule
// phenomenon on Vaucluse so we can verify filtering.
const MIXED_HEATWAVE: MeteoSnapshot = {
  active: true,
  fetched_at: NOW,
  source: 'meteofrance.vigilance',
  departments: ORANGE_SCENARIO.departments.map((dept) =>
    dept.code === '13'
      ? { ...dept, phenomena: [{ id: '6', name: 'canicule', day1: 'orange', day2: 'rouge' }] }
      : dept.code === '84'
        ? {
            ...dept,
            phenomena: [
              { id: '6', name: 'canicule', day1: 'orange', day2: 'orange' },
              { id: '3', name: 'orages', day1: 'jaune', day2: 'vert' },
            ],
          }
        : dept,
  ),
};

const SCENARIOS: Record<ScenarioName, { meteo: MeteoSnapshot }> = {
  heatwave: { meteo: MIXED_HEATWAVE },
  'heatwave-orange': { meteo: ORANGE_SCENARIO },
  'heatwave-rouge': { meteo: ROUGE_SCENARIO },
  quiet: { meteo: QUIET_METEO },
};

const KNOWN_SCENARIOS = new Set<ScenarioName>([
  'heatwave',
  'heatwave-orange',
  'heatwave-rouge',
  'quiet',
]);

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
