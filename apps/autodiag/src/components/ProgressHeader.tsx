import { fr } from '@codegouvfr/react-dsfr';
import { Stepper } from '@codegouvfr/react-dsfr/Stepper';
import { Button } from '@codegouvfr/react-dsfr/Button';
import { useNavigate } from 'react-router-dom';
import type { Question, Theme } from '../data/questions';
import { QUESTIONS } from '../data/questions';
import { CONTENU } from '../data/contenu';

interface ProgressHeaderProps {
  question: Question;
  theme: Theme | undefined;
}

export function ProgressHeader({ question, theme }: ProgressHeaderProps) {
  const navigate = useNavigate();
  const currentIndex = QUESTIONS.findIndex((q) => q.id === question.id);
  const nextQuestion = QUESTIONS[currentIndex + 1];

  return (
    <>
      <div className="autodiag-question-header">
        <div className={fr.cx('fr-container')}>
          <div className="autodiag-question-header__inner">
            <Button
              priority="tertiary no outline"
              iconId="fr-icon-arrow-left-line"
              iconPosition="left"
              onClick={() => navigate('/')}
              size="small"
            >
              {CONTENU.navigation.button_back_home}
            </Button>
            {theme && (
              <span className={fr.cx('fr-badge', 'fr-badge--blue-cumulus', 'fr-badge--sm')}>
                <span aria-hidden="true">{theme.icon}</span>{' '}
                {theme.label}
              </span>
            )}
          </div>
        </div>
      </div>

      <div className={fr.cx('fr-container', 'fr-pt-3w')}>
        <div className={fr.cx('fr-grid-row', 'fr-grid-row--center')}>
          <div className={fr.cx('fr-col-12', 'fr-col-md-10', 'fr-col-lg-8')}>
            <Stepper
              currentStep={currentIndex + 1}
              stepCount={QUESTIONS.length}
              title={question.question}
              nextTitle={nextQuestion?.question}
            />
          </div>
        </div>
      </div>
    </>
  );
}
