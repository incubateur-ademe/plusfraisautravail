import type { Climadiag } from './climadiag/types';

// ponytail: fake but plausible demo values. Their /api/search-climadiag-info is
// session-gated (401 anonymous) — swap this module for a fetch once we get API access.
export const sampleClimadiag: Climadiag[] = [
  {
    id: 1,
    nom: 'Paris',
    code_postal: '75001',
    type_lieu: 'commune',
    seuil_jours_tres_chauds: 32,
    seuil_nuits_chaudes: 20,
    jours_tres_chauds_ref: 2,
    nuits_chaudes_ref: 2,
    jours_vdc_ref: 9,
    jours_tres_chauds_prevision: {
      2030: { min: 4, median: 6, max: 9 },
      2050: { min: 6, median: 9, max: 14 },
      2100: { min: 10, median: 17, max: 32 },
    },
    nuits_chaudes_prevision: {
      2030: { min: 5, median: 8, max: 12 },
      2050: { min: 9, median: 14, max: 21 },
      2100: { min: 16, median: 28, max: 48 },
    },
    jours_vdc_prevision: {
      2030: { min: 13, median: 17, max: 23 },
      2050: { min: 17, median: 24, max: 33 },
      2100: { min: 26, median: 41, max: 63 },
    },
  },
  {
    id: 2,
    nom: 'Lyon',
    code_postal: '69001',
    type_lieu: 'commune',
    seuil_jours_tres_chauds: 33,
    seuil_nuits_chaudes: 21,
    jours_tres_chauds_ref: 3,
    nuits_chaudes_ref: 3,
    jours_vdc_ref: 10,
    jours_tres_chauds_prevision: {
      2030: { min: 6, median: 9, max: 13 },
      2050: { min: 9, median: 13, max: 19 },
      2100: { min: 15, median: 24, max: 41 },
    },
    nuits_chaudes_prevision: {
      2030: { min: 7, median: 11, max: 16 },
      2050: { min: 12, median: 18, max: 27 },
      2100: { min: 21, median: 36, max: 58 },
    },
    jours_vdc_prevision: {
      2030: { min: 15, median: 20, max: 27 },
      2050: { min: 20, median: 28, max: 39 },
      2100: { min: 31, median: 48, max: 72 },
    },
  },
  {
    id: 3,
    nom: 'Marseille',
    code_postal: '13001',
    type_lieu: 'commune',
    seuil_jours_tres_chauds: 32,
    seuil_nuits_chaudes: 23,
    jours_tres_chauds_ref: 4,
    nuits_chaudes_ref: 5,
    jours_vdc_ref: null,
    jours_tres_chauds_prevision: {
      2030: { min: 8, median: 12, max: 17 },
      2050: { min: 12, median: 17, max: 24 },
      2100: { min: 20, median: 31, max: 50 },
    },
    nuits_chaudes_prevision: {
      2030: { min: 10, median: 15, max: 22 },
      2050: { min: 17, median: 25, max: 36 },
      2100: { min: 29, median: 47, max: 71 },
    },
    jours_vdc_prevision: null,
  },
];
