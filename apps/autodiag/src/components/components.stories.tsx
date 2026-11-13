import type { Meta, StoryObj } from '@storybook/react-vite'
import { BLOC_BY_ID, QUESTIONS, computeScores, type Option } from '../data/questions'
import { ProgressHeader } from './ProgressHeader'
import { QuestionCard } from './QuestionCard'
import { RadarChartComponent } from './RadarChartComponent'
import { RecommendationCard } from './RecommendationCard'

// Real questionnaire data (questions.yaml): stories follow content changes.
const question = QUESTIONS[0]
const answerEach = (pick: (options: Option[]) => Option) =>
  Object.fromEntries(QUESTIONS.map((q) => [q.id, pick(q.options).label]))
const middle = answerEach((options) => options[Math.floor(options.length / 2)])
const best = answerEach((options) =>
  options.reduce((top, option) => (option.score > top.score ? option : top)),
)
const themeScores = (answers: Record<string, string>) =>
  computeScores(answers).filter((s) => s.maxScore > 0)
const scores = themeScores(middle)

const meta = { title: 'Autodiag/Composants' } satisfies Meta
export default meta

export const Question: StoryObj<typeof QuestionCard> = {
  name: 'Question',
  render: () => (
    <QuestionCard
      questionId={question.id}
      options={question.options}
      selectedLabel={undefined}
      onSelect={() => {}}
    />
  ),
}

export const QuestionAnswered: StoryObj<typeof QuestionCard> = {
  name: 'Question répondue',
  render: () => (
    <QuestionCard
      questionId={question.id}
      options={question.options}
      selectedLabel={question.options[0].label}
      onSelect={() => {}}
    />
  ),
}

export const Progress: StoryObj<typeof ProgressHeader> = {
  name: 'En-tête de progression',
  render: () => <ProgressHeader question={question} bloc={BLOC_BY_ID[question.blocId]} />,
}

export const Radar: StoryObj<typeof RadarChartComponent> = {
  name: 'Radar, réponses intermédiaires',
  render: () => <RadarChartComponent scores={scores} />,
}

export const RadarBest: StoryObj<typeof RadarChartComponent> = {
  name: 'Radar, meilleures réponses',
  render: () => <RadarChartComponent scores={themeScores(best)} />,
}

export const Recommendation: StoryObj<typeof RecommendationCard> = {
  name: 'Carte de recommandation',
  render: () => <RecommendationCard score={scores[0]} rank={1} />,
}
