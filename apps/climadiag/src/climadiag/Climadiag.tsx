// Port of plusfraichemaville-site src/components/climadiag/* (commit 36b2669)
// Next.js/prisma/tailwind removed; one file, plain CSS. Skipped: PDF export, async search panel.
import { useState } from 'react';
import { climadiagIndicateursData, climadiagColorLegend } from './data';
import type { Climadiag, ClimadiagTemperatureJour, ClimadiagTypeJour, ClimadiagYear } from './types';
import './climadiag.css';

const img = (file: string) => `${import.meta.env.BASE_URL}images/climadiag/${file}`;

const YEARS: ClimadiagYear[] = [2030, 2050, 2100];

// ── Tab button (with the "France + température" badge) ──────────────────────
const TabButton = ({
  active,
  year,
  changeTab,
}: {
  active: boolean;
  year: ClimadiagYear;
  changeTab: (year: ClimadiagYear) => void;
}) => {
  const temperature = year === 2030 ? 2 : year === 2050 ? 2.7 : 4;
  return (
    <button
      className={`cd-tab${active ? ' cd-tab--active' : ''}`}
      role="radio"
      aria-checked={active}
      onClick={() => changeTab(year)}
    >
      {year}
      {active && (
        <div className="cd-tab-badge">
          <span className="cd-tab-badge-temp">+{temperature}°C</span>
          <svg viewBox="0 0 50 50">
            <rect width="50" height="50" fill="#6a6af4" rx="25" ry="25"></rect>
            <path
              fill="none"
              stroke="#fff"
              strokeLinejoin="round"
              strokeMiterlimit="10"
              strokeWidth="1.4"
              d="M40.431 32.771V33c-.075.232-.15.47-.226.693-.143.423-.04.748.315 1.059.703.54 1.407 1.08 2.027 1.625.615.462.638.874-.002 1.408-1.127.81-2.25 1.703-3.377 2.514a2 2 0 01-1.658.344 146 146 0 00-5.781-1.243c-.596-.131-1.18-.098-1.747.266-.482.36-1.053.64-1.54.916-.488.277-.72.622-.69 1.117.02.33-.045.666-.025.996-.045.666-.37.85-1.05.723-1.702-.4-3.482-.712-5.185-1.111-1.279-.341-2.524-.104-3.789-.198-.507-.053-1.014-.106-1.447-.33-1.294-.588-2.508-1.264-3.807-1.935-.777-.37-.88-.695-.678-1.535.68-2.69 1.365-5.3 2.13-7.995.133-.587.183-1.17-.102-1.734-1.14-2.254-2.197-4.514-3.254-6.773-.197-.486-.546-.715-1.063-.934L5.38 19.617c-.684-.21-1.127-.596-1.338-1.33-.113-.49-.309-.978-.422-1.469-.211-.733-.058-.99.69-1.115.502-.029 1.164-.15 2.08-.285 1.58-.256 3.106-.014 4.818.55.517.22 1.111.353 1.623.489.428.141.59.047.477-.443a508 508 0 00-.436-3.123c-.132-.821.109-1.001.965-.72 1.028.356 2.145.79 3.178 1.227.6.215 1.02.19 1.586-.173 1.206-.898 2.499-1.718 3.705-2.616.482-.359.792-.79.925-1.379.129-.67.253-1.422.465-2.097.133-.588.457-.773 1.037-.889q.342-.081.66-.086c.637-.01 1.217.207 1.807.608 2.194 1.614 4.466 3.14 6.576 4.76.876.612 1.731.896 2.819.833.92-.052 1.684.068 2.318.86s1.642.817 2.572.93c.168-.01.34.063.424.058.68.127.866.448.817 1.031-.122.94-.328 1.845-.471 2.762v.116"
            ></path>
          </svg>
        </div>
      )}
    </button>
  );
};

// ── One value cell (référence / basse / médiane / haute) ────────────────────
const LineJour = ({
  withBackground,
  valeur,
  jour,
}: {
  withBackground?: boolean;
  valeur?: 'basse' | 'médiane' | 'haute';
  jour: number | null;
}) => {
  const colorClass =
    valeur === 'basse' ? 'cd-basse' : valeur === 'médiane' ? 'cd-mediane' : valeur === 'haute' ? 'cd-haute' : 'cd-grey';
  return (
    <div className={`cd-jour${withBackground ? ' cd-jour--bg' : ''}`}>
      <div className={`cd-jour-valeur ${colorClass}`}>
        {jour == null ? (
          <span className="cd-jour-nombre">N.R.</span>
        ) : (
          <>
            <span className="cd-jour-nombre">{Math.round(jour)} </span>
            {Math.round(jour) > 1 ? 'jours' : 'jour'}
          </>
        )}
      </div>
      <div className="cd-jour-label">
        <span>valeur</span>
        <span>{valeur ?? 'de référence'}</span>
      </div>
    </div>
  );
};

// ── Legend under a line ──────────────────────────────────────────────────────
const LineLegend = ({ legend, year }: { legend: string[]; year: ClimadiagYear }) => (
  <div className="cd-legend">
    <p className="cd-legend-text">
      {legend.map((line, index) => (
        <span key={index}>{line}</span>
      ))}
    </p>
    <div className="cd-legend-colors">
      {climadiagColorLegend.map((d, index) => (
        <div className="cd-legend-color" key={index}>
          <div className={`cd-dot ${d.color}`}></div>
          <p>
            {d.label} {year}
          </p>
        </div>
      ))}
    </div>
  </div>
);

// ── One indicator line ───────────────────────────────────────────────────────
const IndicateursLine = ({
  type,
  temperature,
  year,
  seuil,
}: {
  type: ClimadiagTypeJour;
  temperature: ClimadiagTemperatureJour;
  year: ClimadiagYear;
  seuil?: number | null;
}) => {
  const { title, picto, legend: climatLegend } = climadiagIndicateursData[type];
  const [legend, setLegend] = useState(false);

  return (
    <div className="cd-line-card">
      <div className="cd-line">
        <div className="cd-line-info">
          <img src={img(`${picto}.svg`)} width={100} height={100} alt="" />
          <div>
            <h4 className="cd-line-title">{title}</h4>
            {seuil != null && <span className="cd-line-seuil">({'>'}{seuil}°C)</span>}
            <button onClick={() => setLegend(!legend)} className="cd-line-toggle">
              {!legend ? 'Afficher la légende' : 'Masquer la légende'}
            </button>
          </div>
        </div>
        <div className="cd-line-jours">
          <LineJour jour={temperature.ref} withBackground />
          <LineJour jour={temperature.prevision.min} valeur="basse" />
          <div className="cd-sep-y" />
          <LineJour jour={temperature.prevision.median} valeur="médiane" />
          <div className="cd-sep-y" />
          <LineJour jour={temperature.prevision.max} valeur="haute" />
        </div>
      </div>
      {legend && <LineLegend legend={climatLegend(seuil ?? 0)[year]} year={year} />}
    </div>
  );
};

// ── Main component ───────────────────────────────────────────────────────────
export const ClimadiagIndicateurs = ({ climadiagInfo }: { climadiagInfo: Climadiag }) => {
  const [selectedYear, setSelectedYear] = useState<ClimadiagYear>(2030);

  return (
    <div className="cd-root">
      <h3 className="cd-city">📍 {climadiagInfo.nom} {climadiagInfo.code_postal}</h3>
      <div className="cd-tabs">
        <div>
          {YEARS.map((year) => (
            <TabButton key={year} changeTab={setSelectedYear} year={year} active={selectedYear === year} />
          ))}
          <span className="cd-tabs-note">
            horizons (TRACC, 2024)<sup>*</sup>
          </span>
        </div>
        <a
          className="cd-mf-link"
          target="_blank"
          rel="noreferrer"
          href="https://climadiag-commune.meteofrance.com/"
        >
          <img src={img('climadiag-meteo-france.png')} width={136} height={48} alt="Logo Météo France Climadiag" />
          <img src={img('meteo-france.svg')} width={48} height={48} alt="Logo Météo France" />
        </a>
      </div>
      <IndicateursLine
        year={selectedYear}
        temperature={{
          prevision: climadiagInfo.jours_tres_chauds_prevision[selectedYear],
          ref: climadiagInfo.jours_tres_chauds_ref,
        }}
        type="jours_chauds"
        seuil={climadiagInfo.seuil_jours_tres_chauds}
      />
      <IndicateursLine
        year={selectedYear}
        temperature={{
          prevision: climadiagInfo.nuits_chaudes_prevision[selectedYear],
          ref: climadiagInfo.nuits_chaudes_ref,
        }}
        type="nuits_chaudes"
        seuil={climadiagInfo.seuil_nuits_chaudes}
      />
      {climadiagInfo.jours_vdc_prevision && (
        <IndicateursLine
          year={selectedYear}
          temperature={{
            prevision: climadiagInfo.jours_vdc_prevision[selectedYear],
            ref: climadiagInfo.jours_vdc_ref,
          }}
          type="jours_vdc"
        />
      )}
      <div className="cd-copyright">Les données Climadiag sont la propriété exclusive de Météo-France.</div>
      <div className="cd-tracc">
        * Ces projections tiennent compte de la Trajectoire de Réchauffement et d’Adaptation au Changement Climatique
        (TRACC) correspondant à une hausse des températures moyennes en France hexagonale et en Corse de +4°C en 2100.
      </div>
    </div>
  );
};
