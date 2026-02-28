import { useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ProgressHeader } from '../components/ProgressHeader';
import { QuestionCard } from '../components/QuestionCard';
import { useFormContext } from '../context/FormContext';
import { useWagtail } from '../context/WagtailContext';
import { QUESTIONS, THEMES } from '../data/questions';

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

    // Entry animation
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

  const selectedScore = answers[question.id];

  function handleSelect(score: number) {
    setAnswer(question!.id, score);
    if (question!.id === QUESTIONS[0].id) {
      prefetchSolutionPages(THEMES);
    }
    setTimeout(() => {
      if (question!.nextRoute) {
        navigate(question!.nextRoute);
      } else {
        navigate('/resultats');
      }
    }, 350);
  }

  return (
    <div className="fr-container" style={{ paddingTop: '2rem', paddingBottom: '3rem' }} ref={containerRef}>
      <div className="fr-grid-row fr-grid-row--center">
        <div className="fr-col-12 fr-col-md-10 fr-col-lg-8">
          <ProgressHeader question={question} />

          {theme && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <span style={{ fontSize: '1.5rem' }}>{theme.icon}</span>
              <span className="fr-badge fr-badge--blue-cumulus fr-badge--sm">
                {theme.label}
              </span>
            </div>
          )}

          <h2 className="fr-h3">{question.question}</h2>

          <QuestionCard
            questionId={question.id}
            options={question.options}
            selectedScore={selectedScore}
            onSelect={handleSelect}
          />
        </div>
      </div>
    </div>
  );
}
