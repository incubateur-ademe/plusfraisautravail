import { fr } from '@codegouvfr/react-dsfr';
import { Stepper } from '@codegouvfr/react-dsfr/Stepper';
import { useNavigate } from 'react-router-dom';
import type { Question } from '../data/questions';
import { QUESTIONS } from '../data/questions';
import { CONTENU } from '../data/contenu';

interface ProgressHeaderProps {
  question: Question;
}

export function ProgressHeader({ question }: ProgressHeaderProps) {
  const navigate = useNavigate();
  const currentIndex = QUESTIONS.findIndex((q) => q.id === question.id);
  const nextQuestion = QUESTIONS[currentIndex + 1];

  return (
    <div className="autodiag-progress-header">
      {question.prevRoute && (
        <button
          className={fr.cx('fr-btn', 'fr-btn--tertiary-no-outline', 'fr-icon-arrow-left-line', 'fr-btn--icon-left')}
          onClick={() => navigate(question.prevRoute!)}
          style={{ marginBottom: '1rem' }}
        >
          {CONTENU.navigation.button_back}
        </button>
      )}
      <Stepper
        currentStep={currentIndex + 1}
        stepCount={QUESTIONS.length}
        title={question.question}
        nextTitle={nextQuestion?.question}
      />
    </div>
  );
}
