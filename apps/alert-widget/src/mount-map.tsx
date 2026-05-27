import { StrictMode, useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { ApiClient, type MeteoSnapshot } from '@pfat/api-client';

import { VigilanceMap } from './components/VigilanceMap';
import mapCss from './components/VigilanceMap.css?inline';
import { buildFakeClient, type ScenarioName } from './demo';

const CANICULE_PHENOMENON_ID = '6';

const HOST_BASE_STYLE = `
:host {
  display: block;
  font: inherit;
  color: #161616;
  /* DSFR weather tokens, inlined so the host page does not need DSFR. */
  --weather-green-main-525: #3eaa3e;
  --weather-yellow-main-525: #fff100;
  --weather-orange-main-525: #ff9100;
  --weather-red-main-525: #cc0000;
  --background-default-grey: #ffffff;
  --text-title-grey: #161616;
  --text-mention-grey: #666666;
}
`;

interface MountMapOptions {
  /** Either a CSS selector or an element to mount into. */
  target?: string | HTMLElement;
  /** API base URL the map calls for vigilance data. */
  apiBaseUrl: string;
  /** Comma-separated phenomenon IDs (e.g. "6" for canicule). Omit for all. */
  phenomena?: string;
  /** Use canned fixtures instead of calling the API. */
  demo?: ScenarioName;
}

interface MapMountProps {
  apiBaseUrl: string;
  phenomenaIds?: ReadonlyArray<string>;
  demo?: ScenarioName;
}

function MapMount({ apiBaseUrl, phenomenaIds, demo }: MapMountProps) {
  const client = useMemo(
    () => (demo ? buildFakeClient(demo) : new ApiClient({ baseUrl: apiBaseUrl })),
    [apiBaseUrl, demo],
  );
  const [meteo, setMeteo] = useState<MeteoSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    client
      .getMeteoAlerts()
      .then((snapshot) => {
        if (!cancelled) setMeteo(snapshot);
      })
      .catch((reason: unknown) => {
        if (cancelled) return;
        setError(reason instanceof Error ? reason.message : 'Erreur inconnue');
      });
    return () => {
      cancelled = true;
    };
  }, [client]);

  if (error) return <p role="alert">Carte indisponible : {error}</p>;
  if (!meteo) return <p>Chargement de la carte…</p>;
  return <VigilanceMap meteo={meteo} phenomenaIds={phenomenaIds} />;
}

function parsePhenomena(value: string | undefined): ReadonlyArray<string> | undefined {
  if (!value) return undefined;
  if (value === 'all') return undefined;
  if (value === 'canicule') return [CANICULE_PHENOMENON_ID];
  // Allow raw comma-separated IDs for flexibility ("6,3").
  const ids = value.split(',').map((s) => s.trim()).filter(Boolean);
  return ids.length > 0 ? ids : undefined;
}

function resolveTarget(target: MountMapOptions['target']): HTMLElement {
  if (target === undefined) {
    // Default: create a div the consumer can style. If they want to control
    // position, they pass `target` explicitly.
    const el = document.createElement('div');
    el.id = 'pfat-vigilance-map';
    document.body.appendChild(el);
    return el;
  }
  const el = typeof target === 'string' ? document.querySelector(target) : target;
  if (!el) throw new Error(`PfatVigilanceMap: target "${String(target)}" not found`);
  return el as HTMLElement;
}

function mount(options: MountMapOptions): void {
  const host = resolveTarget(options.target);
  const shadow = host.attachShadow({ mode: 'open' });

  const style = document.createElement('style');
  style.textContent = HOST_BASE_STYLE + mapCss;
  shadow.appendChild(style);

  const reactRoot = document.createElement('div');
  shadow.appendChild(reactRoot);

  createRoot(reactRoot).render(
    <StrictMode>
      <MapMount
        apiBaseUrl={options.apiBaseUrl}
        phenomenaIds={parsePhenomena(options.phenomena)}
        demo={options.demo}
      />
    </StrictMode>,
  );
}

declare global {
  interface Window {
    PfatVigilanceMap?: { mount: (options: MountMapOptions) => void };
  }
}

window.PfatVigilanceMap = { mount };
