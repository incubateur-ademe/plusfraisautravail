import { useEffect, useMemo, useState } from 'react';
import { Alert } from '@codegouvfr/react-dsfr/Alert';
import { Tooltip } from '@codegouvfr/react-dsfr/Tooltip';
import {
  ApiClient,
  type ElectricityDayForecast,
  type ElectricityLevel,
  type ElectricitySnapshot,
  type MeteoSnapshot,
  type PhenomenonAlert,
  type Severity,
} from '@pfat/api-client';

const DEFAULT_PREVENTION_URL = 'https://plusfraisautravail.beta.gouv.fr/reglementation/';
const DEFAULT_LEVERS_URL = 'https://plusfraisautravail.beta.gouv.fr/agir/';

const VIGILANCE_METEO_URL = 'https://vigilance.meteofrance.fr/fr';
const VIGILANCE_ECOWATT_URL = 'https://www.monecowatt.fr';

const SUPPORTED_PHENOMENON_IDS = new Set(['3', '6']);

const ELECTRICITY_KEY = 'electricity';

interface PhenomenonCopy {
  label: string;
  message: (leversUrl: string, preventionUrl: string) => React.ReactNode;
}

const PHENOMENON_COPY: Record<string, PhenomenonCopy> = {
  '6': {
    label: 'Canicule',
    message: (leversUrl, preventionUrl) => (
      <>
        <a href={preventionUrl}>Consultez</a> les mesures de préventions règlementaires et{' '}
        <a href={leversUrl}>découvrez</a> tous les leviers à actionner pour anticiper les vagues
        de chaleur.
      </>
    ),
  },
  '3': {
    label: 'Orages',
    message: (leversUrl) => (
      <>
        Des coupures d'électricité peuvent impacter votre activité,{' '}
        <a href={leversUrl}>découvrez les leviers ici</a>.
      </>
    ),
  },
  [ELECTRICITY_KEY]: {
    label: 'Tension électrique',
    message: (leversUrl) => (
      <>
        Risque de tension sur le réseau électrique national : des coupures (délestages) sont
        possibles si la consommation ne baisse pas.{' '}
        <a href={leversUrl}>Découvrez les leviers ici</a>.
      </>
    ),
  },
};

const SEVERITY_RANK: Record<Severity, number> = {
  vert: 0,
  jaune: 1,
  orange: 2,
  rouge: 3,
};

// Météo-France Vigilance official palette. DSFR doesn't expose a true yellow,
// so we override fr-badge colors inline to stay faithful to the Vigilance scale.
const SEVERITY_STYLE: Record<Severity, { background: string; color: string }> = {
  vert: { background: '#1F8D49', color: '#FFFFFF' },
  jaune: { background: '#FFEB3B', color: '#161616' },
  orange: { background: '#FB7F2F', color: '#FFFFFF' },
  rouge: { background: '#CC0000', color: '#FFFFFF' },
};

const ELECTRICITY_STYLE: Record<ElectricityLevel, { background: string; color: string }> = {
  vert: SEVERITY_STYLE.vert,
  orange: SEVERITY_STYLE.orange,
  rouge: SEVERITY_STYLE.rouge,
};

const SEVERITY_LABEL: Record<Severity, string> = {
  vert: 'Vert',
  jaune: 'Jaune',
  orange: 'Orange',
  rouge: 'Rouge',
};

const DATE_FORMATTER = new Intl.DateTimeFormat('fr-FR', {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
});

function formatDay(iso: string): string {
  // ISO date "YYYY-MM-DD" — interpret as local date so Intl picks the right weekday.
  const [y, m, d] = iso.split('-').map((s) => parseInt(s, 10));
  if (!y || !m || !d) return iso;
  return DATE_FORMATTER.format(new Date(y, m - 1, d));
}

function maxSeverity(p: PhenomenonAlert): Severity {
  return SEVERITY_RANK[p.day1] >= SEVERITY_RANK[p.day2] ? p.day1 : p.day2;
}

interface TagEntry {
  id: string;
  label: string;
  tone: Severity | ElectricityLevel;
  tooltip: React.ReactNode;
}

interface PhenomenonGroup {
  key: string;
  entries: TagEntry[];
}

function meteoTooltip(phenomenonLabel: string, p: PhenomenonAlert): React.ReactNode {
  return (
    <>
      <strong>{phenomenonLabel}</strong>
      <br />
      Aujourd'hui : {SEVERITY_LABEL[p.day1]}
      <br />
      Demain : {SEVERITY_LABEL[p.day2]}
      <br />
      <a href={VIGILANCE_METEO_URL} target="_blank" rel="noreferrer noopener">
        Voir sur vigilance.meteofrance.fr
      </a>
    </>
  );
}

function electricityTooltip(d: ElectricityDayForecast): React.ReactNode {
  return (
    <>
      <strong>Tension électrique</strong>
      <br />
      Niveau : {SEVERITY_LABEL[d.level as Severity] ?? d.level}
      {d.message && (
        <>
          <br />
          {d.message}
        </>
      )}
      <br />
      <a href={VIGILANCE_ECOWATT_URL} target="_blank" rel="noreferrer noopener">
        Voir sur monecowatt.fr
      </a>
    </>
  );
}

function groupMeteoByPhenomenon(snapshot: MeteoSnapshot): PhenomenonGroup[] {
  const groups = new Map<string, PhenomenonGroup>();
  for (const dept of snapshot.departments) {
    for (const phenom of dept.phenomena) {
      if (!SUPPORTED_PHENOMENON_IDS.has(phenom.id)) continue;
      let group = groups.get(phenom.id);
      if (!group) {
        group = { key: phenom.id, entries: [] };
        groups.set(phenom.id, group);
      }
      group.entries.push({
        id: dept.code,
        label: dept.name,
        tone: maxSeverity(phenom),
        tooltip: meteoTooltip(PHENOMENON_COPY[phenom.id]?.label ?? phenom.name, phenom),
      });
    }
  }
  for (const g of groups.values()) {
    g.entries.sort((a, b) => a.id.localeCompare(b.id));
  }
  return Array.from(groups.values()).sort((a, b) => {
    if (a.key === '6') return -1;
    if (b.key === '6') return 1;
    return a.key.localeCompare(b.key);
  });
}

function buildElectricityGroup(snapshot: ElectricitySnapshot): PhenomenonGroup | null {
  const strained = snapshot.days.filter((d) => d.level !== 'vert');
  if (strained.length === 0) return null;
  return {
    key: ELECTRICITY_KEY,
    entries: strained.map((d) => ({
      id: d.date,
      label: formatDay(d.date),
      tone: d.level,
      tooltip: electricityTooltip(d),
    })),
  };
}

export interface AlertWidgetProps {
  apiBaseUrl: string;
  preventionUrl?: string;
  leversUrl?: string;
}

export function AlertWidget({
  apiBaseUrl,
  preventionUrl = DEFAULT_PREVENTION_URL,
  leversUrl = DEFAULT_LEVERS_URL,
}: AlertWidgetProps) {
  const client = useMemo(() => new ApiClient({ baseUrl: apiBaseUrl }), [apiBaseUrl]);

  const [meteo, setMeteo] = useState<MeteoSnapshot | null>(null);
  const [electricity, setElectricity] = useState<ElectricitySnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [meteoError, setMeteoError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.allSettled([client.getMeteoAlerts(), client.getElectricityAlerts()])
      .then(([meteoRes, electricityRes]) => {
        if (cancelled) return;
        if (meteoRes.status === 'fulfilled') {
          setMeteo(meteoRes.value);
        } else {
          const reason = meteoRes.reason;
          setMeteoError(reason instanceof Error ? reason.message : 'Erreur inconnue');
        }
        if (electricityRes.status === 'fulfilled') {
          setElectricity(electricityRes.value);
        }
        // Electricity failures are non-fatal — the endpoint is optional and may be
        // 503 when RTE creds aren't configured. Just skip the section.
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [client]);

  if (loading) return <p>Chargement…</p>;
  if (meteoError) {
    return <Alert severity="error" title="Erreur" description={meteoError} small closable={false} />;
  }

  const meteoGroups = meteo ? groupMeteoByPhenomenon(meteo) : [];
  const electricityGroup = electricity ? buildElectricityGroup(electricity) : null;
  const groups = electricityGroup ? [...meteoGroups, electricityGroup] : meteoGroups;

  if (groups.length === 0) return null;

  return (
    <Alert
      severity="warning"
      title="Des alertes (vigilance) sont en cours en France"
      description={
        <div>
          {groups.map((group) => {
            const copy = PHENOMENON_COPY[group.key];
            return (
              <div key={group.key} className="fr-mb-2w">
                <p className="fr-mb-1v">
                  <strong>{copy.label}</strong> :{' '}
                  {group.entries.map((entry, i) => (
                    <span key={entry.id}>
                      <Tag
                        label={entry.label}
                        tone={entry.tone}
                        tooltip={entry.tooltip}
                      />
                      {i < group.entries.length - 1 && ' '}
                    </span>
                  ))}
                </p>
                <p className="fr-mb-0 fr-text--sm">
                  {copy.message(leversUrl, preventionUrl)}
                </p>
              </div>
            );
          })}
        </div>
      }
      closable={false}
    />
  );
}

function Tag({
  label,
  tone,
  tooltip,
}: {
  label: string;
  tone: Severity | ElectricityLevel;
  tooltip: React.ReactNode;
}) {
  const style =
    tone in SEVERITY_STYLE
      ? SEVERITY_STYLE[tone as Severity]
      : ELECTRICITY_STYLE[tone as ElectricityLevel];
  return (
    <Tooltip kind="hover" title={tooltip}>
      <span
        className="fr-badge fr-badge--sm"
        style={{
          backgroundColor: style.background,
          color: style.color,
          marginRight: '0.25rem',
          cursor: 'help',
        }}
        tabIndex={0}
      >
        {label}
      </span>
    </Tooltip>
  );
}
