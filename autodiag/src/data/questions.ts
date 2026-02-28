import rawData from '../../../questions.yaml'

export interface Option {
  label: string;
  score: number;
}

export interface Question {
  id: string;
  themeId: string;
  themeLabel: string;
  themeIcon: string;
  solutionPageId: number;
  question: string;
  options: Option[];
  nextRoute: string | null;
  prevRoute: string | null;
}

export interface ThemeScore {
  themeId: string;
  themeLabel: string;
  themeIcon: string;
  score: number;
  description: string;
}

interface RawQuestion {
  id: string;
  themeId: string;
  themeLabel: string;
  themeIcon: string;
  solutionPageId: number;
  question: string;
  options: Option[];
}

interface RawData {
  questions: RawQuestion[];
}

function buildQuestions(raw: RawQuestion[]): Question[] {
  return raw.map((q, i) => ({
    ...q,
    nextRoute: i < raw.length - 1 ? `/${raw[i + 1].id}` : '/resultats',
    prevRoute: i > 0 ? `/${raw[i - 1].id}` : null,
  }));
}

export const QUESTIONS: Question[] = buildQuestions((rawData as RawData).questions);

export type Answers = Record<string, number>;

export function computeScores(answers: Answers): ThemeScore[] {
  const THEME_DESCRIPTIONS: Record<string, string> = {
    sol: "La désimperméabilisation des sols permet de réduire les îlots de chaleur urbains en favorisant l'infiltration de l'eau et en permettant la végétalisation.",
    'eaux-pluviales':
      'La valorisation des eaux pluviales contribue au rafraîchissement naturel du site et réduit les ruissellements qui amplifient les effets de chaleur.',
    'espaces-verts':
      "Les espaces verts, notamment les arbres, créent de l'ombre et réduisent la température ambiante par évapotranspiration, essentiels pour le confort des salariés.",
    batiments:
      "L'adaptation des bâtiments (isolation, protections solaires, systèmes de rafraîchissement) est cruciale pour maintenir des conditions de travail acceptables lors des vagues de chaleur.",
  };

  // Compute BÂTIMENTS as average of batiments-1 and batiments-2
  const batimentsScores: number[] = [];
  if (answers['batiments-1'] !== undefined) batimentsScores.push(answers['batiments-1']);
  if (answers['batiments-2'] !== undefined) batimentsScores.push(answers['batiments-2']);
  const batimentsAvg =
    batimentsScores.length > 0
      ? batimentsScores.reduce((a, b) => a + b, 0) / batimentsScores.length
      : 0;

  return [
    {
      themeId: 'sol',
      themeLabel: 'Sol',
      themeIcon: '🌱',
      score: answers['sol'] ?? 0,
      description: THEME_DESCRIPTIONS['sol'],
    },
    {
      themeId: 'eaux-pluviales',
      themeLabel: 'Eaux pluviales',
      themeIcon: '💧',
      score: answers['eaux-pluviales'] ?? 0,
      description: THEME_DESCRIPTIONS['eaux-pluviales'],
    },
    {
      themeId: 'espaces-verts',
      themeLabel: 'Espaces verts',
      themeIcon: '🌳',
      score: answers['espaces-verts'] ?? 0,
      description: THEME_DESCRIPTIONS['espaces-verts'],
    },
    {
      themeId: 'batiments',
      themeLabel: 'Bâtiments',
      themeIcon: '🏢',
      score: batimentsAvg,
      description: THEME_DESCRIPTIONS['batiments'],
    },
  ];
}

export const QUESTION_IDS = QUESTIONS.map((q) => q.id);
