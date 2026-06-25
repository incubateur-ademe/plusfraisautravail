/**
 * Publicodes-based questions and scoring engine — v2 (Construction).
 *
 * Re-exports from model.ts for backward compatibility with existing components.
 */
export {
  engine,
  BLOCS,
  BLOCS as THEMES,
  BLOC_BY_ID,
  QUESTIONS,
  QUESTION_IDS,
  FIRST_QUESTION_ID,
  getQuestionById,
  getNextQuestionId,
  computeScores,
} from './model'

export type {
  Option,
  Question,
  BlocDef,
  BlocDef as Theme,
  Answers,
  ThemeScore,
} from './model'
