// Port of plusfraichemaville-site src/components/climadiag/types.ts
// (prisma types inlined — we don't have their DB).

export type ClimadiagTemperatureProjection = {
  min: number | null;
  median: number | null;
  max: number | null;
};

export type ClimadiagYear = 2030 | 2050 | 2100;

export type ProjectionsIndicateurClimadiag = Record<ClimadiagYear, ClimadiagTemperatureProjection>;

export type Climadiag = {
  id: number;
  nom: string;
  code_postal: string;
  type_lieu: 'commune' | 'epci';
  seuil_jours_tres_chauds: number | null;
  seuil_nuits_chaudes: number | null;
  jours_tres_chauds_ref: number | null;
  nuits_chaudes_ref: number | null;
  jours_vdc_ref: number | null;
  jours_tres_chauds_prevision: ProjectionsIndicateurClimadiag;
  nuits_chaudes_prevision: ProjectionsIndicateurClimadiag;
  jours_vdc_prevision: ProjectionsIndicateurClimadiag | null;
};

export type ClimadiagTemperatureJour = {
  prevision: ClimadiagTemperatureProjection;
  ref: number | null;
};

export type ClimadiagTypeJour = 'jours_chauds' | 'nuits_chaudes' | 'jours_vdc';
