/**
 * Publicodes model loader — v2 (Construction)
 *
 * Nouvelle structure : 5 blocs (contexte, désimperméabilisation, eaux pluviales,
 * îlots de rafraîchissement, bâtiments) + organisation du travail.
 *
 * Navigation conditionnelle (même principe que Nos Gestes Climat) :
 * les questions sont posées dans un ordre fixe (QUESTION_ORDER) et la
 * question suivante est la première non encore posée dont la règle
 * Publicodes est applicable. Les sauts de l'arbre de décision
 * (cf. questions.pdf) sont encodés dans les fichiers .publicodes via
 * « applicable si » / « non applicable si » — le modèle est la seule
 * source de vérité de l'enchaînement.
 *
 * Scores : 0-100 par question, somme par bloc (max 200-400).
 */

import Engine from 'publicodes'
import { load as parseYaml } from 'js-yaml'

// Import des fichiers .publicodes
import autodiagRules from '../../data/autodiag.publicodes'
import desimpermeabilisationRules from '../../data/desimpermeabilisation.publicodes'
import eauxPluvialesRules from '../../data/eaux-pluviales.publicodes'
import ilotsRules from '../../data/ilots-de-rafraichissement.publicodes'
import batimentsRules from '../../data/batiments.publicodes'

function mergeRules(...yamlStrings: string[]): Record<string, unknown> {
  const merged: Record<string, unknown> = {}
  for (const yamlStr of yamlStrings) {
    const parsed = parseYaml(yamlStr) as Record<string, unknown> | undefined
    if (parsed) {
      Object.assign(merged, parsed)
    }
  }
  return merged
}

const allRules = mergeRules(
  autodiagRules,
  desimpermeabilisationRules,
  eauxPluvialesRules,
  ilotsRules,
  batimentsRules,
)

export const engine = new Engine(allRules as never)

// ── Types ──────────────────────────────────────────────────

export interface ThemeScore {
  blocId: string
  blocLabel: string
  blocIcon: string
  score: number
  maxScore: number
  description: string
}

export interface Option {
  label: string
  score: number
  /** The string value used in Publicodes (the option text) */
  value: string
}

export interface Question {
  id: string
  blocId: string
  blocLabel: string
  blocIcon: string
  question: string
  options: Option[]
  /** Previous question in linear history (set at runtime via FormContext) */
  prevRoute: string | null
}

// ── Bloc definitions ───────────────────────────────────────

export interface BlocDef {
  id: string
  label: string
  icon: string
  description: string
  maxScore: number
  solutionPageId?: number
}

export const BLOCS: BlocDef[] = [
  {
    id: 'contexte',
    label: 'Contexte',
    icon: '📋',
    description: 'Questions préalables sur votre organisation.',
    maxScore: 0,
  },
  {
    id: 'désimperméabilisation des sols',
    label: 'Désimperméabilisation des sols',
    icon: '🌱',
    description:
      "Désimperméabiliser les sols, c'est passer du bitume à des revêtements de sols perméables et créer les meilleures conditions possibles pour accueillir vos plantations.",
    maxScore: 200,
  },
  {
    id: 'eaux pluviales',
    label: 'Eaux pluviales',
    icon: '💧',
    description:
      "Infiltrer l'eau de pluie dans le sol permet d'éviter le ruissellement et d'amener de l'humidité dans le sol, condition indispensable à la survie de vos plantations.",
    maxScore: 300,
  },
  {
    id: 'îlots de rafraîchissement',
    label: 'Îlots de rafraîchissement',
    icon: '🌳',
    description:
      "La végétation (arbres, arbustes...) peut apporter de l'ombre et contribuer à rafraîchir les zones de travail.",
    maxScore: 200,
  },
  {
    id: 'bâtiments',
    label: 'Bâtiments',
    icon: '🏢',
    description:
      "Préserver la fraîcheur dans le bâtiment, c'est à la fois limiter l'entrée de la chaleur et rafraîchir l'air de façon sobre et vertueuse.",
    maxScore: 400,
  },
]

/** @deprecated Use BLOCS instead */
export const THEMES = BLOCS

export const BLOC_BY_ID: Record<string, BlocDef> = {}
for (const b of BLOCS) {
  BLOC_BY_ID[b.id] = b
}

// ── Question definitions ───────────────────────────────────

const BLOC_FOR_QUESTION: Record<string, string> = {
  'contexte.q1': 'contexte',
  'contexte.q2': 'contexte',
  'desimpermeabilisation.q1': 'désimperméabilisation des sols',
  'desimpermeabilisation.q2': 'désimperméabilisation des sols',
  'eaux-pluviales.q1': 'eaux pluviales',
  'eaux-pluviales.q2': 'eaux pluviales',
  'eaux-pluviales.q3': 'eaux pluviales',
  'ilots-rafraichissement.q1': 'îlots de rafraîchissement',
  'ilots-rafraichissement.q2': 'îlots de rafraîchissement',
  'batiments.q1': 'bâtiments',
  'batiments.q2': 'bâtiments',
  'batiments.q2bis': 'bâtiments',
  'batiments.q2ter': 'bâtiments',
}

const SHORT_ID_FOR_QUESTION: Record<string, string> = {
  'contexte.q1': 'q1',
  'contexte.q2': 'q2',
  'desimpermeabilisation.q1': 'q1',
  'desimpermeabilisation.q2': 'q2',
  'eaux-pluviales.q1': 'q1',
  'eaux-pluviales.q2': 'q2',
  'eaux-pluviales.q3': 'q3',
  'ilots-rafraichissement.q1': 'q1',
  'ilots-rafraichissement.q2': 'q2',
  'batiments.q1': 'q1',
  'batiments.q2': 'q2',
  'batiments.q2bis': 'q2bis',
  'batiments.q2ter': 'q2ter',
}

const QUESTION_ORDER: string[] = [
  'contexte.q1',
  'contexte.q2',
  'desimpermeabilisation.q1',
  'desimpermeabilisation.q2',
  'eaux-pluviales.q1',
  'eaux-pluviales.q2',
  'eaux-pluviales.q3',
  'ilots-rafraichissement.q1',
  'ilots-rafraichissement.q2',
  'batiments.q1',
  'batiments.q2',
  'batiments.q2bis',
  'batiments.q2ter',
]

/**
 * Publicodes string literals escape apostrophes by doubling them (''), and
 * that escaping leaks into rule raw nodes and possibility values. Normalize
 * once here; everything (labels, matching) uses the normalized form.
 */
function unescapeQuotes(s: string): string {
  return s.replace(/''/g, "'")
}

/** Nom de la règle Publicodes correspondant à une question du parcours. */
function ruleNameForQuestion(qId: string): string | null {
  const blocId = BLOC_FOR_QUESTION[qId]
  const shortId = SHORT_ID_FOR_QUESTION[qId]
  if (!blocId || !shortId) return null
  return `autodiag . ${blocId} . questions . ${shortId}`
}

function getScoreForValue(scoreRuleName: string, optionValue: string): number {
  try {
    const rule = engine.getRule(scoreRuleName as never)
    const rawNode = (rule as unknown as { rawNode?: { formule?: { variations?: Array<{ si?: string; alors?: number }> } } }).rawNode
    const variations = rawNode?.formule?.variations
    if (variations) {
      for (const v of variations) {
        if (v.si) {
          const match = v.si.match(/= '(.+)'\s*$/)
          if (match && unescapeQuotes(match[1]) === unescapeQuotes(optionValue)) {
            return v.alors ?? 0
          }
        }
      }
    }
  } catch {
    // fallback
  }
  return 0
}

function buildQuestions(): Question[] {
  const questions: Question[] = []

  for (const qId of QUESTION_ORDER) {
    const blocId = BLOC_FOR_QUESTION[qId]
    if (!blocId) {
      console.warn(`No bloc for question ${qId}`)
      continue
    }
    const bloc = BLOC_BY_ID[blocId]
    if (!bloc) {
      console.warn(`No bloc definition for ${blocId}`)
      continue
    }

    const shortId = SHORT_ID_FOR_QUESTION[qId]
    if (!shortId) {
      console.warn(`No short ID mapping for ${qId}`)
      continue
    }
    const ruleName = `autodiag . ${blocId} . questions . ${shortId}`

    let questionText = qId
    try {
      const rule = engine.getRule(ruleName as never)
      const rawNode = (rule as unknown as { rawNode?: { question?: string } }).rawNode
      questionText = rawNode?.question ?? qId
    } catch {
      // fallback
    }

    let possibilities: unknown[] = []
    try {
      const p = engine.getPossibilitiesFor(ruleName as never)
      possibilities = p ?? []
    } catch {
      // fallback
    }

    const options: Option[] = possibilities.map((p) => {
      // nodeValue is the text as written in the YAML (keeps '' escaping) — used for the Publicodes situation
      const rawValue = String((p as { nodeValue?: unknown }).nodeValue ?? p)
      return {
        label: unescapeQuotes(rawValue),
        score: getScoreForValue(`${ruleName} . score`, rawValue),
        value: rawValue,
      }
    })

    questions.push({
      id: qId,
      blocId,
      blocLabel: bloc.label,
      blocIcon: bloc.icon,
      question: questionText,
      options,
      prevRoute: null,
    })
  }

  return questions
}

export const QUESTIONS: Question[] = buildQuestions()
export const QUESTION_IDS = QUESTIONS.map((q) => q.id)

// ── Helpers ────────────────────────────────────────────────

export function getQuestionById(id: string): Question | undefined {
  return QUESTIONS.find((q) => q.id === id)
}

export const FIRST_QUESTION_ID = 'contexte.q1'

// ── Situation & navigation ─────────────────────────────────

export type Answers = Record<string, number>
export type AnswerLabels = Record<string, string>

/**
 * Construit la situation Publicodes à partir des réponses.
 * Les labels qui ne correspondent à aucune option (« Je ne sais pas »,
 * anciennes entrées localStorage) sont simplement ignorés.
 */
function buildSituation(answerLabels: AnswerLabels): Record<string, string> {
  const situation: Record<string, string> = {}
  for (const [qId, selectedLabel] of Object.entries(answerLabels)) {
    if (!selectedLabel) continue
    const question = getQuestionById(qId)
    if (!question) continue
    const option = question.options.find((o) => o.label === unescapeQuotes(selectedLabel))
    if (!option) continue
    const ruleName = ruleNameForQuestion(qId)
    if (!ruleName) continue
    situation[ruleName] = `'${option.value}'`
  }
  return situation
}

function engineWithSituation(answerLabels: AnswerLabels) {
  const localEngine = engine.shallowCopy()
  localEngine.setSituation(buildSituation(answerLabels) as never)
  return localEngine
}

/**
 * Une question est posée sauf si sa règle est explicitement non applicable
 * (« applicable si » / « non applicable si » dans les .publicodes).
 * Une applicabilité indéterminée (réponse manquante ou « Je ne sais pas »
 * en amont) vaut « applicable » : on préfère poser une question de trop
 * que d'en sauter une à tort.
 */
export function isQuestionApplicable(
  questionId: string,
  answerLabels: AnswerLabels,
  localEngine = engineWithSituation(answerLabels),
): boolean {
  const ruleName = ruleNameForQuestion(questionId)
  if (!ruleName) return true
  try {
    const result = localEngine.evaluate({ 'est applicable': ruleName } as never)
    return (result as unknown as { nodeValue?: unknown }).nodeValue !== false
  } catch {
    return true
  }
}

/**
 * Prochaine question du parcours : la première question après `questionId`
 * (dans l'ordre fixe QUESTION_ORDER) dont la règle est applicable au vu des
 * réponses données. Retourne null en fin de questionnaire (→ résultats).
 */
export function getNextQuestionId(questionId: string, answerLabels: AnswerLabels): string | null {
  const currentIndex = QUESTION_ORDER.indexOf(questionId)
  if (currentIndex === -1) return null

  const localEngine = engineWithSituation(answerLabels)
  for (const candidateId of QUESTION_ORDER.slice(currentIndex + 1)) {
    if (isQuestionApplicable(candidateId, answerLabels, localEngine)) {
      return candidateId
    }
  }
  return null
}

// ── Scoring ────────────────────────────────────────────────

export function computeScores(answerLabels: AnswerLabels): ThemeScore[] {
  const localEngine = engineWithSituation(answerLabels)

  return BLOCS.map((bloc) => {
    if (bloc.maxScore === 0) {
      return {
        blocId: bloc.id,
        blocLabel: bloc.label,
        blocIcon: bloc.icon,
        score: 0,
        maxScore: 0,
        description: bloc.description,
      }
    }

    // Somme par question plutôt que la règle « bloc . score » : une question
    // sans réponse (« Je ne sais pas », branche sautée) rend la somme
    // Publicodes indéfinie, alors qu'on veut juste la compter pour 0.
    let total = 0
    for (const qId of QUESTION_ORDER) {
      if (BLOC_FOR_QUESTION[qId] !== bloc.id) continue
      const shortId = SHORT_ID_FOR_QUESTION[qId]
      try {
        const result = localEngine.evaluate(`autodiag . ${bloc.id} . questions . ${shortId} . score`)
        const value = (result as unknown as { nodeValue?: unknown }).nodeValue
        if (typeof value === 'number' && !Number.isNaN(value)) {
          total += value
        }
      } catch {
        // question sans réponse ou règle absente → 0
      }
    }

    return {
      blocId: bloc.id,
      blocLabel: bloc.label,
      blocIcon: bloc.icon,
      score: Math.min(total, bloc.maxScore),
      maxScore: bloc.maxScore,
      description: bloc.description,
    }
  })
}
