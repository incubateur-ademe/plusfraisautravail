import { useMemo, useRef, useState } from 'react';
import type { DepartmentMeteoAlert, MeteoSnapshot, Severity } from '@pfat/api-client';

import { DEPARTMENT_PATHS, DROM_LABELS, VIEW_BOX } from '../data/franceGeo';

const SEVERITY_RANK: Record<Severity, number> = { vert: 0, jaune: 1, orange: 2, rouge: 3 };

const TONE_LABEL: Record<Severity, string> = {
  vert: 'Pas de vigilance',
  jaune: 'Vigilance jaune',
  orange: 'Vigilance orange',
  rouge: 'Vigilance rouge',
};

export interface VigilanceMapProps {
  meteo: MeteoSnapshot;
  /**
   * Restrict the map to a subset of phenomenon IDs (e.g. ['6'] for canicule only).
   * When undefined, all phenomena contribute to each département's tone.
   */
  phenomenaIds?: ReadonlyArray<string>;
  /** Accessible label for the SVG. */
  ariaLabel?: string;
}

type ToneByCode = ReadonlyMap<string, Severity>;

function maxSeverity(a: Severity, b: Severity): Severity {
  return SEVERITY_RANK[a] >= SEVERITY_RANK[b] ? a : b;
}

function deptTone(dept: DepartmentMeteoAlert, phenomenaIds?: ReadonlyArray<string>): Severity {
  let tone: Severity = 'vert';
  for (const p of dept.phenomena) {
    if (phenomenaIds && !phenomenaIds.includes(p.id)) continue;
    tone = maxSeverity(tone, maxSeverity(p.day1, p.day2));
  }
  return tone;
}

function buildToneMap(
  meteo: MeteoSnapshot,
  phenomenaIds?: ReadonlyArray<string>,
): ToneByCode {
  const m = new Map<string, Severity>();
  for (const dept of meteo.departments) m.set(dept.code, deptTone(dept, phenomenaIds));
  return m;
}

export function VigilanceMap({
  meteo,
  phenomenaIds,
  ariaLabel = 'Vigilance canicule en France',
}: VigilanceMapProps) {
  const tones = useMemo(() => buildToneMap(meteo, phenomenaIds), [meteo, phenomenaIds]);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [hovered, setHovered] = useState<{
    code: string;
    name: string;
    tone: Severity;
    x: number;
    y: number;
  } | null>(null);

  const updateHover = (
    code: string,
    name: string,
    tone: Severity,
    clientX: number,
    clientY: number,
  ) => {
    const rect = wrapperRef.current?.getBoundingClientRect();
    if (!rect) return;
    setHovered({ code, name, tone, x: clientX - rect.left, y: clientY - rect.top });
  };

  return (
    <div className="pfat-map-card">
      <div className="pfat-map-wrapper" ref={wrapperRef}>
        <svg
          viewBox={VIEW_BOX}
          role="img"
          aria-label={ariaLabel}
          className="pfat-map-svg"
        >
          {DEPARTMENT_PATHS.map((p) => {
            const tone = tones.get(p.code) ?? 'vert';
            return (
              <path
                key={p.code}
                d={p.d}
                className={`pfat-map-dept pfat-map-dept--${tone}`}
                tabIndex={0}
                role="button"
                aria-label={`${p.code} ${p.name} : ${TONE_LABEL[tone]}`}
                onPointerMove={(e) => updateHover(p.code, p.name, tone, e.clientX, e.clientY)}
                onPointerLeave={() => setHovered(null)}
                onFocus={(e) => {
                  const r = (e.currentTarget as SVGPathElement).getBoundingClientRect();
                  updateHover(p.code, p.name, tone, r.left + r.width / 2, r.top);
                }}
                onBlur={() => setHovered(null)}
              />
            );
          })}
          {DROM_LABELS.map((label) => (
            <text
              key={label.code}
              x={label.cx}
              y={label.labelY}
              className="pfat-map-drom-label"
              textAnchor="middle"
            >
              {label.code}
            </text>
          ))}
        </svg>
        {hovered && (
          <div
            className="pfat-map-tooltip"
            role="tooltip"
            style={{ left: `${hovered.x}px`, top: `${hovered.y}px` }}
          >
            <strong>
              {hovered.code} – {hovered.name}
            </strong>
            <br />
            {TONE_LABEL[hovered.tone]}
          </div>
        )}
      </div>

      <ul className="pfat-map-legend">
        <li>
          <span className="pfat-map-legend__swatch pfat-map-legend__swatch--vert" />
          Pas de vigilance
        </li>
        <li>
          <span className="pfat-map-legend__swatch pfat-map-legend__swatch--jaune" />
          Vigilance jaune
        </li>
        <li>
          <span className="pfat-map-legend__swatch pfat-map-legend__swatch--orange" />
          Vigilance orange
        </li>
        <li>
          <span className="pfat-map-legend__swatch pfat-map-legend__swatch--rouge" />
          Vigilance rouge
        </li>
      </ul>
    </div>
  );
}
