/**
 * Publicodes model loader.
 *
 * Imports all .publicodes files (as raw YAML strings), parses them,
 * and exposes the Publicodes Engine and typed helper functions.
 */
import Engine from 'publicodes'
import { load as parseYaml } from 'js-yaml'

// Import .publicodes files as raw strings via the publicodes Vite plugin
import autodiagRules from '../../data/autodiag.publicodes'
import solRules from '../../data/sol.publicodes'
import eauxPluvialesRules from '../../data/eaux-pluviales.publicodes'
import espacesVertsRules from '../../data/espaces-verts.publicodes'
import batimentsRules from '../../data/batiments.publicodes'

// Merge all rules into a single YAML document by concatenation
// (Publicodes supports multi-document YAML, but we need a single merged object)
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
  solRules,
  eauxPluvialesRules,
  espacesVertsRules,
  batimentsRules,
)

// Create the Publicodes engine
export const engine = new Engine<`autodiag . ${string}`>(allRules as never)

// ── Theme score type ───────────────────────────────────────

export interface ThemeScore {
  themeId: string;
  themeLabel: string;
  themeIcon: string;
  score: number;
  description: string;
}

// ── Theme definitions ──────────────────────────────────────

export interface ThemeDef {
  id: string
  label: string
  icon: string
  solutionPageId: number
  description: string
}

export const THEMES: ThemeDef[] = [
  {
    id: 'sol',
    label: 'Sols',
    icon: '🌱',
    solutionPageId: 80,
    description:
      "La désimperméabilisation des sols permet de réduire les îlots de chaleur urbains en favorisant l'infiltration de l'eau de pluie et en permettant la végétalisation.",
  },
  {
    id: 'eaux pluviales',
    label: 'Eaux pluviales',
    icon: '💧',
    solutionPageId: 81,
    description:
      'La valorisation des eaux pluviales contribue au rafraîchissement naturel du site en alimentant le sol et la végétation. De plus elle contribue à réduire les inondations par ruissellement.',
  },
  {
    id: 'espaces verts',
    label: 'Espaces verts',
    icon: '🌳',
    solutionPageId: 82,
    description:
      "Les espaces verts, notamment les arbres réduisent la température ambiante par évapotranspiration et grâce à leur ombrage, essentiels pour le confort des salariés. Alimentés en eau grâce à une gestion des eaux pluviales adaptée et plantés dans un sol perméable, les espaces verts permettent de créer des îlots de rafraîchissement. Ils accueillent également la biodiversité et stockent du carbone.",
  },
  {
    id: 'bâtiments',
    label: 'Bâtiments',
    icon: '🏢',
    solutionPageId: 77,
    description:
      "L'adaptation des bâtiments (isolation, protections solaires, systèmes de rafraîchissement) est cruciale pour maintenir des conditions de travail acceptables lors des vagues de chaleur. Les 2 enjeux sont d'empêcher au maximum la chaleur d'entrer dans le bâtiment puis de pouvoir le rafraîchir avec des solutions efficaces.",
  },
]

// ── Question definitions ───────────────────────────────────

export interface Option {
  label: string
  score: number
  /** The string value used in Publicodes (the option text) */
  value: string
}

export interface Question {
  id: string
  themeId: string
  question: string
  options: Option[]
  nextRoute: string | null
  prevRoute: string | null
}

/**
 * Question IDs in the order they appear in the auto-diagnostic.
 */
const QUESTION_ORDER: string[] = [
  'sol-1',
  'sol-2',
  'eaux-pluviales-1',
  'eaux-pluviales-2',
  'eaux-pluviales-3',
  'espaces-verts-1',
  'espaces-verts-2',
  'batiments-1',
  'batiments-2',
  'batiments-3',
  'batiments-4',
]

/**
 * Mapping from question ID to its theme ID.
 */
const THEME_FOR_QUESTION: Record<string, string> = {
  'sol-1': 'sol',
  'sol-2': 'sol',
  'eaux-pluviales-1': 'eaux pluviales',
  'eaux-pluviales-2': 'eaux pluviales',
  'eaux-pluviales-3': 'eaux pluviales',
  'espaces-verts-1': 'espaces verts',
  'espaces-verts-2': 'espaces verts',
  'batiments-1': 'bâtiments',
  'batiments-2': 'bâtiments',
  'batiments-3': 'bâtiments',
  'batiments-4': 'bâtiments',
}

/**
 * Score mapping for each question.
 * Maps questionId -> option value -> score.
 * Extracted from the Publicodes rules.
 */
type ScoreMap = Record<string, Record<string, number>>

function getScoreMaps(): ScoreMap {
  const maps: ScoreMap = {}

  for (const qId of QUESTION_ORDER) {
    // The score rule lives at: autodiag . thèmes . <theme> . questions . <qId> . score
    // We can evaluate it with the Engine or extract the variations manually.
    // For extraction, we get the rule's parsed definition.
    const scoreRuleName = `autodiag . thèmes . ${THEME_FOR_QUESTION[qId]} . questions . ${qId} . score`
    try {
      const rule = engine.getRule(scoreRuleName as `autodiag . ${string}`)
      // Navigate to the variations to extract score mappings
      // The rule's rawNode contains the formula with variations
      const rawNode = (rule as unknown as { rawNode?: { formule?: { variations?: Array<{ si?: string; alors?: number }> } } }).rawNode
      const variations = rawNode?.formule?.variations
      if (variations) {
        const qMaps: Record<string, number> = {}
        for (const v of variations) {
          if (v.si && v.alors !== undefined) {
            // Extract the option value from the condition string
            // e.g. `autodiag . thèmes . sol . questions . sol-1 = "'Some text'"`
            const match = v.si.match(/= '(.+)'$/)
            if (match) {
              qMaps[match[1]] = v.alors
            }
          }
        }
        maps[qId] = qMaps
      }
    } catch {
      // fallback
    }
  }

  return maps
}

const SCORE_MAPS = getScoreMaps()

function buildQuestions(): Question[] {
  return QUESTION_ORDER.map((qId, i) => {
    const themeId = THEME_FOR_QUESTION[qId]
    const ruleName = `autodiag . thèmes . ${themeId} . questions . ${qId}`

    // Get the question text from the rule
    const rule = engine.getRule(ruleName as `autodiag . ${string}`)
    const metadatas = (rule as unknown as { rawNode?: { question?: string; formule?: unknown } }).rawNode
    const questionText = metadatas?.question ?? qId

    // Get the possibilities (option values)
    const possibilities = engine.getPossibilitiesFor(ruleName as `autodiag . ${string}`)
    const options: Option[] = (possibilities ?? []).map((p) => {
      const val = String(p)
      // Remove surrounding quotes from the value
      const cleanVal = val.replace(/^'|'$/g, '')
      const score = SCORE_MAPS[qId]?.[cleanVal] ?? 0
      return {
        label: cleanVal,
        score,
        value: val,
      }
    })

    return {
      id: qId,
      themeId,
      question: questionText,
      options,
      nextRoute: i < QUESTION_ORDER.length - 1 ? `/${QUESTION_ORDER[i + 1]}` : '/resultats',
      prevRoute: i > 0 ? `/${QUESTION_ORDER[i - 1]}` : null,
    }
  })
}

/**
 * Build the questions the first time they are loaded.
 */
export const QUESTIONS: Question[] = buildQuestions()
export const QUESTION_IDS = QUESTIONS.map((q) => q.id)

// ── Scoring ────────────────────────────────────────────────

export type Answers = Record<string, number>

/**
 * Compute scores for all themes using the Publicodes engine.
 *
 * Takes the user's answers (questionId -> selected option value string)
 * and sets them as the engine situation, then evaluates each theme score.
 */
export function computeScores(answers: Answers): ThemeScore[] {
  // Build the engine situation from answers
  // Publicodes expects: { "autodiag . thèmes . <theme> . questions . <qId>": "'<option value>'" }
  const situation: Record<string, unknown> = {}
  for (const [qId, scoreValue] of Object.entries(answers)) {
    if (scoreValue < 0) continue // "Je ne sais pas" — skip
    const themeId = THEME_FOR_QUESTION[qId]
    if (!themeId) continue

    const ruleName = `autodiag . thèmes . ${themeId} . questions . ${qId}`
    // Find the option label for this score
    const question = QUESTIONS.find((q) => q.id === qId)
    if (!question) continue

    const option = question.options.find((o) => o.score === scoreValue)
    if (!option) continue

    situation[ruleName] = option.value
  }

  // Clone engine and set situation
  const localEngine = engine.shallowCopy()
  localEngine.setSituation(situation as never)

  // Evaluate each theme's score
  return THEMES.map((theme) => {
    const scoreRule = `autodiag . thèmes . ${theme.id} . score`
    try {
      const result = localEngine.evaluate(scoreRule)
      const rawScore = (result as unknown as { nodeValue?: number }).nodeValue ?? 0
      const score = typeof rawScore === 'number' && !Number.isNaN(rawScore) ? rawScore : 0
      return {
        themeId: theme.id,
        themeLabel: theme.label,
        themeIcon: theme.icon,
        score,
        description: theme.description,
      }
    } catch {
      return {
        themeId: theme.id,
        themeLabel: theme.label,
        themeIcon: theme.icon,
        score: 0,
        description: theme.description,
      }
    }
  })
}
