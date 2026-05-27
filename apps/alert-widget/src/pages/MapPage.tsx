import { useEffect, useMemo, useState } from 'react';
import { ApiClient, type MeteoSnapshot } from '@pfat/api-client';

import { VigilanceMap } from '../components/VigilanceMap';
import '../components/VigilanceMap.css';

const CANICULE_PHENOMENON_ID = '6';
const PHENOMENA_OPTIONS = {
  canicule: [CANICULE_PHENOMENON_ID] as ReadonlyArray<string>,
  all: undefined,
} as const;

type PhenomenaFilter = keyof typeof PHENOMENA_OPTIONS;

export interface MapPageProps {
  apiBaseUrl: string;
  /** Override the API client (used by demo mode to inject canned data). */
  client?: ApiClient;
  /** Which phenomena to colour the map by. Defaults to 'canicule'. */
  phenomena?: PhenomenaFilter;
}

export function MapPage({
  apiBaseUrl,
  client: clientProp,
  phenomena = 'canicule',
}: MapPageProps) {
  const client = useMemo(
    () => clientProp ?? new ApiClient({ baseUrl: apiBaseUrl }),
    [clientProp, apiBaseUrl],
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

  if (error) {
    return (
      <p className="fr-text--lg" role="alert">
        Erreur : {error}
      </p>
    );
  }
  if (!meteo) {
    return <p>Chargement…</p>;
  }

  return <VigilanceMap meteo={meteo} phenomenaIds={PHENOMENA_OPTIONS[phenomena]} />;
}
