import { useEffect, useMemo, useState } from 'react';
import { Select } from '@codegouvfr/react-dsfr/Select';
import { Alert } from '@codegouvfr/react-dsfr/Alert';
import {
  ApiClient,
  isVigilanceActive,
  type DepartmentAlert,
  type Severity,
} from '@pfat/api-client';

import { DEPARTMENTS } from './departments';

const STORAGE_KEY = 'pfat.alert-widget.dept';

const SEVERITY_LABEL: Record<Severity, string> = {
  vert: 'Vert',
  jaune: 'Jaune',
  orange: 'Orange',
  rouge: 'Rouge',
};

const SEVERITY_TO_DSFR: Record<Severity, 'success' | 'info' | 'warning' | 'error'> = {
  vert: 'success',
  jaune: 'info',
  orange: 'warning',
  rouge: 'error',
};

export interface AlertWidgetProps {
  apiBaseUrl: string;
  preventionUrl?: string;
  leversUrl?: string;
  initialDepartment?: string;
}

export function AlertWidget({
  apiBaseUrl,
  preventionUrl = '#',
  leversUrl = '#',
  initialDepartment,
}: AlertWidgetProps) {
  const client = useMemo(() => new ApiClient({ baseUrl: apiBaseUrl }), [apiBaseUrl]);

  const [dept, setDept] = useState<string>(() => {
    if (initialDepartment) return initialDepartment;
    if (typeof window !== 'undefined') {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored) return stored;
    }
    return '';
  });

  const [data, setData] = useState<DepartmentAlert | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!dept) {
      setData(null);
      return;
    }
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, dept);
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    client
      .getHeatwaveForDepartment(dept)
      .then((snapshot) => {
        if (cancelled) return;
        setData(snapshot.departments[0] ?? null);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : 'Erreur inconnue');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [client, dept]);

  const active = data ? isVigilanceActive(data.day1) || isVigilanceActive(data.day2) : false;

  return (
    <div>
      <Select
        label="Votre département"
        nativeSelectProps={{
          value: dept,
          onChange: (e) => setDept(e.target.value),
        }}
      >
        <option value="">Sélectionnez un département…</option>
        {DEPARTMENTS.map((d) => (
          <option key={d.code} value={d.code}>
            {d.code} — {d.name}
          </option>
        ))}
      </Select>

      {loading && <p>Chargement…</p>}
      {error && (
        <Alert severity="error" title="Erreur" description={error} small closable={false} />
      )}

      {data && !loading && (
        <div className="fr-mt-2w">
          <Alert
            severity={SEVERITY_TO_DSFR[data.day1]}
            title={`Vigilance canicule : ${SEVERITY_LABEL[data.day1]} (aujourd'hui)`}
            description={
              <span>
                Demain : {SEVERITY_LABEL[data.day2]}.
                {active && (
                  <>
                    {' '}
                    <a href={preventionUrl}>Consultez</a> les mesures de préventions
                    règlementaires et <a href={leversUrl}>découvrez</a> pour aller plus loin tous
                    les leviers à actionner pour anticiper les vagues de chaleur.
                  </>
                )}
              </span>
            }
            small
            closable={false}
          />
        </div>
      )}
    </div>
  );
}
