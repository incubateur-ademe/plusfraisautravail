/**
 * Publicodes-based questions and scoring engine.
 *
 * This replaces the previous YAML-based data with a Publicodes model.
 * The model files live in data/*.publicodes and are compiled at build time.
 *
 * All existing consumer interfaces are preserved for backward compatibility.
 */
export {
  engine,
  THEMES,
  QUESTIONS,
  QUESTION_IDS,
  computeScores,
} from './model'

export type {
  Option,
  Question,
  ThemeDef as Theme,
  Answers,
  ThemeScore,
} from './model'
