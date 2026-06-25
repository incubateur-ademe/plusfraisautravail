/**
 * Publicodes model loader — v2 (Construction)
 *
 * Nouvelle structure : 5 blocs (contexte, désimperméabilisation, eaux pluviales,
 * îlots de rafraîchissement, bâtiments) + organisation du travail.
 * Navigation conditionnelle : chaque option a un champ "suivant" qui détermine
 * la question suivante (ou null pour terminer le questionnaire).
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
  /** Next question ID (null = terminal question / fin du questionnaire) */
  suivant: string | null
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

/**
 * Définition du graphe de navigation : chaque entrée = { id, suivant par option }.
 * "suivant": null = terminal (fin du questionnaire).
 * Le point de départ est "contexte.q1".
 */
const QUESTION_GRAPH: Record<string, Array<{ optionValue: string; nextId: string | null }>> = {
  'contexte.q1': [
    { optionValue: 'Oui', nextId: 'desimpermeabilisation.q1' },
    { optionValue: 'Non', nextId: 'contexte.q2' },
  ],
  'contexte.q2': [
    { optionValue: "Oui, à l'intérieur et à l'extérieur", nextId: 'desimpermeabilisation.q1' },
    { optionValue: "Oui, uniquement à l'intérieur", nextId: 'batiments.q1' },
    { optionValue: "Oui, uniquement à l'extérieur", nextId: 'desimpermeabilisation.q1' },
    { optionValue: 'Non', nextId: 'resultats' },
  ],
  'desimpermeabilisation.q1': [
    { optionValue: "La plupart des surfaces sont bétonnées ou goudronnées (cour, parking...)", nextId: 'desimpermeabilisation.q2' },
    { optionValue: "Il y a à la fois des surfaces bétonnées/goudronnées et des zones perméables (espaces verts, béton poreux...)", nextId: 'desimpermeabilisation.q2' },
    { optionValue: "La majorité des sols sont perméables, et l''eau de pluie peut s''infiltrer", nextId: 'eaux-pluviales.q1' },
  ],
  'desimpermeabilisation.q2': [
    { optionValue: "Non, rien n'a été fait pour le moment", nextId: 'eaux-pluviales.q1' },
    { optionValue: "Oui, on y réfléchit ou on a commencé à se renseigner (étude de faisabilité programmée ou en cours, ADOPTA, GRAIE...)", nextId: 'eaux-pluviales.q1' },
    { optionValue: "Oui, des actions sont prévues (travaux programmés ou en cours...)", nextId: 'eaux-pluviales.q1' },
    { optionValue: "Oui, des aménagements ont déjà été réalisés", nextId: 'eaux-pluviales.q1' },
  ],
  'eaux-pluviales.q1': [
    { optionValue: "Elle est principalement évacuée vers le réseau d'assainissement (canalisations, égouts...)", nextId: 'eaux-pluviales.q2' },
    { optionValue: "Une partie est évacuée dans le réseau d'assainissement, une autre s'infiltre sur place", nextId: 'eaux-pluviales.q2' },
    { optionValue: "Elle s'infiltre majoritairement sur place (espaces verts, chaussées perméables...)", nextId: 'eaux-pluviales.q2' },
  ],
  'eaux-pluviales.q2': [
    { optionValue: "Non, rien n'a été fait pour le moment", nextId: 'eaux-pluviales.q3' },
    { optionValue: "Oui, on y réfléchit ou on a commencé à se renseigner (agence de l'eau, ADOPTA, GRAIE...)", nextId: 'eaux-pluviales.q3' },
    { optionValue: "Oui, des actions sont prévues (travaux de végétalisation interceptant les ruissellements prévus ou en cours...)", nextId: 'eaux-pluviales.q3' },
    { optionValue: "Oui, des aménagements ont déjà été réalisés (travaux de végétalisation interceptant les ruissellements déjà réalisés...)", nextId: 'eaux-pluviales.q3' },
  ],
  'eaux-pluviales.q3': [
    { optionValue: 'Non', nextId: 'ilots-rafraichissement.q1' },
    { optionValue: 'Oui, en partie', nextId: 'ilots-rafraichissement.q1' },
    { optionValue: 'Oui, de manière régulière', nextId: 'ilots-rafraichissement.q1' },
  ],
  'ilots-rafraichissement.q1': [
    { optionValue: "Il n'y a pas d'espaces verts", nextId: 'ilots-rafraichissement.q2' },
    { optionValue: "Il y a des espaces verts, mais ils sont surtout composés d'herbe", nextId: 'ilots-rafraichissement.q2' },
    { optionValue: 'Il y a des arbres ou arbustes', nextId: 'ilots-rafraichissement.q2' },
  ],
  'ilots-rafraichissement.q2': [
    { optionValue: "Aucune zone de travail n'est ombragée", nextId: 'batiments.q1' },
    { optionValue: 'Quelques zones de travail sont ombragées', nextId: 'batiments.q1' },
    { optionValue: 'Plusieurs zones de travail sont ombragées', nextId: 'batiments.q1' },
    { optionValue: 'La majorité des zones de travail sont ombragées', nextId: 'batiments.q1' },
  ],
  'batiments.q1': [
    { optionValue: "Rien n'a été engagé pour le moment", nextId: 'batiments.q2' },
    { optionValue: "Des premières réflexions sont en cours (recherche d'infos, échanges avec des acteurs publics ou privés)", nextId: 'batiments.q2' },
    { optionValue: 'Un audit thermique a été réalisé (ou est en cours)', nextId: 'batiments.q2' },
    { optionValue: "Des travaux/aménagements sont programmés (ex : protections solaires, isolation...)", nextId: 'batiments.q2' },
    { optionValue: "Des travaux/aménagements sont déjà en place (ex : protections solaires, isolation...)", nextId: 'batiments.q2' },
    { optionValue: "Plusieurs types d'aménagements sont en place pour limiter la chaleur (protections solaires, isolation...), incluant des solutions fondées sur la nature (toiture et/ou murs végétalisés...)", nextId: 'batiments.q2' },
  ],
  'batiments.q2': [
    { optionValue: "Rien n'a été engagé pour le moment", nextId: 'resultats' },
    { optionValue: "Le sujet est en cours d'exploration (recherche d'informations, échanges...) auprès d'un centre de ressources public (ADEME, CSTB...) ou d'un prestataire privé (bureau d'études, entreprise...) et sensibilisation des équipes", nextId: 'resultats' },
    { optionValue: 'Des travaux pour rafraîchir mes ambiances de travail sont programmés', nextId: 'batiments.q2bis' },
    { optionValue: 'Des travaux pour rafraîchir mes ambiances de travail sont déjà en place', nextId: 'batiments.q2ter' },
  ],
  'batiments.q2bis': [
    { optionValue: 'Ventilation naturelle', nextId: 'resultats' },
    { optionValue: "Brasseurs d'air", nextId: 'resultats' },
    { optionValue: "Système de rafraîchissement actif (rafraîchissement adiabatique, réseau de froid, PAC air/eau performante, géocooling...)", nextId: 'resultats' },
    { optionValue: 'Système de climatisation conventionnelle', nextId: 'resultats' },
  ],
  'batiments.q2ter': [
    { optionValue: 'Ventilation naturelle', nextId: null },
    { optionValue: "Brasseurs d'air", nextId: null },
    { optionValue: "Système de rafraîchissement actif (rafraîchissement adiabatique, réseau de froid, PAC air/eau performante, géocooling...)", nextId: null },
    { optionValue: 'Système de climatisation conventionnelle', nextId: null },
  ],
}

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

type OptionDef = { score: number; suivant: string | null }

function extractOptionDefs(): Record<string, Record<string, OptionDef>> {
  const map: Record<string, Record<string, OptionDef>> = {}

  for (const [qId, edges] of Object.entries(QUESTION_GRAPH)) {
    const optionMap: Record<string, OptionDef> = {}
    const blocId = BLOC_FOR_QUESTION[qId]
    if (!blocId) continue

    const shortId = SHORT_ID_FOR_QUESTION[qId]
    if (!shortId) continue
    const scoreRuleName = `autodiag . ${blocId} . questions . ${shortId} . score`

    for (const edge of edges) {
      const score = getScoreForValue(scoreRuleName, edge.optionValue)
      optionMap[edge.optionValue] = { score, suivant: edge.nextId }
    }
    map[qId] = optionMap
  }

  return map
}

function getScoreForValue(scoreRuleName: string, optionValue: string): number {
  try {
    const rule = engine.getRule(scoreRuleName as never)
    const rawNode = (rule as unknown as { rawNode?: { formule?: { variations?: Array<{ si?: string; alors?: number }> } } }).rawNode
    const variations = rawNode?.formule?.variations
    if (variations) {
      for (const v of variations) {
        if (v.si) {
          const match = v.si.match(/= "?'(.+)'"/)
          if (match && match[1] === optionValue) {
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

const OPTION_DEFS = extractOptionDefs()

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
      const val = String((p as { nodeValue?: unknown }).nodeValue ?? p)
      const cleanVal = val.replace(/^'|'$/g, '')
      const def = OPTION_DEFS[qId]?.[cleanVal]
      return {
        label: cleanVal,
        score: def?.score ?? 0,
        value: val,
        suivant: def?.suivant ?? null,
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

export function getNextQuestionId(questionId: string, selectedLabel: string): string | null {
  const q = getQuestionById(questionId)
  if (!q) return null
  // Normalize double single-quotes (YAML escaping artifact) for matching
  const normalized = selectedLabel.replace(/''/g, "'")
  // Try exact match first
  let option = q.options.find((o) => o.label === selectedLabel)
  if (!option) {
    // Fallback: match after normalizing both sides
    option = q.options.find((o) => o.label === normalized)
  }
  if (!option) {
    // Ultimate fallback: normalize the option labels too
    option = q.options.find((o) => o.label.replace(/''/g, "'") === normalized)
  }
  return option?.suivant ?? null
}

// ── Scoring ────────────────────────────────────────────────

export type Answers = Record<string, number>

export function computeScores(answers: Answers): ThemeScore[] {
  const situation: Record<string, unknown> = {}
  for (const [qId, scoreValue] of Object.entries(answers)) {
    if (scoreValue < 0) continue
    const question = getQuestionById(qId)
    if (!question) continue
    const option = question.options.find((o) => o.score === scoreValue)
    if (!option) continue
    const shortId = SHORT_ID_FOR_QUESTION[qId]
    if (!shortId) continue
    const ruleName = `autodiag . ${question.blocId} . questions . ${shortId}`
    situation[ruleName] = `'${option.value}'`
  }

  const localEngine = engine.shallowCopy()
  localEngine.setSituation(situation as never)

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

    const scoreRule = `autodiag . ${bloc.id} . score`
    try {
      const result = localEngine.evaluate(scoreRule)
      const rawScore = (result as unknown as { nodeValue?: number }).nodeValue ?? 0
      const score = typeof rawScore === 'number' && !Number.isNaN(rawScore) ? rawScore : 0
      return {
        blocId: bloc.id,
        blocLabel: bloc.label,
        blocIcon: bloc.icon,
        score,
        maxScore: bloc.maxScore,
        description: bloc.description,
      }
    } catch {
      return {
        blocId: bloc.id,
        blocLabel: bloc.label,
        blocIcon: bloc.icon,
        score: 0,
        maxScore: bloc.maxScore,
        description: bloc.description,
      }
    }
  })
}
