import { useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { fr } from '@codegouvfr/react-dsfr';
import { Button } from '@codegouvfr/react-dsfr/Button';
import { ProgressHeader } from '../components/ProgressHeader';
import { QuestionCard } from '../components/QuestionCard';
import { useFormContext } from '../context/FormContext';
import { useWagtail } from '../context/WagtailContext';
import { QUESTIONS, THEMES } from '../data/questions';
import { CONTENU } from '../data/contenu';

export function QuestionPage() {
  const { questionId } = useParams<{ questionId: string }>();
  const navigate = useNavigate();
  const { answers, setAnswer } = useFormContext();
  const { prefetchSolutionPages } = useWagtail();
  const containerRef = useRef<HTMLDivElement>(null);

  const question = QUESTIONS.find((q) => q.id === questionId);
  const theme = THEMES.find((t) => t.id === question?.themeId);

  useEffect(() => {
    if (!question) {
      navigate('/');
      return;
    }

    const el = containerRef.current;
    if (el) {
      el.animate(
        [
          { opacity: 0, transform: 'translateX(40px)' },
          { opacity: 1, transform: 'translateX(0)' },
        ],
        { duration: 300, easing: 'ease-out', fill: 'both' }
      );
    }
  }, [question, navigate]);

  if (!question) return null;

  const rawAnswer = answers[question.id];
  const selectedScore = rawAnswer !== undefined && rawAnswer >= 0 ? rawAnswer : undefined;
  const hasSelection = selectedScore !== undefined;
  const c = CONTENU.navigation;

  function triggerPrefetch() {
    if (question!.id === QUESTIONS[0].id) {
      prefetchSolutionPages(THEMES);
    }
  }

  function handleSelect(score: number) {
    setAnswer(question!.id, score);
    triggerPrefetch();
  }

  function handleNext() {
    triggerPrefetch();
    navigate(question!.nextRoute ?? '/resultats');
  }

  function handleDontKnow() {
    setAnswer(question!.id, -1);
    triggerPrefetch();
    navigate(question!.nextRoute ?? '/resultats');
  }

  return (
    <div ref={containerRef} className="autodiag-question-page">
      <ProgressHeader question={question} theme={theme} />

      <div className={`${fr.cx('fr-container', 'fr-py-4w')} autodiag-question-body`}>
        <div className={fr.cx('fr-grid-row', 'fr-grid-row--center')}>
          <div className={fr.cx('fr-col-12', 'fr-col-md-10', 'fr-col-lg-8')}>
            <h2 className={fr.cx('fr-h3')}>{question.question}</h2>

            <QuestionCard
              questionId={question.id}
              options={question.options}
              selectedScore={selectedScore}
              onSelect={handleSelect}
            />
          </div>
        </div>
      </div>

      <div className="autodiag-bottom-nav">
        <div className={fr.cx('fr-container')}>
          <div className="autodiag-bottom-nav__inner">
            <Button
              priority={hasSelection ? 'primary' : 'secondary'}
              iconId="fr-icon-arrow-right-line"
              iconPosition="right"
              onClick={handleNext}
              disabled={!hasSelection}
            >
              {c.button_next}
            </Button>
            <Button
              priority="tertiary no outline"
              onClick={handleDontKnow}
            >
              {c.button_dont_know}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
