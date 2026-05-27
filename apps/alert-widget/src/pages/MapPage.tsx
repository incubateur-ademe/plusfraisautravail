import { useEffect, useMemo, useState } from 'react';
import { ApiClient, type MeteoSnapshot } from '@pfat/api-client';

import { VigilanceMap } from '../components/VigilanceMap';

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
  scenarioBadge?: string;
}

export function MapPage({
  apiBaseUrl,
  client: clientProp,
  phenomena = 'canicule',
  scenarioBadge,
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

  const phenomenaIds = PHENOMENA_OPTIONS[phenomena];
  const subtitle =
    phenomena === 'canicule'
      ? 'Niveau de vigilance canicule par département — Source : Météo-France'
      : 'Niveau de vigilance par département — Source : Météo-France';

  return (
    <>
      <VigilanceMap meteo={meteo} phenomenaIds={phenomenaIds} subtitle={subtitle} />
      {scenarioBadge && (
        <p className="fr-mt-2w fr-text--sm pfat-map-scenario-badge">{scenarioBadge}</p>
      )}
    </>
  );
}
