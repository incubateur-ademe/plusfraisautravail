import { useEffect, useMemo, useState } from 'react';
import { Notice } from '@codegouvfr/react-dsfr/Notice';
import {
  ApiClient,
  type MeteoSnapshot,
  type PhenomenonAlert,
  type Severity,
} from '@pfat/api-client';

import './AlertWidget.css';

const DEFAULT_PREVENTION_URL = 'https://plusfraisautravail.beta.gouv.fr/risques/vigilances/';

const CANICULE_PHENOMENON_ID = '6';
const MAX_DEPARTMENTS_SHOWN = 10;

const SEVERITY_RANK: Record<Severity, number> = {
  vert: 0,
  jaune: 1,
  orange: 2,
  rouge: 3,
};

function maxSeverity(p: PhenomenonAlert): Severity {
  return SEVERITY_RANK[p.day1] >= SEVERITY_RANK[p.day2] ? p.day1 : p.day2;
}

interface CaniculeEntry {
  id: string;
  label: string;
  tone: Severity;
}

function collectCaniculeEntries(snapshot: MeteoSnapshot): CaniculeEntry[] {
  const entries: CaniculeEntry[] = [];
  for (const dept of snapshot.departments) {
    for (const phenom of dept.phenomena) {
      if (phenom.id !== CANICULE_PHENOMENON_ID) continue;
      entries.push({
        id: dept.code,
        label: dept.name,
        tone: maxSeverity(phenom),
      });
    }
  }
  entries.sort((a, b) => a.id.localeCompare(b.id));
  return entries;
}

function highestTone(entries: CaniculeEntry[]): Severity {
  return entries.reduce<Severity>(
    (acc, e) => (SEVERITY_RANK[e.tone] > SEVERITY_RANK[acc] ? e.tone : acc),
    'vert',
  );
}

export interface AlertWidgetProps {
  apiBaseUrl: string;
  preventionUrl?: string;
  /** Kept for backwards compatibility with existing host embeds; currently unused. */
  leversUrl?: string;
  /** Override the API client - used by the demo/test mode to inject canned data. */
  client?: ApiClient;
}

export function AlertWidget({
  apiBaseUrl,
  preventionUrl = DEFAULT_PREVENTION_URL,
  client: clientProp,
}: AlertWidgetProps) {
  const client = useMemo(
    () => clientProp ?? new ApiClient({ baseUrl: apiBaseUrl }),
    [clientProp, apiBaseUrl],
  );

  const [meteo, setMeteo] = useState<MeteoSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [meteoError, setMeteoError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    client
      .getMeteoAlerts()
      .then((snapshot) => {
        if (cancelled) return;
        setMeteo(snapshot);
      })
      .catch((reason: unknown) => {
        if (cancelled) return;
        setMeteoError(reason instanceof Error ? reason.message : 'Erreur inconnue');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [client]);

  if (loading) return null;
  if (meteoError) {
    return (
      <Notice severity="alert" title="Erreur" description={meteoError} isClosable={false} />
    );
  }

  const entries = meteo ? collectCaniculeEntries(meteo) : [];
  if (entries.length === 0) return null;

  const tone = highestTone(entries);
  // Map Vigilance tone -> DSFR Notice severity. Jaune treats like orange.
  const noticeSeverity = tone === 'rouge' ? 'weather-red' : 'weather-orange';

  const shown = entries.slice(0, MAX_DEPARTMENTS_SHOWN);
  const hiddenCount = entries.length - shown.length;
  const departmentList = shown.map((e) => e.label).join(', ');

  const title =
    tone === 'rouge'
      ? 'Vigilance canicule rouge en cours'
      : 'Vigilance canicule en cours';

  const description = (
    <>
      {departmentList}
      {hiddenCount > 0 && (
        <span className="canicule-notice__more"> et {hiddenCount} autres départements</span>
      )}. <br/>
    </>
  );

  return (
    <Notice
      severity={noticeSeverity}
      classes={{ root: 'canicule-notice', title: 'fr-icon-sun-fill' }}
      title={title}
      description={description}
      link={{
        linkProps: { href: preventionUrl },
        text: 'Voir les mesures de prévention',
      }}
      isClosable={false}
    />
  );
}
