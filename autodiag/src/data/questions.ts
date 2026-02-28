import rawQuestions from '../../../questions.yaml'
import rawThemes from '../../../themes.yaml'

export interface Option {
  label: string;
  score: number;
}

export interface Theme {
  id: string;
  label: string;
  icon: string;
  solutionPageId: number;
  description: string;
}

export interface Question {
  id: string;
  themeId: string;
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
  question: string;
  options: Option[];
}

interface RawTheme {
  id: string;
  label: string;
  icon: string;
  solutionPageId: number;
  description: string;
}

const THEMES_BY_ID: Record<string, Theme> = {};
for (const t of (rawThemes as { themes: RawTheme[] }).themes) {
  THEMES_BY_ID[t.id] = t;
}

export const THEMES: Theme[] = (rawThemes as { themes: RawTheme[] }).themes;

function buildQuestions(raw: RawQuestion[]): Question[] {
  return raw.map((q, i) => ({
    ...q,
    nextRoute: i < raw.length - 1 ? `/${raw[i + 1].id}` : '/resultats',
    prevRoute: i > 0 ? `/${raw[i - 1].id}` : null,
  }));
}

export const QUESTIONS: Question[] = buildQuestions(
  (rawQuestions as { questions: RawQuestion[] }).questions
);

export type Answers = Record<string, number>;

export function computeScores(answers: Answers): ThemeScore[] {
  return THEMES.map((theme) => {
    const themeQuestions = QUESTIONS.filter((q) => q.themeId === theme.id);
    const scores = themeQuestions
      .map((q) => answers[q.id])
      .filter((s) => s !== undefined && s >= 0);
    const avg = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;

    return {
      themeId: theme.id,
      themeLabel: theme.label,
      themeIcon: theme.icon,
      score: avg,
      description: theme.description,
    };
  });
}

export const QUESTION_IDS = QUESTIONS.map((q) => q.id);
